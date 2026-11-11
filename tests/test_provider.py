"""Exercise the real SDK against a local HTTP mock; no paid or network requests."""

import json
from decimal import Decimal

import httpx
import pytest
from anthropic import Anthropic
from pydantic import ValidationError

from talentscout.models import Hello
from talentscout.providers import ClaudeProvider, ProviderError
from talentscout.utils import Audit, BudgetExceeded, Settings


def make_provider(*, settings=None, stop="end_turn", text=None, failure=None, model_max=8192):
    requests = []

    def handler(request):
        body = json.loads(request.content) if request.content else {}
        requests.append((request.url.path, body))
        if request.url.path.startswith("/v1/models/"):
            return httpx.Response(
                200,
                json={
                    "id": "mock-model",
                    "type": "model",
                    "created_at": "2026-01-01T00:00:00Z",
                    "display_name": "Local mock",
                    "max_tokens": model_max,
                },
            )
        if request.url.path.endswith("count_tokens"):
            if failure == "count":
                return httpx.Response(500, json={"error": {"message": "private text"}})
            return httpx.Response(200, json={"input_tokens": 123})
        if failure == "timeout":
            raise httpx.ReadTimeout("private resume or key must not escape", request=request)
        return httpx.Response(
            200,
            json={
                "id": "msg_local",
                "type": "message",
                "role": "assistant",
                "model": "mock-model",
                "content": [
                    {
                        "type": "text",
                        "text": text
                        if text is not None
                        else json.dumps({"message": "Hello from the local HTTP mock."}),
                    }
                ],
                "stop_reason": stop,
                "stop_sequence": None,
                "usage": {"input_tokens": 123, "output_tokens": 20},
            },
        )

    client = Anthropic(
        api_key="test-key-not-a-secret",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    return ClaudeProvider(settings or Settings(), client=client), requests


def test_sdk_serializes_same_count_and_generation_input():
    provider, requests = make_provider()
    assert provider.request("hello", "System prompt", {"action": "hello"}, Hello).message
    count_request, generation = requests[1][1], dict(requests[2][1])
    assert generation.pop("max_tokens") == 2048
    assert count_request == generation
    schema = generation["output_config"]["format"]["schema"]
    assert schema["additionalProperties"] is False
    assert "maxLength" not in schema["properties"]["message"]
    assert provider.budget.spent == Decimal("0.000223")
    assert provider.budget.reserved == 0


def test_no_generation_when_budget_is_too_low():
    provider, requests = make_provider(settings=Settings(budget=Decimal("0.00001")))
    with pytest.raises(BudgetExceeded):
        provider.request("hello", "System", {}, Hello)
    assert len(requests) == 2
    assert provider.budget.calls == 0


def test_count_failure_never_generates():
    provider, requests = make_provider(failure="count")
    with pytest.raises(ProviderError, match="preflight failed"):
        provider.request("hello", "System", {}, Hello)
    assert len(requests) == 2


def test_timeout_is_not_retried_or_exposed():
    provider, requests = make_provider(failure="timeout")
    with pytest.raises(ProviderError) as caught:
        provider.request("hello", "System", {}, Hello)
    assert "private" not in str(caught.value)
    assert len(requests) == 3
    assert provider.budget.uncertain_calls == 1
    assert provider.budget.reserved > 0


@pytest.mark.parametrize("stop", ["max_tokens", "refusal", "tool_use"])
def test_incomplete_or_refused_response_is_accounted_and_rejected(stop):
    provider, _ = make_provider(stop=stop)
    with pytest.raises(ProviderError, match="incomplete"):
        provider.request("hello", "System", {}, Hello)
    assert provider.budget.calls == 1
    assert provider.budget.spent > 0


@pytest.mark.parametrize(
    "text", ['{"message":"ok","execute":"bad"}', "invalid JSON", '{"message":""}']
)
def test_malformed_output_still_charged(text):
    provider, _ = make_provider(text=text)
    with pytest.raises(ValidationError):
        provider.request("hello", "System", {}, Hello)
    assert provider.budget.calls == 1


def test_model_output_cap_checked_before_generation():
    provider, requests = make_provider(model_max=100)
    with pytest.raises(ProviderError, match="output limit"):
        provider.request("hello", "System", {}, Hello)
    assert len(requests) == 1


def test_log_has_usage_without_resume_content(tmp_path):
    provider, _ = make_provider()
    path = tmp_path / "audit.jsonl"
    provider.audit = Audit(path)
    provider.request("hello", "private system", {"resume": "private document"}, Hello)
    text = path.read_text()
    assert "input_tokens" in text
    assert "private" not in text
    assert "test-key" not in text
