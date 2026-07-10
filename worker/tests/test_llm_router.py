"""Phase 23 LLM tests — all against the mock/fakes, zero real tokens/network."""

from __future__ import annotations

from pathlib import Path

import pytest

from issue_to_pr_agent.errors import LLMError
from issue_to_pr_agent.llm import (
    LLMClient,
    Message,
    ProviderLimits,
    RateLimiter,
    Router,
    build_client,
    extract_code_blocks,
    extract_json,
    load_provider_limits,
)
from issue_to_pr_agent.llm.provider_base import ProviderError, RateLimitError
from issue_to_pr_agent.llm.providers import MockProvider, NvidiaNimProvider
from issue_to_pr_agent.config import WorkerConfig

MSGS = [Message("system", "you are a bot"), Message("user", "fix the bug")]


def test_mock_provider_deterministic() -> None:
    p = MockProvider(response="hello world")
    c1 = p.complete(MSGS)
    c2 = p.complete(MSGS)
    assert c1.text == c2.text == "hello world"
    assert c1.usage.total > 0
    assert c1.provider == "mock"


def test_router_uses_first_healthy_provider() -> None:
    good = MockProvider(response="ok")
    router = Router([good])
    res = router.complete(MSGS)
    assert res.text == "ok"
    assert router.attempts[-1].outcome == "ok"


def test_router_falls_through_on_rate_limit() -> None:
    primary = MockProvider(fail_with=RateLimitError("429"))
    backup = MockProvider(response="from backup")
    router = Router([primary, backup])
    res = router.complete(MSGS)
    assert res.text == "from backup"
    assert [a.outcome for a in router.attempts] == ["rate_limited", "ok"]


def test_router_falls_through_on_provider_error() -> None:
    primary = MockProvider(fail_with=ProviderError("500"))
    backup = MockProvider(response="ok")
    router = Router([primary, backup])
    assert router.complete(MSGS).text == "ok"


def test_router_raises_when_all_fail() -> None:
    a = MockProvider(fail_with=RateLimitError("429"))
    b = MockProvider(fail_with=ProviderError("500"))
    with pytest.raises(LLMError):
        Router([a, b]).complete(MSGS)


def test_rate_limiter_throttles_and_router_skips() -> None:
    t = [0.0]
    rl = RateLimiter({"mock": ProviderLimits(rpm=1, tpm=0)}, clock=lambda: t[0])
    primary = MockProvider(response="first")
    backup = MockProvider(response="second")
    # Give both the same name so the limiter treats them as one provider.
    backup.name = "backup"
    router = Router([primary, backup], rate_limiter=rl)

    r1 = router.complete(MSGS)  # uses mock, records 1 request
    assert r1.text == "first"
    r2 = router.complete(MSGS)  # mock now throttled (rpm=1) -> falls to backup
    assert r2.text == "second"
    assert router.attempts[0].outcome == "throttled"


def test_rate_limiter_window_resets() -> None:
    t = [0.0]
    rl = RateLimiter({"mock": ProviderLimits(rpm=1, tpm=0)}, clock=lambda: t[0])
    assert rl.allow("mock", 10) is True
    rl.record("mock", 10)
    assert rl.allow("mock", 10) is False
    t[0] = 61.0  # past the 60s window
    assert rl.allow("mock", 10) is True


def test_llm_client_meters_tokens_and_cost() -> None:
    client = LLMClient(Router([MockProvider(response="abcd")]))
    client.complete(MSGS)
    client.complete(MSGS)
    assert client.tokens.total > 0
    assert client.cost.dollars == 0.0  # mock is free


def test_build_client_defaults_to_mock() -> None:
    cfg = WorkerConfig(LLM_PROVIDER_ORDER="mock")  # type: ignore[call-arg]
    client = build_client(cfg)
    assert client.complete(MSGS).provider == "mock"


def test_load_provider_limits(tmp_path: Path) -> None:
    policy = Path(__file__).resolve().parents[2] / "policies" / "llm-provider-limits.yaml"
    limits = load_provider_limits(policy)
    assert limits["nvidia_nim"].rpm > 0


def test_openai_compat_provider_shapes_request() -> None:
    calls: list[tuple[str, str, dict, bytes | None]] = []

    def fake_transport(method, url, headers, body):
        calls.append((method, url, headers, body))
        return 200, {
            "choices": [{"message": {"content": "patched"}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 3},
        }

    p = NvidiaNimProvider("nim_key", transport=fake_transport)
    res = p.complete(MSGS)
    assert res.text == "patched"
    assert res.usage.input == 12 and res.usage.output == 3
    method, url, headers, _ = calls[0]
    assert method == "POST" and url.endswith("/chat/completions")
    assert headers["Authorization"] == "Bearer nim_key"


def test_openai_compat_maps_429_to_rate_limit() -> None:
    def fake_transport(method, url, headers, body):
        return 429, {"error": "rate limited"}

    p = NvidiaNimProvider("k", transport=fake_transport)
    with pytest.raises(RateLimitError):
        p.complete(MSGS)


def test_response_parser_extracts_code_and_json() -> None:
    text = 'Here:\n```python\nprint(1)\n```\nand\n```json\n{"a": 1}\n```'
    blocks = extract_code_blocks(text)
    assert "print(1)" in blocks[0]
    assert extract_json(text) == {"a": 1}
    assert extract_json("no structure here") is None
