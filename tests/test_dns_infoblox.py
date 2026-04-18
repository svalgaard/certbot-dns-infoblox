"""Tests for certbot_dns_infoblox.dns_infoblox (current infoblox-client based implementation)."""

import time
from unittest.mock import MagicMock, patch

import pytest

from certbot_dns_infoblox.dns_infoblox import Authenticator


@pytest.fixture
def authenticator():
    """Create an Authenticator with mocked credentials."""
    auth = Authenticator.__new__(Authenticator)
    auth.infoclient = None
    auth.infotxts = []
    auth.ttl = 120

    creds = MagicMock()
    conf_values = {
        "hostname": "infoblox.example.net",
        "username": "admin",
        "password": "secret",
        "view": "",
        "ca_bundle": "",
    }
    creds.conf = MagicMock(side_effect=lambda key: conf_values[key])
    auth.credentials = creds
    auth._conf_values = conf_values  # expose for test mutation
    return auth


class TestGetInfobloxClient:
    @patch("certbot_dns_infoblox.dns_infoblox.infoblox_client.connector.Connector")
    def test_basic(self, mock_connector_cls, authenticator):
        client = authenticator._get_infoblox_client()
        mock_connector_cls.assert_called_once_with(
            {
                "host": "infoblox.example.net",
                "username": "admin",
                "password": "secret",
                "ssl_verify": True,
            }
        )
        assert "connector" in client
        assert client["connector"] is mock_connector_cls.return_value
        assert "view" not in client

    @patch("certbot_dns_infoblox.dns_infoblox.infoblox_client.connector.Connector")
    def test_with_view(self, mock_connector_cls, authenticator):
        authenticator._conf_values["view"] = "external"
        client = authenticator._get_infoblox_client()
        assert client["view"] == "external"

    @patch("certbot_dns_infoblox.dns_infoblox.infoblox_client.connector.Connector")
    def test_with_ca_bundle(self, mock_connector_cls, authenticator):
        authenticator._conf_values["ca_bundle"] = "/path/to/ca.pem"
        authenticator._get_infoblox_client()
        mock_connector_cls.assert_called_once_with(
            {
                "host": "infoblox.example.net",
                "username": "admin",
                "password": "secret",
                "ssl_verify": "/path/to/ca.pem",
            }
        )

    @patch("certbot_dns_infoblox.dns_infoblox.infoblox_client.connector.Connector")
    def test_caches_client(self, mock_connector_cls, authenticator):
        client1 = authenticator._get_infoblox_client()
        client2 = authenticator._get_infoblox_client()
        # Connector should only be created once
        mock_connector_cls.assert_called_once()
        # But returns copies (different dicts, same connector)
        assert client1 is not client2
        assert client1["connector"] is client2["connector"]


class TestGetInfobloxRecord:
    @patch("certbot_dns_infoblox.dns_infoblox.infoblox_client.connector.Connector")
    def test_create_record(self, mock_connector_cls, authenticator):
        record = authenticator._get_infoblox_record(
            "_acme-challenge.example.com", "token123", create=True
        )
        assert record["name"] == "_acme-challenge.example.com"
        assert record["text"] == "token123"
        assert record["ttl"] == 120
        assert "certbot-auto-admin" in record["comment"]
        assert record["connector"] is mock_connector_cls.return_value

    @patch("certbot_dns_infoblox.dns_infoblox.infoblox_client.connector.Connector")
    def test_non_create_record(self, mock_connector_cls, authenticator):
        record = authenticator._get_infoblox_record(
            "_acme-challenge.example.com", "token123", create=False
        )
        assert record["name"] == "_acme-challenge.example.com"
        assert record["text"] == "token123"
        assert "ttl" not in record
        assert "comment" not in record


class TestPerform:
    @patch("certbot_dns_infoblox.dns_infoblox.infoblox_client.objects.TXTRecord")
    @patch("certbot_dns_infoblox.dns_infoblox.infoblox_client.connector.Connector")
    def test_creates_txt_record(
        self, mock_connector_cls, mock_txtrecord_cls, authenticator
    ):
        authenticator._perform("example.com", "_acme-challenge.example.com", "token123")

        mock_txtrecord_cls.create.assert_called_once()
        call_kwargs = mock_txtrecord_cls.create.call_args
        assert call_kwargs.kwargs["check_if_exists"] is False
        # The remaining args come from _get_infoblox_record via **kwargs
        # name, text, ttl, comment, connector are all passed
        assert call_kwargs.kwargs["name"] == "_acme-challenge.example.com"
        assert call_kwargs.kwargs["text"] == "token123"
        assert call_kwargs.kwargs["ttl"] == 120
        assert call_kwargs.kwargs["connector"] is mock_connector_cls.return_value

        # Record is appended to infotxts
        assert len(authenticator.infotxts) == 1
        assert authenticator.infotxts[0] is mock_txtrecord_cls.create.return_value


class TestCleanup:
    @patch("certbot_dns_infoblox.dns_infoblox.infoblox_client.connector.Connector")
    def test_deletes_cached_record(self, mock_connector_cls, authenticator):
        mock_txt = MagicMock()
        mock_txt.name = "_acme-challenge.example.com"
        mock_txt.text = "token123"
        authenticator.infotxts.append(mock_txt)

        authenticator._cleanup("example.com", "_acme-challenge.example.com", "token123")
        mock_txt.delete.assert_called_once()

    @patch("certbot_dns_infoblox.dns_infoblox.infoblox_client.objects.TXTRecord")
    @patch("certbot_dns_infoblox.dns_infoblox.infoblox_client.connector.Connector")
    def test_skips_non_matching_cached_records(
        self, mock_connector_cls, mock_txtrecord_cls, authenticator
    ):
        mock_txt = MagicMock()
        mock_txt.name = "_acme-challenge.other.com"
        mock_txt.text = "othertoken"
        authenticator.infotxts.append(mock_txt)

        mock_txtrecord_cls.search_all.return_value = []

        authenticator._cleanup("example.com", "_acme-challenge.example.com", "token123")
        mock_txt.delete.assert_not_called()
        mock_txtrecord_cls.search_all.assert_called_once()

    @patch("certbot_dns_infoblox.dns_infoblox.infoblox_client.objects.TXTRecord")
    @patch("certbot_dns_infoblox.dns_infoblox.infoblox_client.connector.Connector")
    def test_fallback_search_prints_records(
        self, mock_connector_cls, mock_txtrecord_cls, authenticator, capsys
    ):
        found_txt = MagicMock()
        found_txt.__str__ = (
            lambda self: "record:txt/ZG5zLmJpbmRfYQ:_acme-challenge.example.com/default"
        )
        mock_txtrecord_cls.search_all.return_value = [found_txt]

        authenticator._cleanup("example.com", "_acme-challenge.example.com", "token123")

        captured = capsys.readouterr()
        assert "Please delete this TXT record manually" in captured.out
