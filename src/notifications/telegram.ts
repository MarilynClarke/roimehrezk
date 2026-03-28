import TelegramBot from 'node-telegram-bot-api';
import { config } from '../config.js';
import { logger } from '../logger.js';
import type { CopyTradeParams, FillEvent, TradeResult, HealthCheckResult } from '../types.js';

/**
 * Telegram notification service
 * Sends notifications when trades are copied, errors occur, and system events
 */

let bot: TelegramBot | null = null;
let chatId: string | null = null;

/**
 * Initialize Telegram bot
 */
export async function initTelegramBot(): Promise<void> {
  if (!config.TELEGRAM_BOT_TOKEN || !config.TELEGRAM_CHAT_ID) {
    logger.debug('Telegram notifications disabled (missing token or chat ID)');
    return;
  }

  try {
    bot = new TelegramBot(config.TELEGRAM_BOT_TOKEN, { polling: false });
    chatId = config.TELEGRAM_CHAT_ID;
    
    // Test connection
    await bot.getMe();
    logger.info('Telegram bot initialized successfully');
    
    // Send startup notification
    await sendStartupNotification();
  } catch (error) {
    logger.error('Failed to initialize Telegram bot', { error });
    bot = null;
    chatId = null;
  }
}

/**
 * Check if Telegram is enabled and bot is ready
 */
function isTelegramEnabled(): boolean {
  return bot !== null && chatId !== null;
}

/**
 * Send startup notification
 */
export async function sendStartupNotification(): Promise<void> {
  if (!isTelegramEnabled()) return;

  try {
    const message = `🚀 *Hyperliquid Copy Trading Bot Started*

*Configuration:*
• Testnet: ${config.TESTNET ? 'Yes' : 'No'}
• Dry Run: ${config.DRY_RUN ? 'Yes' : 'No'}
• Target Wallet: \`${config.TARGET_WALLET.substring(0, 10)}...\`
• Size Multiplier: ${config.SIZE_MULTIPLIER}x
• Max Leverage: ${config.MAX_LEVERAGE}x
• Blocked Assets: ${config.BLOCKED_ASSETS.length > 0 ? config.BLOCKED_ASSETS.join(', ') : 'None'}

Bot is now monitoring and ready to copy trades.`;

    await bot!.sendMessage(chatId!, message, { parse_mode: 'Markdown' });
  } catch (error) {
    logger.error('Failed to send startup notification', { error });
  }
}

/**
 * Send shutdown notification
 */
export async function sendShutdownNotification(): Promise<void> {
  if (!isTelegramEnabled()) return;

  try {
    const message = `🛑 *Bot Shutting Down*

Copy trading bot has been stopped.
All positions remain open.`;

    await bot!.sendMessage(chatId!, message, { parse_mode: 'Markdown' });
  } catch (error) {
    logger.error('Failed to send shutdown notification', { error });
  }
}

/**
 * Send trade notification with enhanced formatting
 */
export async function sendTradeNotification(
  fill: FillEvent,
  params: CopyTradeParams,
  result: TradeResult
): Promise<void> {
  if (!isTelegramEnabled()) return;

  try {
    const action = result.success ? '✅' : '❌';
    const status = result.success ? '*Success*' : '*Failed*';
    const sideEmoji = params.side === 'B' ? '📈' : '📉';
    const sideText = params.side === 'B' ? 'Long' : 'Short';
    
    const message = `${action} *Trade Copied*

*Target Trade:*
• Coin: \`${fill.coin}\`
• Direction: ${fill.dir}
• Size: \`${fill.sz}\`
• Price: \`${fill.px}\`

*Our Trade:*
${sideEmoji} Side: *${sideText}*
• Size: \`${params.size}\`
• Leverage: \`${params.leverage}x\`
• Reduce Only: ${params.reduceOnly ? 'Yes' : 'No'}
• Order Type: ${params.orderType}

*Status:* ${status}
${result.orderId ? `• Order ID: \`${result.orderId}\`` : ''}
${result.error ? `• Error: \`${result.error}\`` : ''}

_Time: ${new Date().toLocaleString()}_`;

    await bot!.sendMessage(chatId!, message, { parse_mode: 'Markdown' });
    logger.debug('Telegram trade notification sent');
  } catch (error) {
    logger.error('Failed to send Telegram notification', { error });
  }
}

/**
 * Send error notification
 */
export async function sendErrorNotification(
  error: string | Error,
  context?: Record<string, unknown>
): Promise<void> {
  if (!isTelegramEnabled()) return;

  try {
    const errorMessage = error instanceof Error ? error.message : error;
    const errorStack = error instanceof Error ? error.stack : undefined;
    
    let message = `❌ *Error Occurred*

\`\`\`
${errorMessage}
\`\`\``;

    if (context && Object.keys(context).length > 0) {
      message += `\n\n*Context:*\n`;
      for (const [key, value] of Object.entries(context)) {
        message += `• ${key}: \`${String(value)}\`\n`;
      }
    }

    if (errorStack && config.LOG_LEVEL === 'debug') {
      message += `\n\`\`\`\n${errorStack.substring(0, 500)}\n\`\`\``;
    }

    await bot!.sendMessage(chatId!, message, { parse_mode: 'Markdown' });
  } catch (err) {
    logger.error('Failed to send error notification', { err });
  }
}

/**
 * Send health check notification
 */
export async function sendHealthCheckNotification(
  healthCheck: HealthCheckResult
): Promise<void> {
  if (!isTelegramEnabled()) return;

  try {
    const driftCount = Object.keys(healthCheck.drift).length;
    const statusEmoji = driftCount > 0 ? '⚠️' : '✅';
    
    let message = `${statusEmoji} *Health Check*

*Account Status:*
• Our Equity: \`$${parseFloat(healthCheck.ourEquity).toFixed(2)}\`
• Target Equity: \`$${parseFloat(healthCheck.targetEquity).toFixed(2)}\`
• Our Positions: ${healthCheck.ourPositions.length}
• Target Positions: ${healthCheck.targetPositions.length}

`;

    if (driftCount > 0) {
      message += `*⚠️ Position Drift Detected:*\n`;
      for (const [coin, drift] of Object.entries(healthCheck.drift)) {
        message += `• ${coin}: Our \`${drift.ourSize}\` vs Target \`${drift.targetSize}\` (Diff: \`${drift.difference}\`)\n`;
      }
    } else {
      message += `✅ *No drift detected - positions aligned*`;
    }

    message += `\n_Checked: ${new Date(healthCheck.timestamp).toLocaleString()}_`;

    await bot!.sendMessage(chatId!, message, { parse_mode: 'Markdown' });
  } catch (error) {
    logger.error('Failed to send health check notification', { error });
  }
}

/**
 * Send summary notification (daily/weekly stats)
 */
export async function sendSummaryNotification(stats: {
  tradesCopied: number;
  successfulTrades: number;
  failedTrades: number;
  activePositions: number;
  totalPnL?: string;
}): Promise<void> {
  if (!isTelegramEnabled()) return;

  try {
    const successRate = stats.tradesCopied > 0 
      ? ((stats.successfulTrades / stats.tradesCopied) * 100).toFixed(1)
      : '0';
    
    let message = `📊 *Trading Summary*

*Statistics:*
• Total Trades Copied: ${stats.tradesCopied}
• Successful: ${stats.successfulTrades} (${successRate}%)
• Failed: ${stats.failedTrades}
• Active Positions: ${stats.activePositions}
`;

    if (stats.totalPnL) {
      const pnl = parseFloat(stats.totalPnL);
      const pnlEmoji = pnl >= 0 ? '📈' : '📉';
      message += `\n${pnlEmoji} Total PnL: \`$${pnl.toFixed(2)}\``;
    }

    message += `\n_Generated: ${new Date().toLocaleString()}_`;

    await bot!.sendMessage(chatId!, message, { parse_mode: 'Markdown' });
  } catch (error) {
    logger.error('Failed to send summary notification', { error });
  }
}

/**
 * Send warning notification
 */
export async function sendWarningNotification(
  warning: string,
  context?: Record<string, unknown>
): Promise<void> {
  if (!isTelegramEnabled()) return;

  try {
    let message = `⚠️ *Warning*

${warning}`;

    if (context && Object.keys(context).length > 0) {
      message += `\n\n*Details:*\n`;
      for (const [key, value] of Object.entries(context)) {
        message += `• ${key}: \`${String(value)}\`\n`;
      }
    }

    await bot!.sendMessage(chatId!, message, { parse_mode: 'Markdown' });
  } catch (error) {
    logger.error('Failed to send warning notification', { error });
  }
}

/**
 * Send info notification
 */
export async function sendInfoNotification(
  info: string,
  context?: Record<string, unknown>
): Promise<void> {
  if (!isTelegramEnabled()) return;

  try {
    let message = `ℹ️ *Info*

${info}`;

    if (context && Object.keys(context).length > 0) {
      message += `\n\n*Details:*\n`;
      for (const [key, value] of Object.entries(context)) {
        message += `• ${key}: \`${String(value)}\`\n`;
      }
    }

    await bot!.sendMessage(chatId!, message, { parse_mode: 'Markdown' });
  } catch (error) {
    logger.error('Failed to send info notification', { error });
  }
}

/**
 * Cleanup Telegram bot
 */
export async function cleanupTelegramBot(): Promise<void> {
  if (bot) {
    try {
      await sendShutdownNotification();
      bot.stopPolling();
      bot = null;
      chatId = null;
      logger.info('Telegram bot cleaned up');
    } catch (error) {
      logger.error('Error cleaning up Telegram bot', { error });
    }
  }
}
