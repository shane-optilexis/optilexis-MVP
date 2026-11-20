"""Contract for future speech providers; curated demo remains the only enabled provider."""
import asyncio
from dataclasses import dataclass
from time import monotonic
from typing import Callable, Protocol

from .models import PhraseRequest, PhraseResponse
from .phrases import phrase_for


class TranslationUnavailable(RuntimeError):
    pass


class ConsentRequired(TranslationUnavailable):
    pass


@dataclass(frozen=True)
class TranslationPolicy:
    microphone_consent: bool
    os_microphone_permission: bool
    user_activated: bool
    max_input_bytes: int = 256_000
    timeout_seconds: float = 5.0
    max_estimated_cost_usd: float = 0.05

    def require_microphone(self, size: int, estimated_cost_usd: float = 0.0) -> None:
        if not (self.microphone_consent and self.os_microphone_permission and self.user_activated):
            raise ConsentRequired("Microphone requires explicit action, consent, and OS permission")
        if size > self.max_input_bytes:
            raise TranslationUnavailable("Audio exceeds request limit")
        if estimated_cost_usd < 0 or estimated_cost_usd > self.max_estimated_cost_usd:
            raise TranslationUnavailable("Estimated provider cost exceeds request budget")


class SpeechTranslator(Protocol):
    async def transcribe(self, audio: bytes, language: str) -> str: ...
    async def translate(self, text: str, language: str) -> str: ...
    async def synthesize(self, text: str, language: str) -> bytes: ...


class UnconfiguredSpeechTranslator:
    async def transcribe(self, audio: bytes, language: str) -> str:
        raise TranslationUnavailable("ASR provider not configured")

    async def translate(self, text: str, language: str) -> str:
        raise TranslationUnavailable("Machine translation provider not configured")

    async def synthesize(self, text: str, language: str) -> bytes:
        raise TranslationUnavailable("TTS provider not configured")


class CuratedPhraseProvider:
    def lookup(self, request: PhraseRequest) -> PhraseResponse:
        return phrase_for(request)


async def transcribe_with_policy(
    translator: SpeechTranslator, audio: bytes, language: str,
    policy: TranslationPolicy, record_metric: Callable[[str, int], None],
    *, estimated_cost_usd: float = 0.0,
) -> str:
    """No audio/transcript content is logged; metric callback receives status + latency only."""
    policy.require_microphone(len(audio), estimated_cost_usd)
    start = monotonic()
    status = "ok"
    try:
        return await asyncio.wait_for(translator.transcribe(audio, language), timeout=policy.timeout_seconds)
    except asyncio.TimeoutError:
        status = "timeout"
        raise TranslationUnavailable("Speech provider timed out") from None
    except Exception:
        status = "error"
        raise
    finally:
        record_metric(status, int((monotonic() - start) * 1000))
