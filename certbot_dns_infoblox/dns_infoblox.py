"""DNS Authenticator for Infoblox."""
import logging
import time

import infoblox_client.connector
import infoblox_client.objects
import zope.interface
from certbot import interfaces
from certbot.plugins import dns_common

logger = logging.getLogger(__name__)


@zope.interface.implementer(interfaces.IAuthenticator)
@zope.interface.provider(interfaces.IPluginFactory)
class Authenticator(dns_common.DNSAuthenticator):
    """DNS Authenticator for Infoblox

    This Authenticator uses the Infoblox REST API to fulfill a
    dns-01 challenge.
    """

    description = ("Obtain certificates using a DNS TXT record "
                   "(if you are using Infoblox for DNS).")
    ttl = 120

    def __init__(self, *args, **kwargs):
        super(Authenticator, self).__init__(*args, **kwargs)
        self.credentials = None

    @classmethod
    def add_parser_arguments(cls, add):  # pylint: disable=arguments-differ
        super(Authenticator, cls).add_parser_arguments(
            add, default_propagation_seconds=10
        )
        add("credentials", help="Infoblox credentials INI file.",
            default='/etc/letsencrypt/infoblox.ini')

    def more_info(self):  # pylint: disable=missing-docstring,no-self-use
        return (
            "This plugin configures a DNS TXT record to respond to a "
            "dns-01 challenge using the Infoblox Remote REST API."
        )

    def _setup_credentials(self):
        self.credentials = self._configure_credentials(
            "credentials",
            "Infoblox credentials INI file",
            {
                "hostname": "Hostname for Infoblox REST API.",
                "username": "Username for Infoblox REST API.",
                "password": "Password for Infoblox REST API.",
                "view": "View to use for TXT entries "
                        "(leave blank is view is not necessary)"
            },
        )

    infoclient = None
    infotxts = []

    def _get_infoblox_client(self):
        if not self.infoclient:
            self.infoclient = {
                'connector': infoblox_client.connector.Connector({
                    'host': self.credentials.conf("hostname"),
                    'username': self.credentials.conf("username"),
                    'password': self.credentials.conf("password"),
                    'ssl_verify': True
                })
            }
            if self.credentials.conf("view"):
                self.infoclient['view'] = self.credentials.conf("view")

        return self.infoclient.copy()

    def _get_infoblox_record(self, validation_name, validation, create):
        record = self._get_infoblox_client()
        record['name'] = validation_name
        record['text'] = validation
        if create:
            record['ttl'] = self.ttl
            username = self.credentials.conf("username")
            record['comment'] = time.strftime(
                f'%Y-%m-%d %H:%M:%S: certbot-auto-{username}')

        return record

    def _perform(self, domain, validation_name, validation):
        txt = infoblox_client.objects.TXTRecord.create(
            **self._get_infoblox_record(validation_name, validation, True)
        )
        self.infotxts.append(txt)

    def _cleanup(self, domain, validation_name, validation):
        for txt in self.infotxts:
            if txt.name == validation_name and txt.text == validation:
                txt.delete()
                return

        txts = infoblox_client.objects.TXTRecord.search_all(
            **self._get_infoblox_record(validation_name, validation, False)
        )
        for txt in txts:
            # FIXME
            print(f'Please delete this txt record by yourself: {txt}')
