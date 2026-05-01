/**
 * Type definitions for Hyperliquid Copy Trading Bot
 */

export type Side = 'A' | 'B'; // A = Ask (sell), B = Bid (buy)
export type OrderType = 'Limit' | 'Market';
export type TimeInForce = 'Gtc' | 'Ioc' | 'Alo';

/**
 * Position direction
 */
export type PositionSide = 'Long' | 'Short';

/**
 * Trade action type
 */
export type TradeAction = 'open' | 'reduce' | 'close';

/**
 * Hyperliquid fill event from WebSocket subscription
 */
export interface FillEvent {
  coin: string;
  px: string; // Price as string (no trailing zeros)
  sz: string; // Size as string (no trailing zeros)
  side: Side;
  time: number;
  startPosition: string;
  dir: 'Open Long' | 'Close Long' | 'Open Short' | 'Close Short';
  closedPnl: string;
  hash: string;
  oid: number;
  crossed: boolean;
  fee: string;
}

/**
 * Position information
 */
export interface Position {
  coin: string;
  szi: string; // Position size (signed integer string)
  entryPx: string;
  leverage: {
    value: string;
  };
  liquidationPx: string;
  marginUsed: string;
  returnOnEquity: string;
  unrealizedPnl: string;
}

/**
 * Account equity information
 */
export interface AccountEquity {
  accountValue: string;
  totalMarginUsed: string;
  totalNtlPos: string;
  totalRawUsd: string;
  crossMaintenanceMarginUsed: string;
  crossMarginSummary: Record<string, unknown>;
}

/**
 * Calculated trade parameters for copying
 */
export interface CopyTradeParams {
  coin: string;
  side: Side;
  size: string; // Size in base units (no trailing zeros)
  orderType: OrderType;
  reduceOnly: boolean;
  leverage: number;
}

/**
 * Trade execution result
 */
export interface TradeResult {
  success: boolean;
  orderId?: string;
  error?: string;
  params: CopyTradeParams;
}

/**
 * Health check result
 */
export interface HealthCheckResult {
  timestamp: number;
  ourPositions: Position[];
  targetPositions: Position[];
  ourEquity: string;
  targetEquity: string;
  drift: Record<string, {
    ourSize: string;
    targetSize: string;
    difference: string;
  }>;
}
