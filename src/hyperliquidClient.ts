import { Wallet } from 'ethers';
import { config } from './config.js';
import { logger, loggerUtils } from './logger.js';
import {
  SDKError,
  NetworkError,
  WebSocketError,
  TradingError,
  AccountError,
  ErrorHandler,
} from './utils/errors.js';
import type { AccountEquity, Position } from './types.js';
/**
 * Hyperliquid SDK Client wrapper
 * Handles initialization and provides typed methods for API calls
 * 
 * NOTE: The actual SDK structure may vary. Common options:
 * - @nktkas/hyperliquid (community SDK)
 * - nomeida/hyperliquid (alternative community SDK)
 * - Official Hyperliquid API (direct HTTP/WebSocket)
 * 
 * Adjust imports below based on your chosen SDK.
 * If SDK doesn't exist, you may need to implement direct API calls.
 */

// Placeholder for SDK imports - adjust based on actual package
// Example structure (adjust as needed):
// import { ExchangeClient, InfoClient } from '@nktkas/hyperliquid';
// or
// import Hyperliquid from '@nktkas/hyperliquid';

// For now, we'll use dynamic imports with fallback
let ExchangeClient: any;
let InfoClient: any;
let WebSocketClient: any;

async function loadSDK(): Promise<void> {
  try {
    // Try @nktkas/hyperliquid first
    const hyperliquid = await import('@nktkas/hyperliquid');
    ExchangeClient = hyperliquid.ExchangeClient || hyperliquid.default?.ExchangeClient;
    InfoClient = hyperliquid.InfoClient || hyperliquid.default?.InfoClient;
    WebSocketClient = hyperliquid.SubscriptionClient || hyperliquid.default?.SubscriptionClient;
    
    if (!ExchangeClient || !InfoClient) {
      throw new SDKError('SDK structure not recognized', {
        availableExports: Object.keys(hyperliquid),
      });
    }
    
    logger.info('Hyperliquid SDK loaded successfully');
  } catch (error) {
    const formattedError = ErrorHandler.formatError(error);
    logger.error('Failed to load Hyperliquid SDK', formattedError);
    logger.warn('You may need to install: npm install @nktkas/hyperliquid');
    logger.warn('Or implement direct API calls to Hyperliquid endpoints');
    throw new SDKError(
      'Hyperliquid SDK not found. Please install @nktkas/hyperliquid or implement direct API calls.',
      formattedError.context
    );
  }
}

export class HyperliquidClientWrapper {
  private wallet: Wallet;
  private exchangeClient: any;
  private infoClient: any;
  private wsClient: any;
  private isConnected: boolean = false;
  private baseUrl: string;

  constructor() {
    // Initialize wallet from private key

    this.wallet = new Wallet(config.PRIVATE_KEY);         
    // Set base URL based on testnet/mainnet
    this.baseUrl = config.TESTNET
      ? 'https://api.hyperliquid-testnet.xyz'
      : 'https://api.hyperliquid.xyz';

    logger.info('Hyperliquid client wrapper created', {
      address: this.wallet.address,
      testnet: config.TESTNET,
      baseUrl: this.baseUrl,
    });
  }

  /**
   * Initialize SDK clients (call after SDK is loaded)
   */
  async initialize(): Promise<void> {
    await loadSDK();

    // Initialize exchange client for placing orders
    // Adjust constructor parameters based on actual SDK
    this.exchangeClient = new ExchangeClient(this.wallet, {
      baseUrl: this.baseUrl,
      testnet: config.TESTNET,
    });

    // Initialize info client for querying data
    this.infoClient = new InfoClient({ baseUrl: this.baseUrl });

    logger.info('Hyperliquid clients initialized', {
      address: this.wallet.address,
      testnet: config.TESTNET,
    });
  }

  /**
   * Get account equity information
   */
  async getAccountEquity(address: string): Promise<AccountEquity> {
    try {
      if (!this.infoClient) {
        throw new SDKError('Info client not initialized', { address });
      }

      const userState = await this.infoClient.userState(address);
      
      if (!userState || !userState.marginSummary) {
        throw new AccountError('Invalid account state response', { address });
      }

      return {
        accountValue: userState.marginSummary.accountValue || '0',
        totalMarginUsed: userState.marginSummary.totalMarginUsed || '0',
        totalNtlPos: userState.marginSummary.totalNtlPos || '0',
        totalRawUsd: userState.marginSummary.totalRawUsd || '0',
        crossMaintenanceMarginUsed:
          userState.marginSummary.crossMaintenanceMarginUsed || '0',
        crossMarginSummary: userState.marginSummary.crossMarginSummary || {},
      };
    } catch (error) {
      const formattedError = ErrorHandler.formatError(error);
      logger.error('Failed to get account equity', {
        address,
        ...formattedError,
      });
      
      if (error instanceof AccountError || error instanceof SDKError) {
        throw error;
      }
      
      throw new NetworkError('Failed to fetch account equity', {
        address,
        originalError: formattedError.message,
      });
    }
  }

  /**
   * Get open positions for an address
   */
  async getPositions(address: string): Promise<Position[]> {
    try {
      if (!this.infoClient) {
        throw new SDKError('Info client not initialized', { address });
      }

      const userState = await this.infoClient.userState(address);
      
      if (!userState) {
        throw new AccountError('Invalid user state response', { address });
      }

const assetPositions = (userState.assetPositions ?? []) as Array<{ position?: Position }>;

return assetPositions
  .map((pos): Position | null => {
    if (!pos.position) {
      logger.warn('Invalid position data', { pos });
      return null;
    }
    return {
      coin: pos.position.coin,
      szi: pos.position.szi,
      entryPx: pos.position.entryPx,
      leverage: pos.position.leverage,
      liquidationPx: pos.position.liquidationPx,
      marginUsed: pos.position.marginUsed,
      returnOnEquity: pos.position.returnOnEquity,
      unrealizedPnl: pos.position.unrealizedPnl,
    };
  })
  .filter((pos): pos is Position => pos !== null);
    } catch (error) {
      const formattedError = ErrorHandler.formatError(error);
      logger.error('Failed to get positions', {
        address,
        ...formattedError,
      });
      
      if (error instanceof AccountError || error instanceof SDKError) {
        throw error;
      }
      
      throw new NetworkError('Failed to fetch positions', {
        address,
        originalError: formattedError.message,
      });
    }
  }

  /**
   * Place an order
   * Returns order ID or throws error
   */
  async placeOrder(params: {
    coin: string;
    side: 'A' | 'B';
    sz: string; // Size (no trailing zeros)
    limitPx?: string; // Limit price (for limit orders)
    orderType: 'Limit' | 'Market';
    reduceOnly: boolean;
    leverage: number;
  }): Promise<string> {
    try {
      if (!this.exchangeClient) {
        throw new SDKError('Exchange client not initialized', { params });
      }

      // Validate parameters
      if (!params.coin || !params.sz || parseFloat(params.sz) <= 0) {
        throw new TradingError('Invalid order parameters', false, { params });
      }

      // Hyperliquid-specific: no trailing zeros in size/price
      const orderParams = {
        ...params,
        sz: params.sz.replace(/\.?0+$/, ''),
        limitPx: params.limitPx?.replace(/\.?0+$/, ''),
      };

      const startTime = Date.now();
      loggerUtils.logTrade('info', 'Placing order', orderParams);

      if (config.DRY_RUN) {
        loggerUtils.logTrade('warn', 'DRY RUN: Order not placed', orderParams);
        return 'dry-run-order-id';
      }

      // Set leverage first if needed
      if (params.leverage > 1) {
        try {
          await this.exchangeClient.updateLeverage({
            coin: params.coin,
            leverage: params.leverage,
            isCross: false, // Isolated margin
          });
        } catch (error) {
          logger.warn('Failed to update leverage, continuing with order', {
            error: ErrorHandler.formatError(error),
            params,
          });
          // Don't throw - leverage update failure shouldn't block order
        }
      }

      // Place order
      const result = await this.exchangeClient.order(orderParams, {
        type: params.orderType,
        tif: 'Gtc', // Good till cancel
        reduceOnly: params.reduceOnly,
      });

      if (!result || !result.status) {
        throw new TradingError('Invalid order response', true, { params, result });
      }

      const orderId = result.status.resting?.oid || result.status.filled?.oid;
      
      if (!orderId) {
        throw new TradingError('Order placed but no order ID returned', true, {
          params,
          result,
        });
      }

      const duration = Date.now() - startTime;
      loggerUtils.logTrade('info', 'Order placed successfully', {
        orderId,
        params: orderParams,
        duration: `${duration}ms`,
      });
      loggerUtils.logPerformance('placeOrder', duration, { coin: params.coin });

      return orderId;
    } catch (error) {
      const formattedError = ErrorHandler.formatError(error);
      logger.error('Failed to place order', {
        params,
        ...formattedError,
      });
      
      if (error instanceof TradingError || error instanceof SDKError) {
        throw error;
      }
      
      throw new TradingError('Failed to place order', true, {
        params,
        originalError: formattedError.message,
      });
    }
  }

  /**
   * Subscribe to user fills via WebSocket
   * Returns unsubscribe function
   */
  async subscribeToUserFills(
    address: string,
    onFill: (fill: any) => void
  ): Promise<() => void> {
    try {
      const wsUrl = config.TESTNET
        ? 'wss://api.hyperliquid-testnet.xyz/ws'
        : 'wss://api.hyperliquid.xyz/ws';

      // Initialize WebSocket client
      // Adjust based on actual SDK WebSocket implementation
      let WebSocket: any;
      
      try {
        const ws = await import('ws');
        WebSocket = ws.default || ws;
      } catch (error) {
        throw new WebSocketError('Failed to import WebSocket library', {
          originalError: ErrorHandler.getErrorMessage(error),
        });
      }
      
      if (WebSocketClient) {
        this.wsClient = new WebSocketClient(wsUrl);
      } else {
        // Fallback to native WebSocket or ws library
        try {
          this.wsClient = new WebSocket(wsUrl);
        } catch (error) {
          throw new WebSocketError('Failed to create WebSocket connection', {
            url: wsUrl,
            originalError: ErrorHandler.getErrorMessage(error),
          });
        }
      }

      this.wsClient.on('open', () => {
        loggerUtils.logWebSocket('open', 'WebSocket connected', { address, url: wsUrl });
        this.isConnected = true;

        try {
          // Subscribe to user fills
          this.wsClient.send(
            JSON.stringify({
              method: 'subscribe',
              subscription: {
                type: 'userFills',
                user: address,
              },
            })
          );
        } catch (error) {
          logger.error('Failed to send WebSocket subscription', {
            error: ErrorHandler.formatError(error),
            address,
          });
        }
      });

      this.wsClient.on('message', (data: string | { toString(): string }) => {
        try {
          const messageStr = typeof data === 'string' ? data : data.toString();
          const message = JSON.parse(messageStr);
          
          if (message.channel === 'userFills' && message.data) {
            if (Array.isArray(message.data)) {
              message.data.forEach((fill: any) => {
                try {
                  onFill(fill);
                } catch (error) {
                  logger.error('Error in fill callback', {
                    error: ErrorHandler.formatError(error),
                    fill,
                  });
                }
              });
            }
          }
        } catch (error) {
          logger.error('Failed to parse WebSocket message', {
            error: ErrorHandler.formatError(error),
            data: typeof data === 'string' ? data.substring(0, 200) : 'Buffer',
          });
        }
      });

      this.wsClient.on('error', (error: Error) => {
        const formattedError = ErrorHandler.formatError(error);
        logger.error('WebSocket error', {
          ...formattedError,
          address,
          url: wsUrl,
        });
        this.isConnected = false;
      });

      this.wsClient.on('close', (code: number, reason?: { toString(): string } | string) => {
        logger.warn('WebSocket closed', {
          code,
          reason: reason ? (typeof reason === 'string' ? reason : reason.toString()) : 'Unknown',
          address,
        });
        this.isConnected = false;
        this.reconnect(address, onFill);
      });

      // Return unsubscribe function
      return () => {
        try {
          if (this.wsClient) {
            this.wsClient.close();
            this.isConnected = false;
            loggerUtils.logWebSocket('close', 'WebSocket unsubscribed', { address });
          }
        } catch (error) {
          logger.error('Error unsubscribing WebSocket', {
            error: ErrorHandler.formatError(error),
            address,
          });
        }
      };
    } catch (error) {
      const formattedError = ErrorHandler.formatError(error);
      logger.error('Failed to subscribe to user fills', {
        address,
        ...formattedError,
      });
      
      if (error instanceof WebSocketError) {
        throw error;
      }
      
      throw new WebSocketError('Failed to subscribe to user fills', {
        address,
        originalError: formattedError.message,
      });
    }
  }

  /**
   * Reconnect WebSocket with exponential backoff
   */
  private reconnect(address: string, onFill: (fill: any) => void, attempt = 1): void {
    const maxAttempts = 10;
    const delay = Math.min(1000 * Math.pow(2, attempt - 1), 30000);

    if (attempt > maxAttempts) {
      const error = new WebSocketError('Max reconnection attempts reached', {
        address,
        attempts: maxAttempts,
      });
      logger.error('Max reconnection attempts reached', ErrorHandler.formatError(error));
      return;
    }

    setTimeout(async () => {
      logger.info(`Reconnection attempt ${attempt}/${maxAttempts}`, { address });
      try {
        await this.subscribeToUserFills(address, onFill);
      } catch (error) {
        const formattedError = ErrorHandler.formatError(error);
        logger.error('Reconnection failed', {
          attempt,
          ...formattedError,
          address,
        });
        this.reconnect(address, onFill, attempt + 1);
      }
    }, delay);
  }

  /**
   * Get our wallet address
   */
  getAddress(): string {
    return this.wallet.address;
  }

  /**
   * Check if WebSocket is connected
   */
  isWsConnected(): boolean {
    return this.isConnected;
  }
}
