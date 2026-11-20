from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import jwt
import pytest
from fastapi import HTTPException
from cryptography.hazmat.primitives.asymmetric import rsa

from optilexis_api import auth
from optilexis_api.settings import Settings


def test_rs256_oidc_checks_issuer_audience_expiry_and_scopes(monkeypatch):
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = private.public_key()
    class MockKeys:
        def get_signing_key_from_jwt(self, token):
            return SimpleNamespace(key=public)
    monkeypatch.setattr(auth, "_jwks_client", lambda url: MockKeys())
    settings = Settings(env="production", database_url="postgresql+psycopg://ignored/unused",
                        oidc_issuer="https://accounts.example.test/", oidc_audience="optilexis-api",
                        oidc_jwks_url="https://accounts.example.test/.well-known/jwks.json")
    settings.validate()
    now = datetime.now(timezone.utc)
    claims = {"iss": settings.oidc_issuer, "aud": settings.oidc_audience,
              "sub": "user-oidc-123", "scope": "journeys:read journeys:write",
              "iat": now, "exp": now + timedelta(minutes=2)}
    good = jwt.encode(claims, private, algorithm="RS256", headers={"kid": "test-key"})
    principal = auth.verify_bearer(good, settings)
    assert principal.subject == "user-oidc-123" and "journeys:write" in principal.scopes
    for changes in ({"aud": "wrong"}, {"iss": "https://other.example/"},
                    {"exp": now - timedelta(minutes=5)}):
        bad = jwt.encode({**claims, **changes}, private, algorithm="RS256", headers={"kid": "test-key"})
        with pytest.raises(HTTPException) as exc:
            auth.verify_bearer(bad, settings)
        assert exc.value.status_code == 401
    with pytest.raises(HTTPException):
        auth.verify_bearer(jwt.encode(claims, "not-real-issuer-key-that-is-long-enough-for-hs256", algorithm="HS256"), settings)
