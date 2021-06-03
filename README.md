certbot-dns-infoblox
====================

Infoblox DNS Authenticator plugin for Certbot

This plugin automates the process of completing a ``dns-01`` challenge by
creating, and subsequently removing, TXT records using the Infoblox Remote API.


Installation
------------
```
pip install certbot-dns-infoblox
```

Named Arguments
---------------

To start using DNS authentication for Infoblox, pass the following arguments on
certbot's command line:

| ``--authenticator certbot-dns-infoblox:dns-infoblox`` | Select the authenticator plugin (Required) |
| ``--certbot-dns-infoblox:dns-infoblox-credentials`` | Infoblox remote user credentials INI file. (Default: ``/etc/letsencrypt/infoblox.ini``) |
| ``--certbot-dns-infoblox:dns-infoblox-propagation-seconds`` | Waiting time for DNS to propagate before asking the ACME server to verify the DNS record. (Default: 10) |

If you are using certbot >= 1.0, you can skip the `certbot-dns-infoblox:`
in the above arguments.


Credentials
-----------
An example ``credentials.ini`` file:

    #
    # Sample Infoblox INI file
    #
    dns_infoblox_hostname="infoblox.example.net"
    dns_infoblox_username="my-wapi-user"
    dns_infoblox_password="5f4dcc3b5aa765d61d8327deb882cf99"
    dns_infoblox_view=""

The path to this file can be provided interactively or using the
``--dns-infoblox-credentials`` command-line argument. Certbot
records the path to this file for use during renewal, but does not store the
file's contents.

**CAUTION:** You should protect these API credentials as you would the
password to your infoblox account. Users who can read this file can use these
credentials to issue arbitrary API calls on your behalf. Users who can cause
Certbot to run using these credentials can complete a ``dns-01`` challenge to
acquire new certificates or revoke existing certificates for associated
domains, even if those domains aren't being managed by this server.

Certbot will emit a warning if it detects that the credentials file can be
accessed by other users on your system. The warning reads "Unsafe permissions
on credentials configuration file", followed by the path to the credentials
file. This warning will be emitted each time Certbot uses the credentials file,
including for renewal, and cannot be silenced except by addressing the issue
(e.g., by using a command like ``chmod 600`` to restrict access to the file).


Examples
--------
To acquire a single certificate for both ``example.com`` and
``*.example.com``, waiting 100 seconds for DNS propagation:

    certbot certonly \
    --authenticator dns-infoblox \
    --dns-infoblox-credentials /etc/letsencrypt/.secrets/domain.tld.ini \
    --dns-infoblox-propagation-seconds 100 \
    --agree-tos \
    --rsa-key-size 4096 \
    -d 'example.com' \
    -d '*.example.com'


Notes
-----

This is based on the work in [certbot-dns-ipsconfig](https://github.com/m42e/certbot-dns-ispconfig)
and the package [infoblox-client](https://github.com/infobloxopen/infoblox-client) python package.

Note that all your issued certificates can be found in public databases, e.g., [crt.sh](https://crt.sh/).
