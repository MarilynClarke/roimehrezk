import { z } from 'zod';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

/**
 * Configuration schema with zod validation
 * Ensures all required env vars are present and properly typed
 */
const configSchema = z.object({
  // Required
  PRIVATE_KEY: z.string().min(1, 'PRIVATE_KEY is required'),
  TARGET_WALLET: z.string().min(1, 'TARGET_WALLET is required'),
  TESTNET: z
    .string()
    .transform((val) => val.toLowerCase() === 'true')
    .pipe(z.boolean()),

  // Position sizing & risk management
  SIZE_MULTIPLIER: z
    .string()
    .default('1.0')
    .transform(Number)
    .pipe(z.number().positive()),
  MAX_LEVERAGE: z
    .string()
    .default('20')
    .transform(Number)
    .pipe(z.number().min(1).max(100)),
  MAX_POSITION_SIZE_PERCENT: z
    .string()
    .default('50')
    .transform(Number)
    .pipe(z.number().min(1).max(100)),
  MIN_NOTIONAL: z
    .string()
    .default('10')
    .transform(Number)
    .pipe(z.number().min(0)),
  MAX_CONCURRENT_TRADES: z
    .string()
    .default('10')
    .transform(Number)
    .pipe(z.number().int().positive()),

  // Asset filtering
  BLOCKED_ASSETS: z
    .string()
    .default('')
    .transform((val) =>
      val.split(',').map((s) => s.trim().toUpperCase()).filter(Boolean)
    ),

  // Safety features
  DRY_RUN: z
    .string()
    .default('false')
    .transform((val) => val.toLowerCase() === 'true')
    .pipe(z.boolean()),
  LOG_LEVEL: z
    .enum(['error', 'warn', 'info', 'debug'])
    .default('info'),

  // Optional: Telegram notifications
  TELEGRAM_BOT_TOKEN: z.string().optional(),
  TELEGRAM_CHAT_ID: z.string().optional(),

  // Optional: Health check
  HEALTH_CHECK_INTERVAL: z
    .string()
    .default('5')
    .transform(Number)
    .pipe(z.number().int().positive()),
});

export type Config = z.infer<typeof configSchema>;

/**
 * Validates and returns configuration
 * Throws error if validation fails
 */
export function loadConfig(): Config {
  try {
    return configSchema.parse(process.env);
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errors = error.errors.map((e) => `${e.path.join('.')}: ${e.message}`);
      throw new Error(`Configuration validation failed:\n${errors.join('\n')}`);
    }
    throw error;
  }
}

// Export singleton config instance
export const config = loadConfig();
