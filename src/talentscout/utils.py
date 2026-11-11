"""Conservative per-run accounting with reservations and metadata-only audit events."""

import json
import logging
import os
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from time import monotonic


class BudgetExceeded(ValueError):
    pass


def positive_decimal(value: str, name: str) -> Decimal:
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be a positive finite number") from exc
    if not result.is_finite() or result <= 0:
        raise ValueError(f"{name} must be a positive finite number")
    return result


@dataclass(frozen=True)
class Settings:
    model: str = "claude-haiku-4-5-20251001"
    budget: Decimal = Decimal("5")
    input_rate: Decimal = Decimal("1")
    output_rate: Decimal = Decimal("5")
    max_output: int = 2048

    def __post_init__(self):
        for name in ("budget", "input_rate", "output_rate"):
            positive_decimal(str(getattr(self, name)), name)
        if not self.model.strip() or not 256 <= self.max_output <= 8192:
            raise ValueError("provide a model and MAX_OUTPUT_TOKENS between 256 and 8192")

    @classmethod
    def from_env(cls, budget: str | None = None) -> "Settings":
        return cls(
            model=os.getenv("MODEL_ID", cls.model),
            budget=positive_decimal(budget or os.getenv("BUDGET_USD", "5"), "BUDGET_USD"),
            input_rate=positive_decimal(os.getenv("INPUT_USD_PER_MTOK", "1"), "input rate"),
            output_rate=positive_decimal(os.getenv("OUTPUT_USD_PER_MTOK", "5"), "output rate"),
            max_output=int(os.getenv("MAX_OUTPUT_TOKENS", "2048")),
        )


@dataclass
class Budget:
    settings: Settings
    spent: Decimal = Decimal(0)
    reserved: Decimal = Decimal(0)
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0
    uncertain_calls: int = 0
    started: float = field(default_factory=monotonic)

    def cost(self, inputs: int, outputs: int) -> Decimal:
        return (inputs * self.settings.input_rate + outputs * self.settings.output_rate) / 1_000_000

    def reserve(self, inputs: int) -> Decimal:
        # Token counting is an estimate. Keep 10% + 1024 tokens for schema/serialization overhead.
        estimate = self.cost((inputs * 11 + 9) // 10 + 1024, self.settings.max_output)
        if self.spent + self.reserved + estimate > self.settings.budget:
            raise BudgetExceeded("next request would exceed the per-run budget; no call sent")
        self.reserved += estimate
        return estimate

    def settle(self, reservation: Decimal, inputs: int, outputs: int) -> None:
        self.reserved -= reservation
        self.spent += self.cost(inputs, outputs)
        self.input_tokens += inputs
        self.output_tokens += outputs
        self.calls += 1
        if self.spent > self.settings.budget:
            raise BudgetExceeded("reported usage exceeded the estimate; further calls stopped")

    def uncertain(self) -> None:
        # Do not release a reservation when a timeout may have incurred a charge.
        self.uncertain_calls += 1

    def metrics(self) -> dict:
        return {"model": self.settings.model, "calls": self.calls,
                "input_tokens": self.input_tokens, "output_tokens": self.output_tokens,
                "estimated_cost_usd": str(self.spent),
                "unresolved_reservation_usd": str(self.reserved),
                "uncertain_calls": self.uncertain_calls,
                "budget_usd": str(self.settings.budget),
                "elapsed_seconds": round(monotonic() - self.started, 3)}


class Audit:
    def __init__(self, path: Path | None = None):
        self.path = path

    def emit(self, event: str, **metadata) -> None:
        record = {"event": event, **metadata}
        logging.getLogger("talentscout").info(json.dumps(record, sort_keys=True))
        if self.path:
            # Only app-owned metadata is supplied: no resumes, names, prompts, keys or API errors.
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, sort_keys=True) + "\n")
