"""Azure Translator text-only adapter. Network/credentials are server-side only.

This is NOT live microphone recognition, synthesis, or route-aware translation.
Request and response text are never logged or saved by the application.
"""
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

import httpx
from pydantic import BaseModel, ConfigDict, Field

LANGUAGE = Literal['en', 'ja', 'fr', 'es', 'de', 'zh', 'th']


class LiveTextRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    journey_id: UUID
    text: str = Field(min_length=1, max_length=400)
    source_language: LANGUAGE = 'en'
    target_language: LANGUAGE
    user_activated: bool = False


class LiveTextResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    engine: Literal['azure_text_api'] = 'azure_text_api'
    simulated: bool = False
    audio_available: bool = False


class LiveTextUnavailable(Exception):
    pass


@dataclass
class AzureTextTranslator:
    endpoint: str
    key: str
    region: str
    transport: httpx.AsyncBaseTransport | None = None

    async def translate(self, text: str, source: str, target: str) -> str:
        """Azure Translator REST v3.0 custom resource endpoint; no redirects."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0),
                                         transport=self.transport,
                                         follow_redirects=False) as client:
                response = await client.post(
                    self.endpoint,
                    params={'api-version': '3.0', 'from': source, 'to': target},
                    json=[{'Text': text}],
                    headers={
                        'Ocp-Apim-Subscription-Key': self.key,
                        'Ocp-Apim-Subscription-Region': self.region,
                        'Content-Type': 'application/json',
                    },
                )
            if response.status_code != 200:
                raise LiveTextUnavailable('Translation provider unavailable')
            body = response.json()
            translated = body[0]['translations'][0]['text']
            if not isinstance(translated, str) or not translated:
                raise ValueError('Invalid provider text')
            return translated
        except (httpx.HTTPError, ValueError, LookupError, KeyError, IndexError, TypeError) as exc:
            raise LiveTextUnavailable('Translation provider unavailable') from exc
