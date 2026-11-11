from decimal import Decimal

import pytest

from talentscout.utils import Budget, BudgetExceeded, Settings, positive_decimal


@pytest.mark.parametrize("value", ["0", "-1", "NaN", "Infinity", "bad"])
def test_invalid_budget(value):
    with pytest.raises(ValueError):
        positive_decimal(value, "budget")


def test_full_output_reservation_prevents_overspend():
    budget = Budget(Settings(budget=Decimal("0.001")))
    with pytest.raises(BudgetExceeded):
        budget.reserve(10)
    assert budget.reserved == 0


def test_multiple_calls_share_budget():
    budget = Budget(Settings(budget=Decimal("0.02")))
    reservation = budget.reserve(100)
    budget.settle(reservation, 100, 2000)
    assert budget.spent == Decimal("0.0101")
    with pytest.raises(BudgetExceeded):
        budget.reserve(100)


def test_uncertain_call_keeps_reservation():
    budget = Budget(Settings())
    reservation = budget.reserve(100)
    budget.uncertain()
    assert budget.reserved == reservation
    assert budget.metrics()["uncertain_calls"] == 1


def test_usage_surprise_stops_more_calls():
    budget = Budget(Settings(budget=Decimal("0.02")))
    reservation = budget.reserve(100)
    with pytest.raises(BudgetExceeded, match="reported usage"):
        budget.settle(reservation, 100000, 10000)
