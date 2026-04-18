"""Minimal Infoblox WAPI client using requests."""

from __future__ import annotations

import requests


class InfobloxClient:
    """A minimal client for the Infoblox WAPI, covering only TXT record operations."""

    WAPI_VERSION = "2.10"

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        ssl_verify: bool | str = True,
        view: str | None = None,
    ) -> None:
        self.base_url = f"https://{host}/wapi/v{self.WAPI_VERSION}/"
        self.view = view
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.verify = ssl_verify
        self.session.headers.update({"Content-Type": "application/json"})

    def create_txt_record(
        self,
        name: str,
        text: str,
        ttl: int | None = None,
        comment: str | None = None,
    ) -> str:
        """Create a TXT record. Returns the object reference string."""
        payload: dict[str, str | int] = {"name": name, "text": text}
        if ttl is not None:
            payload["ttl"] = ttl
        if self.view is not None:
            payload["view"] = self.view
        if comment is not None:
            payload["comment"] = comment
        resp = self.session.post(self.base_url + "record:txt", json=payload)
        resp.raise_for_status()
        return resp.json()

    def search_txt_records(
        self, name: str, text: str | None = None
    ) -> list[dict[str, str]]:
        """Search for TXT records by name. Returns a list of record dicts."""
        params: dict[str, str] = {"name": name, "_return_fields": "name,text,view"}
        if text is not None:
            params["text"] = text
        if self.view is not None:
            params["view"] = self.view
        resp = self.session.get(self.base_url + "record:txt", params=params)
        resp.raise_for_status()
        return resp.json()

    def delete_txt_record(self, ref: str) -> None:
        """Delete a TXT record by its object reference."""
        resp = self.session.delete(self.base_url + ref)
        resp.raise_for_status()
