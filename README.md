# certbot-dns-infoblox

Infoblox DNS Authenticator plugin for Certbot

This plugin automates the process of completing a ``dns-01`` challenge
by creating, and subsequently removing, TXT records using the Infoblox
Remote API.

In order to get a certificate from Let’s Encrypt, you have to
demonstrate control over the domain name. Usually, this is done using
HTTP where you upload a specific file to your website. Using DNS /
Infoblox as a backend, you are no longer required to run a webserver,
and can furthermore prove ownership of domain names only accessible
internally, and even of wildcard DNS names as, e.g., `*.example.com`.

Note that all certificates issued by Certificate Authorities as, e.g.,
Let's Encrypt are added to a distributed database called the
[certificate transparency logs](https://certificate.transparency.dev/)
(searchable at e.g. [crt.sh](https://crt.sh/)). In particular when
issuing internal certificates, you should be careful about revealing
names of internal servers, etc.


## Installation

**From PyPI (all platforms):**

```
pip install certbot-dns-infoblox
```

**Ubuntu `.deb` package:**

Pre-built `.deb` packages for Ubuntu 22.04 (Jammy) and 24.04 (Noble) are
attached to each [GitHub Release](https://github.com/svalgaard/certbot-dns-infoblox/releases).

```bash
# Download the .deb for your Ubuntu release from the Releases page, then
# run the following to install the .deb and all dependencies:
sudo apt install -f ./python3-certbot-dns-infoblox_*.deb
```

## Named Arguments

To start using DNS authentication for Infoblox, pass the following
arguments on certbot's command line:

| Argument | Description |
|---|---|
| `--authenticator dns-infoblox` | Select the authenticator plugin (Required) |
| `--dns-infoblox-credentials` | Path to Infoblox credentials INI file (Default: `/etc/letsencrypt/infoblox.ini`) |
| `--dns-infoblox-propagation-seconds` | Waiting time for DNS to propagate before asking the ACME server to verify the DNS record. (Default: 60) |


## Credentials

Create an INI file (default location `/etc/letsencrypt/infoblox.ini`):

```ini
#
# Infoblox credentials - keep this file private (chmod 600)
#
dns_infoblox_hostname = infoblox.example.net
dns_infoblox_username = my-wapi-user
dns_infoblox_password = 5f4dcc3b5aa765d61d8327deb882cf99

# Optional: Infoblox DNS view (omit this if not required)
# dns_infoblox_view = ""

# Optional: set to false to disable SSL verification (default: true).
# WARNING: disabling TLS verification exposes you to MITM attacks.
# dns_infoblox_ssl_verify = true

# Optional: path to a custom CA bundle (file or directory) for SSL
# verification.
# dns_infoblox_ca_bundle = "/path/to/ca-bundle.crt"
```

Restrict access to the file:

```
chmod 600 /etc/letsencrypt/infoblox.ini
```

The path to this file can be provided interactively or using the
`--dns-infoblox-credentials` command-line argument. Certbot records
the path to this file for use during renewal, but does not store the
file's contents.

**CAUTION:** Protect these credentials as you would any password.
Users who can read this file can issue arbitrary WAPI calls on your
behalf. Certbot will warn you with "Unsafe permissions on credentials
configuration file" if the file is readable by other users.


## SSL verification

By default the plugin verifies the Infoblox WAPI server's TLS
certificate against the system trust store. If your Infoblox uses a
certificate signed by an internal or private CA, point
`dns_infoblox_ca_bundle` at the CA bundle file or directory (PEM format):

```ini
dns_infoblox_ca_bundle = /etc/ssl/certs/my-internal-ca.pem
```

To disable certificate verification entirely (not recommended for
production), set `dns_infoblox_ssl_verify` to `false`:

```ini
# WARNING: disabling TLS verification exposes you to MITM attacks.
dns_infoblox_ssl_verify = false
```


## Examples

Acquire a certificate for `example.com` and `*.example.com`, waiting
10 seconds for DNS propagation:

```
certbot certonly \
  --authenticator dns-infoblox \
  --dns-infoblox-credentials /etc/letsencrypt/infoblox.ini \
  --dns-infoblox-propagation-seconds 10 \
  -d 'example.com' \
  -d '*.example.com'
```

Renew all certificates non-interactively (e.g. cron job or systemd
timer):

```
certbot renew --quiet
```


## Notes

This plugin communicates with the Infoblox WAPI REST API directly
using [`requests`](https://requests.readthedocs.io/), with no
dependency on the `infoblox-client` package.

Inspired by [certbot-dns-ispconfig](https://github.com/m42e/certbot-dns-ispconfig).


## Developing / Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for instructions on setting up a
development environment, running the test suite, building `.deb`
packages, and the CI/CD release workflow.
