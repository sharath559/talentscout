"""Interchangeable live SDK and hash-bound fixture providers."""

import json
import os
from pathlib import Path
from typing import Protocol, TypeVar

from .models import Contract
from .tools import fingerprint, read_text
from .utils import Audit, Budget, Settings

T = TypeVar("T", bound=Contract)


class ProviderError(ValueError):
    pass


class Provider(Protocol):
    def request(self, key: str, system: str, payload: dict, contract: type[T]) -> T: ...


class OfflineProvider:
    """Replay curated fixtures only if the entire stage input matches its recorded hash."""

    def __init__(self, path: Path, audit: Audit | None = None):
        self.fixtures = json.loads(read_text(path))
        self.audit = audit or Audit()
        self.calls = 0

    def request(self, key: str, system: str, payload: dict, contract: type[T]) -> T:
        entry = self.fixtures.get(key)
        if entry is None or entry["input_sha256"] != fingerprint(payload):
            raise ProviderError("offline fixtures do not match this input; use the bundled demo data")
        self.calls += 1
        self.audit.emit("fixture_replayed", stage=key.split(":")[0])
        return contract.model_validate_json(json.dumps(entry["output"]))

    def metrics(self) -> dict:
        return {"mode": "offline", "fixture_calls": self.calls, "api_calls": 0,
                "estimated_cost_usd": "0", "model": "curated-fixtures"}


class ClaudeProvider:
    def __init__(self, settings: Settings, audit: Audit | None = None, client=None):
        if client is None:
            from anthropic import Anthropic

            if not os.getenv("ANTHROPIC_API_KEY"):
                raise ProviderError("--live requires ANTHROPIC_API_KEY")
            client = Anthropic(max_retries=0, timeout=45.0)
        self.client = client
        self.settings = settings
        self.budget = Budget(settings)
        self.audit = audit or Audit()
        self._checked_model = False

    def _check_model(self) -> None:
        if self._checked_model:
            return
        try:
            info = self.client.models.retrieve(self.settings.model)
        except Exception:
            raise ProviderError("model lookup failed; verify MODEL_ID and API access") from None
        maximum = getattr(info, "max_output_tokens", None)
        if isinstance(maximum, int) and self.settings.max_output > maximum:
            raise ProviderError("MAX_OUTPUT_TOKENS exceeds the model's reported output limit")
        self._checked_model = True

    def request(self, key: str, system: str, payload: dict, contract: type[T]) -> T:
        from anthropic import transform_schema

        self._check_model()
        request = {"model": self.settings.model, "system": system,
                   "messages": [{"role": "user", "content": json.dumps(payload)}],
                   "output_config": {"format": {"type": "json_schema",
                                                "schema": transform_schema(contract)}}}
        # Count precisely the same input configuration that will be sent to generation.
        try:
            count = self.client.messages.count_tokens(**request).input_tokens
        except Exception:
            raise ProviderError("token preflight failed; no generation request sent") from None
        reservation = self.budget.reserve(count)
        self.audit.emit("request_reserved", stage=key.split(":")[0],
                        input_token_estimate=count, reservation_usd=str(reservation))
        try:
            response = self.client.messages.create(
                **request, max_tokens=self.settings.max_output,
            )
        except Exception:
            self.budget.uncertain()
            self.audit.emit("request_failed", stage=key.split(":")[0], billing="uncertain")
            raise ProviderError("generation failed; reservation retained; no automatic retry") from None
        # Charge successful responses before parsing, including refusals and truncated responses.
        self.budget.settle(reservation, response.usage.input_tokens, response.usage.output_tokens)
        self.audit.emit("request_completed", stage=key.split(":")[0],
                        input_tokens=response.usage.input_tokens,
                        output_tokens=response.usage.output_tokens)
        if response.stop_reason != "end_turn":
            raise ProviderError("response refused, truncated or incomplete; review stopped")
        if not response.content or any(block.type != "text" for block in response.content):
            raise ProviderError("unexpected response block; review stopped")
        text = "".join(block.text for block in response.content)
        return contract.model_validate_json(text)

    def metrics(self) -> dict:
        return {"mode": "live", **self.budget.metrics()}
