"""Tests for certbot_dns_infoblox._infoblox (minimal WAPI client)."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from certbot_dns_infoblox._infoblox import InfobloxClient


@pytest.fixture
def mock_session():
    with patch("certbot_dns_infoblox._infoblox.requests.Session") as mock_cls:
        session = MagicMock()
        mock_cls.return_value = session
        session.headers = {}
        yield session


class TestInit:
    def test_basic_auth(self, mock_session):
        client = InfobloxClient("ib.example.net", "admin", "secret")
        assert mock_session.auth == ("admin", "secret")
        assert mock_session.verify is True
        assert client.base_url == "https://ib.example.net/wapi/v2.10/"
        assert client.view is None

    def test_with_view(self, mock_session):
        client = InfobloxClient("ib.example.net", "admin", "secret", view="external")
        assert client.view == "external"

    def test_ssl_verify_false(self, mock_session):
        InfobloxClient("ib.example.net", "admin", "secret", ssl_verify=False)
        assert mock_session.verify is False

    def test_ssl_verify_ca_bundle(self, mock_session):
        InfobloxClient(
            "ib.example.net", "admin", "secret", ssl_verify="/path/to/ca.pem"
        )
        assert mock_session.verify == "/path/to/ca.pem"

    def test_content_type_header(self, mock_session):
        InfobloxClient("ib.example.net", "admin", "secret")
        assert mock_session.headers["Content-Type"] == "application/json"


class TestCreateTxtRecord:
    def test_minimal(self, mock_session):
        mock_session.post.return_value.json.return_value = (
            "record:txt/ZG5z:_acme.example.com/default"
        )
        client = InfobloxClient("ib.example.net", "admin", "secret")

        ref = client.create_txt_record("_acme.example.com", "token123")

        mock_session.post.assert_called_once_with(
            "https://ib.example.net/wapi/v2.10/record:txt",
            json={"name": "_acme.example.com", "text": "token123"},
        )
        mock_session.post.return_value.raise_for_status.assert_called_once()
        assert ref == "record:txt/ZG5z:_acme.example.com/default"

    def test_full_params(self, mock_session):
        mock_session.post.return_value.json.return_value = "record:txt/ref123"
        client = InfobloxClient("ib.example.net", "admin", "secret", view="external")

        client.create_txt_record(
            "_acme.example.com",
            "token123",
            ttl=120,
            comment="auto-created",
        )

        mock_session.post.assert_called_once_with(
            "https://ib.example.net/wapi/v2.10/record:txt",
            json={
                "name": "_acme.example.com",
                "text": "token123",
                "ttl": 120,
                "view": "external",
                "comment": "auto-created",
            },
        )

    def test_raises_on_error(self, mock_session):
        mock_session.post.return_value.raise_for_status.side_effect = (
            requests.HTTPError("401 Unauthorized")
        )
        client = InfobloxClient("ib.example.net", "admin", "secret")

        with pytest.raises(requests.HTTPError):
            client.create_txt_record("_acme.example.com", "token123")


class TestSearchTxtRecords:
    def test_basic(self, mock_session):
        mock_session.get.return_value.json.return_value = [
            {"_ref": "record:txt/ref1", "name": "_acme.example.com", "text": "token123"}
        ]
        client = InfobloxClient("ib.example.net", "admin", "secret")

        results = client.search_txt_records("_acme.example.com")

        mock_session.get.assert_called_once_with(
            "https://ib.example.net/wapi/v2.10/record:txt",
            params={
                "name": "_acme.example.com",
                "_return_fields": "name,text,view",
            },
        )
        mock_session.get.return_value.raise_for_status.assert_called_once()
        assert len(results) == 1
        assert results[0]["_ref"] == "record:txt/ref1"

    def test_with_text_and_view(self, mock_session):
        mock_session.get.return_value.json.return_value = []
        client = InfobloxClient("ib.example.net", "admin", "secret", view="external")

        client.search_txt_records("_acme.example.com", text="token123")

        mock_session.get.assert_called_once_with(
            "https://ib.example.net/wapi/v2.10/record:txt",
            params={
                "name": "_acme.example.com",
                "text": "token123",
                "view": "external",
                "_return_fields": "name,text,view",
            },
        )

    def test_raises_on_error(self, mock_session):
        mock_session.get.return_value.raise_for_status.side_effect = requests.HTTPError(
            "500 Server Error"
        )
        client = InfobloxClient("ib.example.net", "admin", "secret")

        with pytest.raises(requests.HTTPError):
            client.search_txt_records("_acme.example.com")


class TestDeleteTxtRecord:
    def test_basic(self, mock_session):
        client = InfobloxClient("ib.example.net", "admin", "secret")

        client.delete_txt_record("record:txt/ZG5z:_acme.example.com/default")

        mock_session.delete.assert_called_once_with(
            "https://ib.example.net/wapi/v2.10/record:txt/ZG5z:_acme.example.com/default"
        )
        mock_session.delete.return_value.raise_for_status.assert_called_once()

    def test_raises_on_error(self, mock_session):
        mock_session.delete.return_value.raise_for_status.side_effect = (
            requests.HTTPError("404 Not Found")
        )
        client = InfobloxClient("ib.example.net", "admin", "secret")

        with pytest.raises(requests.HTTPError):
            client.delete_txt_record("record:txt/nonexistent")
