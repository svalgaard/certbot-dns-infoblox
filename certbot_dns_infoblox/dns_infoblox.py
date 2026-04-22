"""DNS Authenticator for Infoblox."""

import os
import time

from certbot import errors
from certbot.plugins import dns_common

from ._infoblox import InfobloxClient


class Authenticator(dns_common.DNSAuthenticator):
    """DNS Authenticator for Infoblox

    This Authenticator uses the Infoblox REST API to fulfill a
    dns-01 challenge.
    """

    description = (
        "Obtain certificates using a DNS TXT record "
        "(if you are using Infoblox for DNS)."
    )
    ttl = 120

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.credentials = None

    @classmethod
    def add_parser_arguments(cls, add, default_propagation_seconds: int = 120):
        super().add_parser_arguments(add, default_propagation_seconds=10)
        add(
            "credentials",
            help="Infoblox credentials INI file.",
            default="/etc/letsencrypt/infoblox.ini",
        )

    def more_info(self):
        return (
            "This plugin configures a DNS TXT record to respond to a "
            "dns-01 challenge using the Infoblox WAPI."
        )

    def _setup_credentials(self):
        self.credentials = self._configure_credentials(
            "credentials",
            "Infoblox credentials INI file",
            {
                "hostname": "Hostname for Infoblox WAPI.",
                "username": "Username for Infoblox WAPI.",
                "password": "Password for Infoblox WAPI.",
            },
            validator=self._validate_credentials,
        )

    @staticmethod
    def _validate_credentials(credentials):
        ssl_verify = credentials.conf("ssl_verify")
        if ssl_verify and ssl_verify.lower() not in ("true", "false"):
            raise errors.PluginError(
                f"Invalid value for ssl_verify: {ssl_verify!r}. Must be true or false."
            )

        ca_bundle = credentials.conf("ca_bundle")
        if ca_bundle:
            if not os.path.exists(ca_bundle):
                raise errors.PluginError(f"ca_bundle path does not exist: {ca_bundle}")

    infoclient = None

    def _get_infoblox_client(self):
        if not self.infoclient:
            ssl_verify_str = self.credentials.conf("ssl_verify")
            if ssl_verify_str and ssl_verify_str.lower() == "false":
                ssl_verify_value = False
            else:
                ssl_verify_value = self.credentials.conf("ca_bundle") or True
            view = self.credentials.conf("view") or None
            self.infoclient = InfobloxClient(
                host=self.credentials.conf("hostname"),
                username=self.credentials.conf("username"),
                password=self.credentials.conf("password"),
                ssl_verify=ssl_verify_value,
                view=view,
            )
        return self.infoclient

    def _perform(self, domain, validation_name, validation):
        client = self._get_infoblox_client()
        username = self.credentials.conf("username")
        comment = time.strftime(f"%Y-%m-%d %H:%M:%S: certbot-auto-{username}")
        client.create_txt_record(
            name=validation_name,
            text=validation,
            ttl=self.ttl,
            comment=comment,
        )

    def _cleanup(self, domain, validation_name, validation):
        client = self._get_infoblox_client()
        txts = client.search_txt_records(name=validation_name, text=validation)
        for txt in txts:
            client.delete_txt_record(txt["_ref"])
