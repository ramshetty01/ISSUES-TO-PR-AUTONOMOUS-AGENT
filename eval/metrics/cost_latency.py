"""Cost + latency metric. Free/mock providers report zero dollars."""

from __future__ import annotations


def cost_latency(input_tokens: int, output_tokens: int, wall_ms: int, dollars: float = 0.0) -> dict:
    total = input_tokens + output_tokens
    tps = round(total / (wall_ms / 1000), 2) if wall_ms else 0.0
    return {
        "tokens": total,
        "inputTokens": input_tokens,
        "outputTokens": output_tokens,
        "dollars": round(dollars, 6),
        "wallMs": wall_ms,
        "tokensPerSec": tps,
    }
