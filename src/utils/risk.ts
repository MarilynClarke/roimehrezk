import { config } from '../config.js';
import { logger } from '../logger.js';
import type { CopyTradeParams, FillEvent } from '../types.js';

/**
 * Risk management utilities
 * Handles position sizing, leverage capping, and safety checks
 */

/**
 * Removes trailing zeros from a number string (Hyperliquid requirement)
 */
export function removeTrailingZeros(value: string): string {
  return value.replace(/\.?0+$/, '');
}

/**
 * Check if asset is blocked
 */
export function isAssetBlocked(coin: string): boolean {
  return config.BLOCKED_ASSETS.includes(coin.toUpperCase());
}

/**
 * Check if position size meets minimum notional requirement
 * Hyperliquid requires ~$10 minimum per order
 */
export function meetsMinimumNotional(size: string, price: string): boolean {
  const notional = parseFloat(size) * parseFloat(price);
  return notional >= config.MIN_NOTIONAL;
}

/**
 * Cap leverage to configured maximum
 */
export function capLeverage(leverage: number): number {
  return Math.min(leverage, config.MAX_LEVERAGE);
}

/**
 * Cap position size to maximum percentage of equity
 */
export function capPositionSize(
  calculatedSize: number,
  ourEquity: number
): number {
  const maxSize = (ourEquity * config.MAX_POSITION_SIZE_PERCENT) / 100;
  return Math.min(calculatedSize, maxSize);
}

/**
 * Calculate position size based on equity ratio and multiplier
 * Formula: (ourEquity / targetEquity) * targetSize * multiplier
 */
export function calculatePositionSize(
  targetSize: number,
  ourEquity: number,
  targetEquity: number
): number {
  if (targetEquity === 0) {
    logger.warn('Target equity is zero, using target size directly');
    return targetSize * config.SIZE_MULTIPLIER;
  }

  const ratio = ourEquity / targetEquity;
  const calculatedSize = ratio * targetSize * config.SIZE_MULTIPLIER;
  const cappedSize = capPositionSize(calculatedSize, ourEquity);

  logger.debug('Position size calculation', {
    targetSize,
    ourEquity,
    targetEquity,
    ratio,
    multiplier: config.SIZE_MULTIPLIER,
    calculatedSize,
    cappedSize,
  });

  return cappedSize;
}

/**
 * Determine trade action from fill event
 */
export function getTradeAction(fill: FillEvent): 'open' | 'reduce' | 'close' {
  if (fill.dir === 'Open Long' || fill.dir === 'Open Short') {
    return 'open';
  }
  if (fill.dir === 'Close Long' || fill.dir === 'Close Short') {
    // Check if position is fully closed by comparing startPosition
    const startPos = parseFloat(fill.startPosition);
    const fillSize = parseFloat(fill.sz);
    if (Math.abs(startPos) <= fillSize) {
      return 'close';
    }
    return 'reduce';
  }
  return 'reduce'; // Default fallback
}

/**
 * Validate trade parameters before execution
 */
export function validateTradeParams(
  params: CopyTradeParams,
  price: string,
  ourEquity: number
): { valid: boolean; reason?: string } {
  // Check blocked assets
  if (isAssetBlocked(params.coin)) {
    return { valid: false, reason: `Asset ${params.coin} is blocked` };
  }

  // Check minimum notional
  if (!meetsMinimumNotional(params.size, price)) {
    return {
      valid: false,
      reason: `Position size ${params.size} * ${price} < ${config.MIN_NOTIONAL} minimum`,
    };
  }

  // Check leverage
  if (params.leverage > config.MAX_LEVERAGE) {
    return {
      valid: false,
      reason: `Leverage ${params.leverage} exceeds max ${config.MAX_LEVERAGE}`,
    };
  }

  // Check position size cap
  const positionValue = parseFloat(params.size) * parseFloat(price);
  const maxAllowed = (ourEquity * config.MAX_POSITION_SIZE_PERCENT) / 100;
  if (positionValue > maxAllowed) {
    return {
      valid: false,
      reason: `Position value ${positionValue} exceeds ${maxAllowed} max`,
    };
  }

  return { valid: true };
}
