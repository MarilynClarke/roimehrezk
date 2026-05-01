import { config } from './config.js';
import { logger, loggerUtils } from './logger.js';
import { HyperliquidClientWrapper } from './hyperliquidClient.js';
import {
  calculatePositionSize,
  capLeverage,
  getTradeAction,
  removeTrailingZeros,
  validateTradeParams,
} from './utils/risk.js';
import {
  TradingError,
  ValidationError,
  ErrorHandler,
  retryWithBackoff,
} from './utils/errors.js';
import { sendErrorNotification } from './notifications/telegram.js';
import type {
  CopyTradeParams,
  FillEvent,
  Position,
  TradeResult,
} from './types.js';

/**
 * Core copy trading logic
 * Monitors target wallet and mirrors trades
 */
export class CopyTrader {
  private client: HyperliquidClientWrapper;
  private targetWallet: string;
  private ourAddress: string;
  private activeTrades: Set<string> = new Set(); // Track active trades by coin
  private unsubscribeFn?: () => void;

  constructor(client: HyperliquidClientWrapper, targetWallet: string) {
    this.client = client;
    this.targetWallet = targetWallet;
    this.ourAddress = client.getAddress();
  }

  /**
   * Start monitoring target wallet and copying trades
   */
  async start(): Promise<void> {
    logger.info('Starting copy trader', {
      ourAddress: this.ourAddress,
      targetWallet: this.targetWallet,
      dryRun: config.DRY_RUN,
    });

    // Subscribe to target wallet fills
    this.unsubscribeFn = await this.client.subscribeToUserFills(
      this.targetWallet,
      (fill: FillEvent) => this.handleFill(fill)
    );

    logger.info('Copy trader started, monitoring fills...');
  }

  /**
   * Stop monitoring
   */
  stop(): void {
    if (this.unsubscribeFn) {
      this.unsubscribeFn();
      this.unsubscribeFn = undefined;
    }
    logger.info('Copy trader stopped');
  }

  /**
   * Handle incoming fill event from target wallet
   */
  private async handleFill(fill: FillEvent): Promise<void> {
    try {
      logger.info('Received fill event', {
        coin: fill.coin,
        side: fill.side,
        size: fill.sz,
        price: fill.px,
        direction: fill.dir,
        hash: fill.hash,
      });

      // Determine trade action
      const action = getTradeAction(fill);
      logger.debug('Trade action determined', { action, fill });

      // Get account equities for position sizing with retry
      let ourEquityData, targetEquityData;
      try {
        [ourEquityData, targetEquityData] = await retryWithBackoff(
          async () => {
            return await Promise.all([
              this.client.getAccountEquity(this.ourAddress),
              this.client.getAccountEquity(this.targetWallet),
            ]);
          },
          { maxRetries: 3, initialDelay: 1000, maxDelay: 10000, backoffMultiplier: 2 },
          (error, attempt) => {
            logger.warn(`Failed to fetch account equity (attempt ${attempt}/3)`, { error });
          }
        );
      } catch (error) {
        const formattedError = ErrorHandler.formatError(error);
        logger.error('Failed to fetch account equity after retries', formattedError);
        await sendErrorNotification(
          ErrorHandler.wrapError(error, 'Failed to fetch account equity'),
          { fillHash: fill.hash, coin: fill.coin }
        );
        return;
      }

      const ourEquity = parseFloat(ourEquityData.accountValue);
      const targetEquity = parseFloat(targetEquityData.accountValue);

      if (isNaN(ourEquity) || isNaN(targetEquity)) {
        throw new ValidationError('Invalid equity values', {
          ourEquity: ourEquityData.accountValue,
          targetEquity: targetEquityData.accountValue,
        });
      }

      logger.debug('Account equities', {
        ourEquity,
        targetEquity,
      });

      // Get current positions to determine leverage and reduce-only status
      let targetPositions;
      try {
        [, targetPositions] = await retryWithBackoff(
          async () => {
            return await Promise.all([
              this.client.getPositions(this.ourAddress),
              this.client.getPositions(this.targetWallet),
            ]);
          },
          { maxRetries: 3, initialDelay: 1000, maxDelay: 10000, backoffMultiplier: 2 }
        );
      } catch (error) {
        const formattedError = ErrorHandler.formatError(error);
        logger.error('Failed to fetch positions after retries', formattedError);
        await sendErrorNotification(
          ErrorHandler.wrapError(error, 'Failed to fetch positions'),
          { fillHash: fill.hash, coin: fill.coin }
        );
        return;
      }

      const targetPosition = targetPositions.find((p) => p.coin === fill.coin);

      // Calculate trade parameters
      let tradeParams: CopyTradeParams | null;
      try {
        tradeParams = await this.calculateTradeParams(
          fill,
          action,
          ourEquity,
          targetEquity,
          targetPosition
        );
      } catch (error) {
        const formattedError = ErrorHandler.formatError(error);
        logger.error('Failed to calculate trade parameters', formattedError);
        await sendErrorNotification(
          ErrorHandler.wrapError(error, 'Failed to calculate trade parameters'),
          { fillHash: fill.hash, coin: fill.coin }
        );
        return;
      }

      if (!tradeParams) {
        logger.warn('Trade parameters calculation returned null, skipping', {
          coin: fill.coin,
          action,
        });
        return;
      }

      // Execute trade
      const result = await this.executeTrade(tradeParams, fill.px, ourEquity);

      if (result.success) {
        loggerUtils.logTrade('info', 'Trade executed successfully', {
          orderId: result.orderId,
          params: tradeParams,
          fillHash: fill.hash,
          coin: fill.coin,
          action,
        });

        // Track active trade
        if (action === 'open') {
          this.activeTrades.add(fill.coin);
        } else if (action === 'close') {
          this.activeTrades.delete(fill.coin);
        }

        // Send notification if configured
        await this.sendNotification(fill, tradeParams, result);
      } else {
        loggerUtils.logTrade('error', 'Trade execution failed', {
          error: result.error,
          params: tradeParams,
          fillHash: fill.hash,
          coin: fill.coin,
        });
        await sendErrorNotification(
          new TradingError(result.error || 'Trade execution failed', false, {
            tradeParams,
            fillHash: fill.hash,
          })
        );
      }
    } catch (error) {
      const formattedError = ErrorHandler.formatError(error);
      logger.error('Error handling fill', {
        fill,
        ...formattedError,
      });
      
      // Send error notification for critical errors
      if (error instanceof TradingError || error instanceof ValidationError) {
        await sendErrorNotification(
          ErrorHandler.wrapError(error, 'Error handling fill'),
          { fillHash: fill.hash, coin: fill.coin }
        );
      }
    }
  }

  /**
   * Calculate trade parameters for copying
   */
  private async calculateTradeParams(
    fill: FillEvent,
    action: 'open' | 'reduce' | 'close',
    ourEquity: number,
    targetEquity: number,
    targetPosition: Position | undefined
  ): Promise<CopyTradeParams | null> {
    const coin = fill.coin;
    const fillSize = parseFloat(fill.sz);

    // Determine side: B = Buy (Long), A = Sell (Short/Close)
    let side: 'A' | 'B';
    let reduceOnly = false;

    if (action === 'open') {
      // Opening: Long = Buy (B), Short = Sell (A)
      side = fill.dir === 'Open Long' ? 'B' : 'A';
    } else {
      // Reducing/Closing: opposite of position direction
      if (targetPosition) {
        const isLong = parseFloat(targetPosition.szi) > 0;
        side = isLong ? 'A' : 'B'; // Close long = sell, close short = buy
      } else {
        // Fallback: use fill side
        side = fill.side;
      }
      reduceOnly = true;
    }

    // Calculate position size
    const targetSize = fillSize;
    const calculatedSize = calculatePositionSize(
      targetSize,
      ourEquity,
      targetEquity
    );

    // Get leverage from target position or use default
    let leverage = 1;
    if (targetPosition?.leverage) {
      leverage = parseInt(targetPosition.leverage.value);
      leverage = capLeverage(leverage);
    }

      // Check max concurrent trades
    if (action === 'open' && this.activeTrades.size >= config.MAX_CONCURRENT_TRADES) {
      logger.warn('Max concurrent trades reached, skipping', {
        activeTrades: this.activeTrades.size,
        max: config.MAX_CONCURRENT_TRADES,
        coin: fill.coin,
      });
      return null;
    }

    // Validate calculated size
    if (calculatedSize <= 0 || isNaN(calculatedSize) || !isFinite(calculatedSize)) {
      logger.error('Invalid calculated position size', {
        calculatedSize,
        targetSize,
        ourEquity,
        targetEquity,
        coin: fill.coin,
      });
      return null;
    }

    const sizeStr = removeTrailingZeros(calculatedSize.toFixed(8));

    return {
      coin,
      side,
      size: sizeStr,
      orderType: 'Market', // Use market orders for immediate execution
      reduceOnly,
      leverage,
    };
  }

  /**
   * Execute trade with retry logic
   */
  private async executeTrade(
    params: CopyTradeParams,
    price: string,
    ourEquity: number
  ): Promise<TradeResult> {
    // Validate trade parameters
    const validation = validateTradeParams(params, price, ourEquity);
    if (!validation.valid) {
      const error = new ValidationError(validation.reason || 'Invalid trade parameters', {
        params,
        price,
        ourEquity,
      });
      logger.warn('Trade validation failed', ErrorHandler.formatError(error));
      return {
        success: false,
        error: error.message,
        params,
      };
    }

    // Execute with retry logic
    try {
      const orderId = await retryWithBackoff(
        async () => {
          return await this.client.placeOrder({
            coin: params.coin,
            side: params.side,
            sz: params.size,
            orderType: params.orderType,
            reduceOnly: params.reduceOnly,
            leverage: params.leverage,
          });
        },
        {
          maxRetries: 3,
          initialDelay: 1000,
          maxDelay: 10000,
          backoffMultiplier: 2,
        },
        (error, attempt) => {
          logger.warn(`Trade execution attempt ${attempt}/3 failed`, {
            error: ErrorHandler.formatError(error),
            params,
          });
        }
      );

      return {
        success: true,
        orderId,
        params,
      };
    } catch (error) {
      const formattedError = ErrorHandler.formatError(error);
      logger.error('Trade execution failed after retries', {
        ...formattedError,
        params,
      });

      return {
        success: false,
        error: formattedError.message,
        params,
      };
    }
  }

  /**
   * Send notification (Telegram, etc.)
   */
  private async sendNotification(
    fill: FillEvent,
    params: CopyTradeParams,
    result: TradeResult
  ): Promise<void> {
    // Send Telegram notification if configured
    if (config.TELEGRAM_BOT_TOKEN && config.TELEGRAM_CHAT_ID) {
      const { sendTradeNotification } = await import('./notifications/telegram.js');
      await sendTradeNotification(fill, params, result);
    }
  }

  /**
   * Get active trades count
   */
  getActiveTradesCount(): number {
    return this.activeTrades.size;
  }
}
