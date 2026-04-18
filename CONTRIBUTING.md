# Developer Guide

## Prerequisites

- Python 3.8 or later
- Git

## Setting up the development environment

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/svalgaard/certbot-dns-infoblox.git
cd certbot-dns-infoblox
python3 -m venv .venv
source .venv/bin/activate
```

Install the package in editable mode with test dependencies:

```bash
pip install -e ".[test]"
```

## Running tests

```bash
pytest
```

With verbose output:

```bash
pytest -v
```

With coverage report:

```bash
pip install pytest-cov
pytest --cov=certbot_dns_infoblox --cov-report=term-missing
```

## Project structure

```
certbot_dns_infoblox/
    __init__.py          # Package docstring and plugin documentation
    _infoblox.py         # Minimal Infoblox WAPI client using requests
    dns_infoblox.py      # Certbot DNS Authenticator plugin
tests/
    test_infoblox.py     # Unit tests for the WAPI client
    test_dns_infoblox.py # Unit tests for the Authenticator plugin
```

## Architecture

The plugin is split into two modules:

- **`_infoblox.py`** — A standalone HTTP client for the Infoblox WAPI (v2.10). Uses `requests.Session` with basic auth. Supports creating, searching, and deleting TXT records.
- **`dns_infoblox.py`** — The certbot `DNSAuthenticator` subclass that uses `InfobloxClient` to fulfil `dns-01` challenges.

## Building a release

Versioning is handled by `setuptools_scm` from git tags. To build a distribution:

```bash
pip install build
python -m build
```

## Configuration

See [infoblox.sample.ini](infoblox.sample.ini) for an example credentials file, and [README.md](README.md) for full usage instructions.
