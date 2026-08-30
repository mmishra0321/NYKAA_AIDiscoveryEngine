from src.generation.lint import lint_hits


def test_lint_catches_monetary_incentives():
    blob = "We should send coupons and cashback, plus a 20% off price-cut."
    hits = lint_hits(blob)
    assert "coupons" in hits
    assert "cashback" in hits or any("cash" in h for h in hits)
    assert any("off" in h or "price" in h for h in hits)


def test_lint_allows_price_as_decision_factor():
    assert not lint_hits("Fit, size, and price as a signal all show up after save.")
