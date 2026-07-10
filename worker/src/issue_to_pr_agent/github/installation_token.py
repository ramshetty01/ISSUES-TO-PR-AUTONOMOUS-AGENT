"""Holder for the short-lived installation token the dispatcher injected."""

from __future__ import annotations

from ..errors import BootstrapError


class InstallationToken:
    """Wraps the installation token; refuses to hand out an empty token."""

    def __init__(self, token: str) -> None:
        self._token = token

    @property
    def token(self) -> str:
        if not self._token:
            raise BootstrapError("installation token is empty")
        return self._token

    def update(self, token: str) -> None:
        self._token = token
