"""Verifies OIDC RS256 access JWTs or explicitly enabled local dev tokens.

Never trusts an unverified token's sub/scope, caller-supplied user IDs, or client headers.
"""
import hmac
from dataclasses import dataclass
from functools import lru_cache

import jwt
from jwt import PyJWKClient, InvalidTokenError
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .settings import Settings

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    issuer: str
    subject: str
    scopes: frozenset[str]


@lru_cache(maxsize=8)
def _jwks_client(url: str) -> PyJWKClient:
    return PyJWKClient(url, cache_jwk_set=True, lifespan=300, timeout=5)


def verify_bearer(token: str, settings: Settings) -> Principal:
    if settings.env == "development" and settings.allow_dev_auth:
        for expected, user in settings.dev_tokens().items():
            if hmac.compare_digest(token, expected):
                return Principal("optilexis-local-development", user["sub"], frozenset(user["scope"].split()))
        raise HTTPException(status_code=401, detail="Invalid access token")

    try:
        key = _jwks_client(settings.oidc_jwks_url).get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token, key, algorithms=["RS256"], audience=settings.oidc_audience,
            issuer=settings.oidc_issuer, options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            leeway=30,
        )
        scope = claims.get("scope", claims.get("scp", ""))
        scopes = scope.split() if isinstance(scope, str) else scope if isinstance(scope, list) else []
        if not isinstance(claims.get("sub"), str) or not claims["sub"]:
            raise InvalidTokenError("Missing subject")
        return Principal(claims["iss"], claims["sub"], frozenset(scopes))
    except (InvalidTokenError, jwt.PyJWKClientError, OSError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid access token") from exc


def require_scope(scope: str):
    def dependency(request: Request, authorization: HTTPAuthorizationCredentials | None = Depends(bearer)) -> Principal:
        if authorization is None or authorization.scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Bearer access token required", headers={"WWW-Authenticate": "Bearer"})
        principal = verify_bearer(authorization.credentials, request.app.state.settings)
        if scope not in principal.scopes:
            raise HTTPException(status_code=403, detail="Insufficient scope")
        return principal
    return dependency
