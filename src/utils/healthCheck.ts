import { HyperliquidClientWrapper } from '../hyperliquidClient.js';
import { logger, loggerUtils } from '../logger.js';
import { config } from '../config.js';
import { NetworkError, ErrorHandler } from '../utils/errors.js';
import type { HealthCheckResult } from '../types.js';

/**
 * Health check utility
 * Periodically checks our positions vs target positions
 */

export class HealthChecker {
  private client: HyperliquidClientWrapper;
  private ourAddress: string;
  private targetAddress: string;
  private intervalId?: ReturnType<typeof setInterval>;
  private lastResult?: HealthCheckResult;

  constructor(
    client: HyperliquidClientWrapper,
    ourAddress: string,
    targetAddress: string
  ) {
    this.client = client;
    this.ourAddress = ourAddress;
    this.targetAddress = targetAddress;
  }

  /**
   * Start periodic health checks
   */
  start(intervalMinutes: number): void {
    logger.info(`Starting health checks every ${intervalMinutes} minutes`);

    // Run immediately
    this.checkHealth();

    // Then run periodically
    this.intervalId = setInterval(() => {
      this.checkHealth();
    }, intervalMinutes * 60 * 1000);
  }

  /**
   * Stop health checks
   */
  stop(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = undefined;
      logger.info('Health checks stopped');
    }
  }

  /**
   * Get last health check result
   */
  getLastResult(): HealthCheckResult | undefined {
    return this.lastResult;
  }

  /**
   * Manually trigger health check and return result
   */
  async runHealthCheck(): Promise<HealthCheckResult> {
    return await this.checkHealthPublic();
  }

  /**
   * Perform health check
   */
  private async checkHealth(): Promise<HealthCheckResult> {
    try {
      const [ourPositions, targetPositions, ourEquityData, targetEquityData] =
        await Promise.all([
          this.client.getPositions(this.ourAddress),
          this.client.getPositions(this.targetAddress),
          this.client.getAccountEquity(this.ourAddress),
          this.client.getAccountEquity(this.targetAddress),
        ]);

      const ourEquity = ourEquityData.accountValue;
      const targetEquity = targetEquityData.accountValue;

      // Calculate drift between positions
      const drift: Record<string, { ourSize: string; targetSize: string; difference: string }> = {};

      // Check all target positions
      for (const targetPos of targetPositions) {
        const ourPos = ourPositions.find((p) => p.coin === targetPos.coin);
        const targetSize = parseFloat(targetPos.szi);
        const ourSize = ourPos ? parseFloat(ourPos.szi) : 0;
        const difference = Math.abs(targetSize - ourSize);

        if (difference > 0.01) {
          // Significant drift
          drift[targetPos.coin] = {
            ourSize: ourSize.toString(),
            targetSize: targetSize.toString(),
            difference: difference.toString(),
          };
        }
      }

      // Check for positions we have but target doesn't
      for (const ourPos of ourPositions) {
        const targetPos = targetPositions.find((p) => p.coin === ourPos.coin);
        if (!targetPos) {
          drift[ourPos.coin] = {
            ourSize: ourPos.szi,
            targetSize: '0',
            difference: ourPos.szi,
          };
        }
      }

      const result: HealthCheckResult = {
        timestamp: Date.now(),
        ourPositions,
        targetPositions,
        ourEquity,
        targetEquity,
        drift,
      };

      this.lastResult = result;

      if (Object.keys(drift).length > 0) {
        loggerUtils.logHealthCheck('warning', 'Position drift detected', {
          drift,
          ourEquity,
          targetEquity,
          ourPositions: ourPositions.length,
          targetPositions: targetPositions.length,
        });
        
        // Send Telegram notification if drift detected
        if (config.TELEGRAM_BOT_TOKEN && config.TELEGRAM_CHAT_ID) {
          try {
            const { sendHealthCheckNotification } = await import('../notifications/telegram.js');
            await sendHealthCheckNotification(result);
          } catch (error) {
            logger.error('Failed to send health check notification', { error });
          }
        }
      } else {
        loggerUtils.logHealthCheck('healthy', 'Health check passed', {
          ourEquity,
          targetEquity,
          positionCount: ourPositions.length,
        });
      }

      return result;
    } catch (error) {
      const formattedError = ErrorHandler.formatError(error);
      logger.error('Health check failed', formattedError);
      
      // Wrap and rethrow with better context
      if (error instanceof NetworkError) {
        throw error;
      }
      
      throw new NetworkError('Health check failed', {
        ourAddress: this.ourAddress,
        targetAddress: this.targetAddress,
        originalError: formattedError.message,
      });
    }
  }

  /**
   * Perform health check (public method)
   */
  async checkHealthPublic(): Promise<HealthCheckResult> {
    return await this.checkHealth();
  }
}
