"""DNS Authenticator for Infoblox."""

import json
import logging
import os
import time

from certbot import errors
from certbot.plugins import dns_common

from ._infoblox import InfobloxClient

logger = logging.getLogger(__name__)


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
    def add_parser_arguments(cls, add, default_propagation_seconds: int = 60):
        super().add_parser_arguments(add, default_propagation_seconds=60)
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

        translation_table = credentials.conf("translation_table")
        if translation_table:
            if not os.path.isfile(translation_table):
                raise errors.PluginError(
                    f"translation_table path does not exist: {translation_table}"
                )

    infoclient = None
    _translation_table = None
    _translation_table_loaded = False

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
            logger.debug(
                "Created Infoblox client for %s", self.credentials.conf("hostname")
            )
        return self.infoclient

    def _load_translation_table(self):
        """Load and cache the translation table from the configured JSON file."""
        if self._translation_table_loaded:
            return self._translation_table
        self._translation_table_loaded = True
        path = self.credentials.conf("translation_table")
        if not path:
            return None
        try:
            with open(path, encoding="utf-8") as f:
                table = json.load(f)
        except FileNotFoundError:
            raise errors.PluginError(
                f"translation_table file not found: {path}"
            ) from None
        except json.JSONDecodeError as e:
            raise errors.PluginError(
                f"translation_table is not valid JSON: {e}"
            ) from None
        if not isinstance(table, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in table.items()
        ):
            raise errors.PluginError(
                "translation_table must be a JSON object mapping strings to strings"
            )
        self._translation_table = table
        logger.debug(
            "Loaded translation table with %d entries from %s",
            len(table),
            path,
        )
        return self._translation_table

    def _translate_domain(self, validation_name):
        """Translate a validation domain name using the translation table.

        Finds the longest matching domain suffix from the table keys
        (matching on domain boundaries only) and replaces it with the
        mapped value.
        """
        table = self._load_translation_table()
        if not table:
            return validation_name
        best_key = None
        for key in table:
            if validation_name == key or validation_name.endswith("." + key):
                if best_key is None or len(key) > len(best_key):
                    best_key = key
        if best_key is None:
            return validation_name
        if validation_name == best_key:
            translated = table[best_key]
        else:
            prefix = validation_name[: -(len(best_key))]
            translated = prefix + table[best_key]
        logger.info("Translated %s -> %s", validation_name, translated)
        return translated

    def _perform(self, domain, validation_name, validation):
        client = self._get_infoblox_client()
        validation_name = self._translate_domain(validation_name)
        username = self.credentials.conf("username")
        comment = time.strftime(f"%Y-%m-%d %H:%M:%S: certbot-auto-{username}")
        logger.debug("Creating TXT record for %s", validation_name)
        client.create_txt_record(
            name=validation_name,
            text=validation,
            ttl=self.ttl,
            comment=comment,
        )

    def _cleanup(self, domain, validation_name, validation):
        client = self._get_infoblox_client()
        validation_name = self._translate_domain(validation_name)
        txts = client.search_txt_records(name=validation_name, text=validation)
        logger.debug("Found %d TXT record(s) for %s", len(txts), validation_name)
        for txt in txts:
            client.delete_txt_record(txt["_ref"])
