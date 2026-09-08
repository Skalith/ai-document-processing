"""Omniroute provider — OpenAI-compatible gateway/router.

Omniroute exposes every supported model behind one endpoint. The base URL
defaults to a locally-run gateway but can point at a cloud instance via
`OMNIROUTE_BASE_URL`. The special model name ``auto`` enables the gateway's
zero-config smart routing.
"""

from __future__ import annotations

from app.config import get_settings
from app.services.llm.providers.openai_compat import OpenAICompatibleProvider

settings = get_settings()


class OmnirouteProvider(OpenAICompatibleProvider):
    name = "omniroute"
    api_key_field = "omniroute_api_key"
    model_field = "omniroute_model"

    def __init__(self) -> None:
        self.model = getattr(settings, self.model_field)
        self.base_url = settings.omniroute_base_url
        self._client = None