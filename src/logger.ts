import winston from 'winston';
import DailyRotateFile from 'winston-daily-rotate-file';
import { config } from './config.js';
import { existsSync } from 'fs';
import { mkdir } from 'fs/promises';

/**
 * Enhanced Winston logger instance
 * Provides structured logging with timestamps, log levels, and file rotation
 */

// Ensure logs directory exists
const logsDir = 'logs';
if (!existsSync(logsDir)) {
  mkdir(logsDir, { recursive: true }).catch((err: unknown) => {
    console.error('Failed to create logs directory:', err);
  });
}

/**
 * Custom format for console output with better readability
 */
const consoleFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss.SSS' }),
  winston.format.errors({ stack: true }),
  winston.format.colorize({ all: true }),
  winston.format.printf((info: winston.Logform.TransformableInfo) => {
    const { timestamp, level, message, service, ...meta } = info;
    // Build the log message
    let logMessage = `${timestamp} [${level}]`;
    
    if (service) {
      logMessage += ` [${service}]`;
    }
    
    logMessage += `: ${message}`;
    
    // Add metadata if present
    const metaKeys = Object.keys(meta);
    if (metaKeys.length > 0) {
      // Filter out internal winston properties
      const filteredMeta: Record<string, unknown> = {};
      for (const key of metaKeys) {
        if (!key.startsWith('Symbol(') && key !== 'splat' && key !== 'level') {
          filteredMeta[key] = meta[key];
        }
      }
      
      if (Object.keys(filteredMeta).length > 0) {
        // Pretty print metadata
        const metaStr = JSON.stringify(filteredMeta, null, 2);
        // Only show first 500 chars of metadata to avoid cluttering console
        if (metaStr.length > 500) {
          logMessage += `\n${metaStr.substring(0, 500)}...`;
        } else {
          logMessage += `\n${metaStr}`;
        }
      }
    }
    
    return logMessage;
  })
);

/**
 * JSON format for file output (structured logging)
 */
const fileFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss.SSS' }),
  winston.format.errors({ stack: true }),
  winston.format.splat(),
  winston.format.json()
);

/**
 * Create logger instance
 */
export const logger = winston.createLogger({
  level: config.LOG_LEVEL,
  format: fileFormat,
  defaultMeta: {
    service: 'hyperliquid-copy-bot',
    environment: config.TESTNET ? 'testnet' : 'mainnet',
    dryRun: config.DRY_RUN,
  },
  transports: [
    // Console output with colorized format
    new winston.transports.Console({
      format: consoleFormat,
      handleExceptions: true,
      handleRejections: true,
    }),
    
    // Daily rotating file for all logs
    new DailyRotateFile({
      filename: `${logsDir}/combined-%DATE%.log`,
      datePattern: 'YYYY-MM-DD',
      maxSize: '20m',
      maxFiles: '14d', // Keep logs for 14 days
      format: fileFormat,
      handleExceptions: true,
      handleRejections: true,
    }),
    
    // Daily rotating file for errors only
    new DailyRotateFile({
      filename: `${logsDir}/error-%DATE%.log`,
      datePattern: 'YYYY-MM-DD',
      level: 'error',
      maxSize: '20m',
      maxFiles: '30d', // Keep error logs for 30 days
      format: fileFormat,
      handleExceptions: true,
      handleRejections: true,
    }),
    
    // Separate file for trading operations
    new DailyRotateFile({
      filename: `${logsDir}/trading-%DATE%.log`,
      datePattern: 'YYYY-MM-DD',
      maxSize: '20m',
      maxFiles: '30d',
      format: fileFormat,
      // Custom filter for trading-related logs
    }),
  ],
  // Handle exceptions and rejections
  exceptionHandlers: [
    new DailyRotateFile({
      filename: `${logsDir}/exceptions-%DATE%.log`,
      datePattern: 'YYYY-MM-DD',
      maxSize: '20m',
      maxFiles: '30d',
    }),
  ],
  rejectionHandlers: [
    new DailyRotateFile({
      filename: `${logsDir}/rejections-%DATE%.log`,
      datePattern: 'YYYY-MM-DD',
      maxSize: '20m',
      maxFiles: '30d',
    }),
  ],
  exitOnError: false, // Don't exit on handled errors
});

/**
 * Logger utility functions for common use cases
 */
export const loggerUtils = {
  /**
   * Log a trade operation
   */
  logTrade(
    level: 'info' | 'warn' | 'error',
    message: string,
    meta?: Record<string, unknown>
  ): void {
    logger[level](message, {
      ...meta,
      context: 'trading',
      type: 'trade',
    });
  },

  /**
   * Log an API call
   */
  logApiCall(
    method: string,
    endpoint: string,
    duration?: number,
    success?: boolean,
    error?: unknown
  ): void {
    const meta: Record<string, unknown> = {
      context: 'api',
      method,
      endpoint,
    };

    if (duration !== undefined) {
      meta.duration = `${duration}ms`;
    }

    if (success !== undefined) {
      meta.success = success;
    }

    if (error) {
      meta.error = error instanceof Error ? error.message : String(error);
    }

    logger.info(`API Call: ${method} ${endpoint}`, meta);
  },

  /**
   * Log performance metrics
   */
  logPerformance(
    operation: string,
    duration: number,
    meta?: Record<string, unknown>
  ): void {
    logger.debug(`Performance: ${operation}`, {
      ...meta,
      context: 'performance',
      duration: `${duration}ms`,
      operation,
    });
  },

  /**
   * Log WebSocket events
   */
  logWebSocket(
    event: string,
    message: string,
    meta?: Record<string, unknown>
  ): void {
    logger.info(`WebSocket [${event}]: ${message}`, {
      ...meta,
      context: 'websocket',
      event,
    });
  },

  /**
   * Log health check results
   */
  logHealthCheck(
    status: 'healthy' | 'warning' | 'error',
    message: string,
    meta?: Record<string, unknown>
  ): void {
    const level = status === 'healthy' ? 'info' : status === 'warning' ? 'warn' : 'error';
    logger[level](`Health Check [${status}]: ${message}`, {
      ...meta,
      context: 'health',
      status,
    });
  },

  /**
   * Log configuration changes
   */
  logConfig(
    action: string,
    key: string,
    value?: unknown,
    meta?: Record<string, unknown>
  ): void {
    logger.info(`Config ${action}: ${key}`, {
      ...meta,
      context: 'config',
      key,
      value,
      action,
    });
  },

  /**
   * Create a child logger with additional context
   */
  child(meta: Record<string, unknown>): winston.Logger {
    return logger.child(meta);
  },
};

// Export logger instance and utilities
export default logger;
