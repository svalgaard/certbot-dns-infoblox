"""Tests for certbot_dns_infoblox.dns_infoblox (InfobloxClient-based implementation)."""

from unittest.mock import MagicMock, patch

import pytest
from certbot import errors

from certbot_dns_infoblox.dns_infoblox import Authenticator


@pytest.fixture
def mock_client():
    with patch("certbot_dns_infoblox.dns_infoblox.InfobloxClient") as mock_cls:
        yield mock_cls.return_value


@pytest.fixture
def authenticator():
    """Create an Authenticator with mocked credentials."""
    auth = Authenticator.__new__(Authenticator)
    auth.infoclient = None
    auth.ttl = 120

    creds = MagicMock()
    conf_values = {
        "hostname": "infoblox.example.net",
        "username": "admin",
        "password": "secret",
        "view": "",
        "ssl_verify": "",
        "ca_bundle": "",
    }
    creds.conf = MagicMock(side_effect=lambda key: conf_values.get(key))
    auth.credentials = creds
    auth._conf_values = conf_values  # expose for test mutation
    return auth


class TestAuthenticatorInit:
    def test_init(self):
        with patch.object(Authenticator, "__init__", lambda self, *a, **kw: None):
            Authenticator()
        # The real __init__ calls super().__init__ and sets credentials = None
        # We just verify the class can be instantiated

    @patch("certbot_dns_infoblox.dns_infoblox.dns_common.DNSAuthenticator.__init__")
    def test_init_calls_super_and_sets_credentials(self, mock_super_init):
        mock_super_init.return_value = None
        auth = Authenticator("config", "name")
        mock_super_init.assert_called_once_with("config", "name")
        assert auth.credentials is None


class TestAddParserArguments:
    def test_add_parser_arguments(self):
        mock_add = MagicMock()
        with patch(
            "certbot_dns_infoblox.dns_infoblox.dns_common.DNSAuthenticator.add_parser_arguments"
        ):
            Authenticator.add_parser_arguments(mock_add)
        mock_add.assert_called_once_with(
            "credentials",
            help="Infoblox credentials INI file.",
            default="/etc/letsencrypt/infoblox.ini",
        )


class TestMoreInfo:
    def test_more_info(self, authenticator):
        info = authenticator.more_info()
        assert "DNS TXT record" in info
        assert "Infoblox" in info


class TestSetupCredentials:
    def test_setup_credentials(self, authenticator):
        authenticator._configure_credentials = MagicMock()
        authenticator._setup_credentials()
        authenticator._configure_credentials.assert_called_once()
        args = authenticator._configure_credentials.call_args
        assert args[0][0] == "credentials"
        assert "hostname" in args[0][2]
        assert "username" in args[0][2]
        assert "password" in args[0][2]

    def test_view_is_optional(self, authenticator):
        """view should not be in the required_variables dict."""
        authenticator._configure_credentials = MagicMock()
        authenticator._setup_credentials()
        required_variables = authenticator._configure_credentials.call_args[0][2]
        assert "view" not in required_variables

    def test_ssl_verify_is_optional(self, authenticator):
        """ssl_verify should not be in the required_variables dict."""
        authenticator._configure_credentials = MagicMock()
        authenticator._setup_credentials()
        required_variables = authenticator._configure_credentials.call_args[0][2]
        assert "ssl_verify" not in required_variables

    def test_ca_bundle_is_optional(self, authenticator):
        """ca_bundle should not be in the required_variables dict."""
        authenticator._configure_credentials = MagicMock()
        authenticator._setup_credentials()
        required_variables = authenticator._configure_credentials.call_args[0][2]
        assert "ca_bundle" not in required_variables

    def test_validator_is_passed(self, authenticator):
        authenticator._configure_credentials = MagicMock()
        authenticator._setup_credentials()
        kwargs = authenticator._configure_credentials.call_args[1]
        assert kwargs["validator"] is Authenticator._validate_credentials


class TestValidateCredentials:
    def test_accepts_empty(self):
        """No ssl_verify or ca_bundle set should be accepted."""
        creds = MagicMock()
        creds.conf = MagicMock(side_effect=lambda key: None)
        Authenticator._validate_credentials(creds)

    def test_accepts_ssl_verify_true(self):
        values = {"ssl_verify": "true", "ca_bundle": None}
        creds = MagicMock()
        creds.conf = MagicMock(side_effect=lambda key: values.get(key))
        Authenticator._validate_credentials(creds)

    def test_accepts_ssl_verify_false(self):
        values = {"ssl_verify": "false", "ca_bundle": None}
        creds = MagicMock()
        creds.conf = MagicMock(side_effect=lambda key: values.get(key))
        Authenticator._validate_credentials(creds)

    def test_rejects_invalid_ssl_verify(self):
        values = {"ssl_verify": "maybe", "ca_bundle": None}
        creds = MagicMock()
        creds.conf = MagicMock(side_effect=lambda key: values.get(key))
        with pytest.raises(errors.PluginError, match="Invalid value for ssl_verify"):
            Authenticator._validate_credentials(creds)

    @patch("certbot_dns_infoblox.dns_infoblox.os.path.exists", return_value=True)
    def test_accepts_existing_ca_bundle(self, mock_exists):
        values = {"ssl_verify": None, "ca_bundle": "/path/to/ca.pem"}
        creds = MagicMock()
        creds.conf = MagicMock(side_effect=lambda key: values.get(key))
        Authenticator._validate_credentials(creds)
        mock_exists.assert_called_once_with("/path/to/ca.pem")

    @patch("certbot_dns_infoblox.dns_infoblox.os.path.exists", return_value=False)
    def test_rejects_nonexistent_ca_bundle(self, mock_exists):
        values = {"ssl_verify": None, "ca_bundle": "/no/such/path.pem"}
        creds = MagicMock()
        creds.conf = MagicMock(side_effect=lambda key: values.get(key))
        with pytest.raises(errors.PluginError, match="ca_bundle path does not exist"):
            Authenticator._validate_credentials(creds)


class TestGetInfobloxClient:
    def test_basic(self, mock_client, authenticator):
        from certbot_dns_infoblox.dns_infoblox import InfobloxClient

        client = authenticator._get_infoblox_client()
        InfobloxClient.assert_called_once_with(
            host="infoblox.example.net",
            username="admin",
            password="secret",
            ssl_verify=True,
            view=None,
        )
        assert client is mock_client

    def test_ssl_verify_false(self, mock_client, authenticator):
        from certbot_dns_infoblox.dns_infoblox import InfobloxClient

        authenticator._conf_values["ssl_verify"] = "false"
        authenticator._get_infoblox_client()
        InfobloxClient.assert_called_once_with(
            host="infoblox.example.net",
            username="admin",
            password="secret",
            ssl_verify=False,
            view=None,
        )

    def test_ssl_verify_False(self, mock_client, authenticator):
        from certbot_dns_infoblox.dns_infoblox import InfobloxClient

        authenticator._conf_values["ssl_verify"] = "False"
        authenticator._get_infoblox_client()
        InfobloxClient.assert_called_once_with(
            host="infoblox.example.net",
            username="admin",
            password="secret",
            ssl_verify=False,
            view=None,
        )

    def test_ssl_verify_true(self, mock_client, authenticator):
        from certbot_dns_infoblox.dns_infoblox import InfobloxClient

        authenticator._conf_values["ssl_verify"] = "true"
        authenticator._get_infoblox_client()
        InfobloxClient.assert_called_once_with(
            host="infoblox.example.net",
            username="admin",
            password="secret",
            ssl_verify=True,
            view=None,
        )

    def test_with_ca_bundle(self, mock_client, authenticator):
        from certbot_dns_infoblox.dns_infoblox import InfobloxClient

        authenticator._conf_values["ca_bundle"] = "/path/to/ca.pem"
        authenticator._get_infoblox_client()
        InfobloxClient.assert_called_once_with(
            host="infoblox.example.net",
            username="admin",
            password="secret",
            ssl_verify="/path/to/ca.pem",
            view=None,
        )

    def test_ssl_verify_false_overrides_ca_bundle(self, mock_client, authenticator):
        """ssl_verify=false takes precedence over ca_bundle."""
        from certbot_dns_infoblox.dns_infoblox import InfobloxClient

        authenticator._conf_values["ssl_verify"] = "false"
        authenticator._conf_values["ca_bundle"] = "/path/to/ca.pem"
        authenticator._get_infoblox_client()
        InfobloxClient.assert_called_once_with(
            host="infoblox.example.net",
            username="admin",
            password="secret",
            ssl_verify=False,
            view=None,
        )

    def test_with_view(self, mock_client, authenticator):
        from certbot_dns_infoblox.dns_infoblox import InfobloxClient

        authenticator._conf_values["view"] = "external"
        authenticator._get_infoblox_client()
        InfobloxClient.assert_called_once_with(
            host="infoblox.example.net",
            username="admin",
            password="secret",
            ssl_verify=True,
            view="external",
        )

    def test_without_optional_params(self, mock_client, authenticator):
        """Client should work when optional params return None."""
        from certbot_dns_infoblox.dns_infoblox import InfobloxClient

        authenticator._conf_values["view"] = None
        authenticator._conf_values["ssl_verify"] = None
        authenticator._conf_values["ca_bundle"] = None
        authenticator._get_infoblox_client()
        InfobloxClient.assert_called_once_with(
            host="infoblox.example.net",
            username="admin",
            password="secret",
            ssl_verify=True,
            view=None,
        )

    def test_caches_client(self, mock_client, authenticator):
        from certbot_dns_infoblox.dns_infoblox import InfobloxClient

        client1 = authenticator._get_infoblox_client()
        client2 = authenticator._get_infoblox_client()
        InfobloxClient.assert_called_once()
        assert client1 is client2


class TestPerform:
    def test_creates_txt_record(self, mock_client, authenticator):
        authenticator._perform("example.com", "_acme-challenge.example.com", "token123")

        mock_client.create_txt_record.assert_called_once()
        call_kwargs = mock_client.create_txt_record.call_args.kwargs
        assert call_kwargs["name"] == "_acme-challenge.example.com"
        assert call_kwargs["text"] == "token123"
        assert call_kwargs["ttl"] == 120
        assert "view" not in call_kwargs
        assert "certbot-admin" in call_kwargs["comment"]

    def test_creates_with_view(self, mock_client, authenticator):
        authenticator._conf_values["view"] = "external"
        authenticator.infoclient = None

        authenticator._perform("example.com", "_acme-challenge.example.com", "token123")

        mock_client.create_txt_record.assert_called_once()
        call_kwargs = mock_client.create_txt_record.call_args.kwargs
        assert "view" not in call_kwargs


class TestCleanup:
    def test_searches_and_deletes_records(self, mock_client, authenticator):
        mock_client.search_txt_records.return_value = [
            {
                "_ref": "record:txt/found1",
                "name": "_acme-challenge.example.com",
                "text": "token123",
            },
        ]

        authenticator._cleanup("example.com", "_acme-challenge.example.com", "token123")

        mock_client.search_txt_records.assert_called_once_with(
            name="_acme-challenge.example.com", text="token123"
        )
        mock_client.delete_txt_record.assert_called_once_with("record:txt/found1")

    def test_deletes_multiple_records(self, mock_client, authenticator):
        mock_client.search_txt_records.return_value = [
            {
                "_ref": "record:txt/found1",
                "name": "_acme-challenge.example.com",
                "text": "token123",
            },
            {
                "_ref": "record:txt/found2",
                "name": "_acme-challenge.example.com",
                "text": "token123",
            },
        ]

        authenticator._cleanup("example.com", "_acme-challenge.example.com", "token123")

        assert mock_client.delete_txt_record.call_count == 2
        mock_client.delete_txt_record.assert_any_call("record:txt/found1")
        mock_client.delete_txt_record.assert_any_call("record:txt/found2")

    def test_no_records_found(self, mock_client, authenticator):
        mock_client.search_txt_records.return_value = []

        authenticator._cleanup("example.com", "_acme-challenge.example.com", "token123")

        mock_client.search_txt_records.assert_called_once()
        mock_client.delete_txt_record.assert_not_called()

    def test_search_with_view(self, mock_client, authenticator):
        authenticator._conf_values["view"] = "external"
        authenticator.infoclient = None
        mock_client.search_txt_records.return_value = []

        authenticator._cleanup("example.com", "_acme-challenge.example.com", "token123")

        mock_client.search_txt_records.assert_called_once_with(
            name="_acme-challenge.example.com", text="token123"
        )
