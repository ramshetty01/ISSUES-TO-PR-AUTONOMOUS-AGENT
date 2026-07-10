/**
 * DynamoDB ledger backend. Runs against LocalStack in dev (same code path as
 * real DynamoDB later). A per-window aggregate item makes reservation atomic
 * via a conditional UpdateItem, so concurrent checks cannot overspend.
 */
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import {
  DynamoDBDocumentClient,
  GetCommand,
  UpdateCommand,
} from "@aws-sdk/lib-dynamodb";
import type { RepoRef, LedgerEntry } from "@itpr/shared-types";
import { BaseLedger, type Ledger, type LedgerStore } from "./ledger.js";
import type { BudgetCaps } from "./repo-budget.js";
import { LedgerUnavailable } from "./errors.js";

export interface DynamoLedgerOptions {
  table: string;
  endpoint?: string;
  region?: string;
}

const pk = (repo: RepoRef) => `${repo.owner}/${repo.name}`;
const aggKey = (start: string) => `agg#${start.slice(0, 10)}`;

class DynamoStore implements LedgerStore {
  private readonly doc: DynamoDBDocumentClient;
  constructor(
    private readonly table: string,
    private readonly client: DynamoDBClient,
  ) {
    this.doc = DynamoDBDocumentClient.from(client);
  }

  async append(entry: LedgerEntry): Promise<void> {
    await this.doc.send(
      new UpdateCommand({
        TableName: this.table,
        Key: { pk: pk(entry.repo), sk: aggKey(entry.at) },
        UpdateExpression: "ADD tokens :t, dollars :d",
        ExpressionAttributeValues: {
          ":t": entry.tokens.total,
          ":d": entry.dollars,
        },
      }),
    );
  }

  async sum(
    repo: RepoRef,
    start: string,
  ): Promise<{ tokens: number; dollars: number }> {
    const res = await this.doc.send(
      new GetCommand({
        TableName: this.table,
        Key: { pk: pk(repo), sk: aggKey(start) },
      }),
    );
    return {
      tokens: Number(res.Item?.tokens ?? 0),
      dollars: Number(res.Item?.dollars ?? 0),
    };
  }

  async reserve(
    repo: RepoRef,
    start: string,
    _end: string,
    caps: BudgetCaps,
    entry: LedgerEntry,
  ): Promise<{ ok: boolean; tokens: number; dollars: number }> {
    const conditions: string[] = [];
    const values: Record<string, number> = {
      ":t": entry.tokens.total,
      ":d": entry.dollars,
    };
    if (caps.tokenCap > 0) {
      conditions.push("(attribute_not_exists(tokens) OR tokens <= :tkBefore)");
      values[":tkBefore"] = caps.tokenCap - entry.tokens.total;
    }
    if (caps.dollarCap > 0) {
      conditions.push("(attribute_not_exists(dollars) OR dollars <= :dlBefore)");
      values[":dlBefore"] = caps.dollarCap - entry.dollars;
    }

    try {
      const res = await this.doc.send(
        new UpdateCommand({
          TableName: this.table,
          Key: { pk: pk(repo), sk: aggKey(start) },
          UpdateExpression: "ADD tokens :t, dollars :d",
          ...(conditions.length
            ? { ConditionExpression: conditions.join(" AND ") }
            : {}),
          ExpressionAttributeValues: values,
          ReturnValues: "UPDATED_OLD",
        }),
      );
      return {
        ok: true,
        tokens: Number(res.Attributes?.tokens ?? 0),
        dollars: Number(res.Attributes?.dollars ?? 0),
      };
    } catch (e) {
      if ((e as { name?: string }).name === "ConditionalCheckFailedException") {
        const spent = await this.sum(repo, start);
        return { ok: false, tokens: spent.tokens, dollars: spent.dollars };
      }
      throw new LedgerUnavailable(e);
    }
  }

  async close(): Promise<void> {
    this.client.destroy();
  }
}

/** Create a DynamoDB-backed ledger (LocalStack endpoint in dev). */
export function createDynamoLedger(opts: DynamoLedgerOptions): Ledger {
  const client = new DynamoDBClient({
    ...(opts.endpoint ? { endpoint: opts.endpoint } : {}),
    region: opts.region ?? "us-east-1",
  });
  return new BaseLedger(new DynamoStore(opts.table, client));
}
