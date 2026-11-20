"""Fail-closed runtime configuration. The default environment is production.

A developer token is accepted ONLY with ENV=development and ALLOW_DEV_AUTH=true.
No development credentials, database, or OIDC issuer are supplied by defaults.
"""
import json
import os
from urllib.parse import urlparse
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    env: str = "production"
    database_url: str = ""
    allow_dev_auth: bool = False
    dev_auth_tokens_json: str = ""
    oidc_issuer: str = ""
    oidc_audience: str = ""
    oidc_jwks_url: str = ""
    retention_days: int = 30
    text_translator: str = "disabled"
    azure_translator_endpoint: str = ""
    azure_translator_key: str = ""
    azure_translator_region: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            env=os.getenv("ENV", "production"),
            database_url=os.getenv("DATABASE_URL", ""),
            allow_dev_auth=os.getenv("ALLOW_DEV_AUTH", "false").lower() == "true",
            dev_auth_tokens_json=os.getenv("DEV_AUTH_TOKENS_JSON", ""),
            oidc_issuer=os.getenv("OIDC_ISSUER", ""),
            oidc_audience=os.getenv("OIDC_AUDIENCE", ""),
            oidc_jwks_url=os.getenv("OIDC_JWKS_URL", ""),
            retention_days=int(os.getenv("RETENTION_DAYS", "30")),
            text_translator=os.getenv("TEXT_TRANSLATOR", "disabled"),
            azure_translator_endpoint=os.getenv("AZURE_TRANSLATOR_ENDPOINT", ""),
            azure_translator_key=os.getenv("AZURE_TRANSLATOR_KEY", ""),
            azure_translator_region=os.getenv("AZURE_TRANSLATOR_REGION", ""),
        )

    def dev_tokens(self) -> dict[str, dict[str, str]]:
        if not self.dev_auth_tokens_json:
            return {}
        raw = json.loads(self.dev_auth_tokens_json)
        if not isinstance(raw, dict):
            raise ValueError("DEV_AUTH_TOKENS_JSON must be a token-to-identity object")
        result = {}
        for token, identity in raw.items():
            if not isinstance(token, str) or len(token) < 24:
                raise ValueError("Development tokens must have at least 24 characters")
            if not isinstance(identity, dict) or not isinstance(identity.get("sub"), str) or not identity["sub"]:
                raise ValueError("Development identity must include a non-empty sub")
            scopes = identity.get("scope", "")
            if not isinstance(scopes, str):
                raise ValueError("Development identity scope must be a string")
            result[token] = {"sub": identity["sub"], "scope": scopes}
        return result

    def validate(self) -> None:
        if self.env not in ("development", "production"):
            raise ValueError("ENV must explicitly be development or production")
        if not self.database_url:
            raise ValueError("DATABASE_URL is mandatory; configure and migrate a real database")
        if self.retention_days < 1:
            raise ValueError("RETENTION_DAYS must be positive")
        if self.text_translator not in ("disabled", "azure"):
            raise ValueError("TEXT_TRANSLATOR must be disabled or azure")
        if self.text_translator == "azure":
            parsed = urlparse(self.azure_translator_endpoint)
            if (parsed.scheme != "https" or parsed.username or parsed.password or
                not parsed.hostname or not (parsed.hostname == "api.cognitive.microsofttranslator.com" or
                parsed.hostname.endswith(".cognitiveservices.azure.com")) or
                not (parsed.path.endswith("/translator/text/v3.0/translate") or
                     parsed.path == "/translate") or parsed.query or parsed.fragment or
                not self.azure_translator_key or not self.azure_translator_region):
                raise ValueError("Azure Translator requires HTTPS resource endpoint, key and region")
        if self.env == "production":
            if self.allow_dev_auth or self.dev_auth_tokens_json:
                raise ValueError("Development authentication cannot be enabled in production")
            if not self.database_url.startswith(("postgresql+psycopg://", "postgresql://")):
                raise ValueError("Production requires PostgreSQL")
        if self.allow_dev_auth:
            if self.env != "development" or not self.dev_tokens():
                raise ValueError("Development token auth requires ENV=development and token configuration")
        if not self.allow_dev_auth:
            if not (self.oidc_issuer.startswith("https://") and self.oidc_audience and self.oidc_jwks_url.startswith("https://")):
                raise ValueError("OIDC_ISSUER, OIDC_AUDIENCE and HTTPS OIDC_JWKS_URL are required")
