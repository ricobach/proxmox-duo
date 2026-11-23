"""Isolated Duo Auth API client. No Proxmox login hooks are installed."""
from __future__ import annotations

from dataclasses import dataclass
import re

import duo_client

_HOST_PATTERN = re.compile(r"^api-[a-z0-9-]+\\.duosecurity\\.com$", re.I)


@dataclass(frozen=True)
class Settings:
    ikey: str
    skey: str
    host: str

    def __post_init__(self) -> None:
        if not self.ikey or not self.skey:
            raise ValueError("Duo integration key and secret are required")
        if not _HOST_PATTERN.fullmatch(self.host):
            raise ValueError("Duo host must be a duosecurity.com API hostname")


class DuoPush:
    """Request and inspect Push only; no OTP or bypass functionality."""

    def __init__(self, settings: Settings, client=None):
        self._client = client or duo_client.Auth(
            ikey=settings.ikey, skey=settings.skey, host=settings.host
        )

    def check(self) -> dict:
        return self._client.check()

    def start(self, username: str) -> str:
        if not username or username.strip() != username or "@" in username:
            raise ValueError("Expected a nonempty local Duo username without realm")
        # Preauthentication is intentionally not consulted to avoid interpreting
        # an enroll/bypass response as successful second-factor authentication.
        response = self._client.auth(
            factor="push", username=username, device="auto", async_txn=True
        )
        txid = response.get("txid") if isinstance(response, dict) else None
        if not isinstance(txid, str) or not txid:
            raise RuntimeError("Duo did not issue an asynchronous Push transaction")
        return txid

    def status(self, txid: str) -> dict:
        if not isinstance(txid, str) or not txid:
            raise ValueError("Invalid transaction identifier")
        raw = self._client.auth_status(txid)
        if not isinstance(raw, dict):
            raise RuntimeError("Invalid Duo status response")
        # Explicitly ignore trusted_device_token: no trusted-device bypass.
        if raw.get("waiting") is True:
            state = "waiting"
        elif raw.get("success") is True:
            state = "approved"
        else:
            state = "denied"
        return {"state": state, "message": str(raw.get("status_msg") or "")}
