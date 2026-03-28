#!/usr/bin/env tsx

/**
 * Setup validation script
 * Checks if all required dependencies and configuration are in place
 */

import { existsSync } from 'fs';
import { readFile } from 'fs/promises';
import { config } from '../src/config.js';

async function validateSetup() {
  console.log('🔍 Validating setup...\n');

  const errors: string[] = [];
  const warnings: string[] = [];

  // Check .env file exists
  if (!existsSync('.env')) {
    errors.push('❌ .env file not found. Copy .env.example to .env and fill in your values.');
  }

  // Check node_modules
  if (!existsSync('node_modules')) {
    errors.push('❌ node_modules not found. Run: npm install');
  }

  // Check required config
  try {
    console.log('✅ Configuration loaded successfully');
    console.log(`   Testnet: ${config.TESTNET}`);
    console.log(`   Dry Run: ${config.DRY_RUN}`);
    console.log(`   Target Wallet: ${config.TARGET_WALLET.substring(0, 10)}...`);
    console.log(`   Our Address: ${config.PRIVATE_KEY ? 'Set' : 'Missing'}`);
  } catch (error) {
    errors.push(`❌ Configuration validation failed: ${error}`);
  }

  // Check SDK availability
  try {
    await import('@nktkas/hyperliquid');
    console.log('✅ Hyperliquid SDK found');
  } catch (error) {
    warnings.push('⚠️  Hyperliquid SDK not found. You may need to install it or adjust imports.');
  }

  // Check logs directory
  if (!existsSync('logs')) {
    warnings.push('⚠️  logs/ directory will be created automatically');
  }

  // Summary
  console.log('\n📋 Validation Summary:');
  
  if (errors.length > 0) {
    console.log('\n❌ Errors:');
    errors.forEach((err) => console.log(`   ${err}`));
  }

  if (warnings.length > 0) {
    console.log('\n⚠️  Warnings:');
    warnings.forEach((warn) => console.log(`   ${warn}`));
  }

  if (errors.length === 0 && warnings.length === 0) {
    console.log('\n✅ All checks passed! You\'re ready to start the bot.');
    console.log('   Run: npm start');
  } else if (errors.length === 0) {
    console.log('\n✅ Setup looks good (with some warnings).');
  } else {
    console.log('\n❌ Please fix the errors above before starting the bot.');
    process.exit(1);
  }
}

validateSetup().catch((error) => {
  console.error('Validation failed:', error);
  process.exit(1);
});
