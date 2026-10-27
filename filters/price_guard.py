"""
Haiox Project Scout - Price Guard & Currency Normalization
Module: filters/price_guard.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

from typing import Dict, Optional, Tuple
from core.schemas import RawJobPosting, UserFilterCriteria


class CurrencyConverter:
    """Handles multi-currency conversion to USD base using configurable exchange rates."""
    
    DEFAULT_RATES_TO_USD: Dict[str, float] = {
        "USD": 1.0,
        "EUR": 1.08,
        "GBP": 1.30,
        "CAD": 0.74,
        "AUD": 0.65,
        "SGD": 0.76,
        "NZD": 0.61,
        "CHF": 1.15,
        "SEK": 0.095,
        "NOK": 0.094,
        "DKK": 0.145,
        "JPY": 0.0067,
        "TOMAN": 0.000016,  # Domestic currency normalization support
        "IRR": 0.0000016,
    }

    def __init__(self, custom_rates: Optional[Dict[str, float]] = None):
        self.rates = dict(self.DEFAULT_RATES_TO_USD)
        if custom_rates:
            for cur, rate in custom_rates.items():
                self.rates[cur.upper()] = rate

    def to_usd(self, amount: float, currency: str) -> float:
        """Converts an amount in given currency to USD equivalent."""
        if amount <= 0:
            return 0.0
        cur_upper = currency.upper().strip()
        rate = self.rates.get(cur_upper, 1.0)  # Default fallback 1.0 if unknown
        return round(amount * rate, 2)


class PriceGuard:
    """
    Validates and screens project budgets against user-defined price criteria.
    Supports multi-currency conversion and flexible floor/ceiling thresholds.
    """

    def __init__(self, converter: Optional[CurrencyConverter] = None):
        self.converter = converter or CurrencyConverter()

    def evaluate(self, job: RawJobPosting, criteria: UserFilterCriteria) -> Tuple[bool, float, Optional[str]]:
        """
        Evaluates project pricing.
        Returns:
            - passed: bool
            - normalized_usd_price: float
            - reason: Optional rejection reason if rejected, or None if passed
        """
        # Currency check
        if criteria.allowed_currencies:
            allowed = [c.upper().strip() for c in criteria.allowed_currencies]
            if job.currency.upper().strip() not in allowed:
                return False, 0.0, f"Currency '{job.currency}' is not in allowed list: {allowed}"

        # Determine effective price (prefer budget_max, fallback to budget_min)
        nominal_price = job.budget_max if job.budget_max > 0 else job.budget_min
        
        # If no budget specified (0.0), decide whether to allow based on min_price
        if nominal_price <= 0:
            if criteria.min_price > 0:
                return False, 0.0, f"Unspecified project budget does not satisfy minimum price requirement ({criteria.min_price} USD)"
            return True, 0.0, None

        usd_price = self.converter.to_usd(nominal_price, job.currency)

        # Minimum Price Floor Check
        if criteria.min_price > 0 and usd_price < criteria.min_price:
            return False, usd_price, f"Normalized budget ({usd_price} USD) is below floor ({criteria.min_price} USD)"

        # Maximum Price Ceiling Check
        if criteria.max_price is not None and usd_price > criteria.max_price:
            return False, usd_price, f"Normalized budget ({usd_price} USD) exceeds ceiling ({criteria.max_price} USD)"

        return True, usd_price, None
