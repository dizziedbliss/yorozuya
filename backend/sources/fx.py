"""Exchange rates (ECB data via Frankfurter, free) so salaries convert to ₹ LPA. Saved for the next run."""

from typing import Any

import httpx

from sources.base import SourceResult, raise_for_block


class FxSource:
    name = "fx-rates"
    config_key = "rates_to_inr"

    async def fetch(self, client: httpx.AsyncClient, settings: dict[str, Any]) -> SourceResult:
        response = await client.get(
            "https://api.frankfurter.dev/v1/latest", params={"base": "INR", "symbols": "USD,EUR,GBP"}
        )
        raise_for_block(response)
        rates = response.json()["rates"]
        return SourceResult(state={code: round(1 / per_rupee, 2) for code, per_rupee in rates.items()})
