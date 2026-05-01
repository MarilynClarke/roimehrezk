/**
 * Custom error classes for better error handling and categorization
 */

/**
 * Base error class for all application errors
 */
export class AppError extends Error {
  public readonly code: string;
  public readonly context?: Record<string, unknown>;
  public readonly retryable: boolean;

  constructor(
    message: string,
    code: string,
    retryable = false,
    context?: Record<string, unknown>
  ) {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    this.retryable = retryable;
    this.context = context;
    Error.captureStackTrace(this, this.constructor);
  }
}

/**
 * SDK/API related errors
 */
export class SDKError extends AppError {
  constructor(message: string, context?: Record<string, unknown>) {
    super(message, 'SDK_ERROR', true, context);
  }
}

/**
 * Network/Connection errors
 */
export class NetworkError extends AppError {
  constructor(message: string, context?: Record<string, unknown>) {
    super(message, 'NETWORK_ERROR', true, context);
  }
}

/**
 * WebSocket connection errors
 */
export class WebSocketError extends AppError {
  constructor(message: string, context?: Record<string, unknown>) {
    super(message, 'WEBSOCKET_ERROR', true, context);
  }
}


/**
 * Trading/Order execution errors
 */
export class TradingError extends AppError {
  constructor(message: string, retryable = false, context?: Record<string, unknown>) {
    super(message, 'TRADING_ERROR', retryable, context);
  }
}

/**
 * Validation errors (non-retryable)
 */
export class ValidationError extends AppError {
  constructor(message: string, context?: Record<string, unknown>) {
    super(message, 'VALIDATION_ERROR', false, context);
  }
}

/**
 * Configuration errors
 */
export class ConfigError extends AppError {
  constructor(message: string, context?: Record<string, unknown>) {
    super(message, 'CONFIG_ERROR', false, context);
  }
}

/**
 * Rate limit errors
 */
export class RateLimitError extends AppError {
  constructor(message: string, retryAfter?: number, context?: Record<string, unknown>) {
    super(
      message,
      'RATE_LIMIT_ERROR',
      true,
      { ...context, retryAfter }
    );
  }
}

/**
 * Account/Authorization errors
 */
export class AccountError extends AppError {
  constructor(message: string, context?: Record<string, unknown>) {
    super(message, 'ACCOUNT_ERROR', false, context);
  }
}

/**
 * Error helper utilities
 */
export class ErrorHandler {
  /**
   * Check if error is retryable
   */
  static isRetryable(error: unknown): boolean {
    if (error instanceof AppError) {
      return error.retryable;
    }
    // Default: network errors are retryable
    if (error instanceof Error) {
      const message = error.message.toLowerCase();
      return (
        message.includes('network') ||
        message.includes('timeout') ||
        message.includes('connection') ||
        message.includes('econnreset') ||
        message.includes('enotfound')
      );
    }
    return false;
  }

  /**
   * Extract error message safely
   */
  static getErrorMessage(error: unknown): string {
    if (error instanceof AppError) {
      return error.message;
    }
    if (error instanceof Error) {
      return error.message;
    }
    if (typeof error === 'string') {
      return error;
    }
    return 'Unknown error occurred';
  }

  /**
   * Extract error code
   */
  static getErrorCode(error: unknown): string {
    if (error instanceof AppError) {
      return error.code;
    }
    return 'UNKNOWN_ERROR';
  }

  /**
   * Extract error context
   */
  static getErrorContext(error: unknown): Record<string, unknown> {
    if (error instanceof AppError && error.context) {
      return error.context;
    }
    return {};
  }

  /**
   * Format error for logging
   */
  static formatError(error: unknown): {
    message: string;
    code: string;
    retryable: boolean;
    context: Record<string, unknown>;
    stack?: string;
  } {
    const result = {
      message: this.getErrorMessage(error),
      code: this.getErrorCode(error),
      retryable: this.isRetryable(error),
      context: this.getErrorContext(error),
    };

    if (error instanceof Error && error.stack) {
      return { ...result, stack: error.stack };
    }

    return result;
  }

  /**
   * Wrap unknown error into AppError
   */
  static wrapError(
    error: unknown,
    defaultMessage = 'An error occurred',
    defaultCode = 'UNKNOWN_ERROR'
  ): AppError {
    if (error instanceof AppError) {
      return error;
    }

    const message = this.getErrorMessage(error);
    const isRetryable = this.isRetryable(error);

    return new AppError(
      message || defaultMessage,
      defaultCode,
      isRetryable,
      error instanceof Error ? { originalError: error.name } : {}
    );
  }
}

/**
 * Retry configuration
 */
export interface RetryConfig {
  maxRetries: number;
  initialDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  retryableErrors?: string[];
}

/**
 * Default retry configuration
 */
export const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  initialDelay: 1000,
  maxDelay: 30000,
  backoffMultiplier: 2,
};

/**
 * Retry utility with exponential backoff
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  config: RetryConfig = DEFAULT_RETRY_CONFIG,
  onRetry?: (error: unknown, attempt: number) => void
): Promise<T> {
  let lastError: unknown;
  let delay = config.initialDelay;

  for (let attempt = 1; attempt <= config.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Check if error is retryable
      if (!ErrorHandler.isRetryable(error)) {
        throw error;
      }

      // Check if we've exhausted retries
      if (attempt >= config.maxRetries) {
        break;
      }

      // Call retry callback if provided
      if (onRetry) {
        onRetry(error, attempt);
      }

      // Wait before retry with exponential backoff
      await new Promise((resolve) => setTimeout(resolve, delay));
      delay = Math.min(delay * config.backoffMultiplier, config.maxDelay);
    }
  }

  throw ErrorHandler.wrapError(lastError, 'Max retries exceeded');
}
