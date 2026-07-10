/**
 * Adapter that constructs the budget Ledger backend for the dispatcher:
 * DynamoDB (LocalStack) primary, sqlite fallback controlled by config.
 */
import {
  createDynamoLedger,
  createSqliteLedger,
  type Ledger,
} from "@itpr/budget-ledger";
import { loadConfig } from "@itpr/config";

/** Build a Ledger from config. Falls back to sqlite when configured. */
export function createLedger(source?: NodeJS.ProcessEnv): Ledger {
  const cfg = loadConfig(source);
  if (cfg.BUDGET_LEDGER_FALLBACK_SQLITE) {
    return createSqliteLedger();
  }
  return createDynamoLedger({
    table: cfg.DYNAMODB_BUDGET_TABLE,
    endpoint: cfg.AWS_ENDPOINT_URL,
    region: cfg.AWS_REGION,
  });
}
