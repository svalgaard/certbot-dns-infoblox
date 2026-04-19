# Developer Guide

This document covers everything needed to work on **certbot-dns-infoblox**:
setting up a development environment, running the test suite, and building
Ubuntu-compatible `.deb` packages.

## Prerequisites

- Python 3.8 or later
- Git


## Project structure

```
certbot_dns_infoblox/
    __init__.py          # Package docstring and plugin documentation
    _infoblox.py         # Minimal Infoblox WAPI client using requests
    dns_infoblox.py      # Certbot DNS Authenticator plugin
tests/
    test_infoblox.py     # Unit tests for the WAPI client
    test_dns_infoblox.py # Unit tests for the Authenticator plugin
debian/                 # Debian/Ubuntu packaging files
```


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
python -m unittest discover -s tests -v
```
With coverage report:

```bash
pip install pytest-cov
pytest --cov=certbot_dns_infoblox --cov-report=term-missing
```

Tests use `unittest.mock` only — no live Infoblox instance is required.


## Testing against a live certbot

Install in editable mode to be able to edit the files without installing them.

```bash
pip install -e .
```

Verify the plugin is visible to certbot:

```bash
certbot plugins --configurator dns-infoblox
```

Do a dry-run against the Let's Encrypt staging CA:

```bash
certbot certonly --test-cert --dry-run \
    --authenticator dns-infoblox \
    --dns-infoblox-credentials /etc/letsencrypt/infoblox.ini \
    --dns-infoblox-propagation-seconds 100 \
    -d 'example.com'
```


## Building a `.deb` package

### Prerequisites (Ubuntu/Debian)

```bash
sudo apt-get install \
    debhelper dh-python devscripts \
    python3-all python3-setuptools python3-setuptools-scm \
    python3-certbot python3-requests python3-pytest \
    build-essential pybuild-plugin-pyproject
```

### Build

From the repository root:

```bash
dpkg-buildpackage -us -uc -b
```

The resulting `.deb` is placed one directory above the repo root (`../`).


## Building inside Docker (any distro)

To build for Ubuntu 24.04 (Noble) without affecting your host system:

```bash
docker run --rm -v "$PWD:/src" -w /src ubuntu:24.04 bash -c "
  apt-get update && apt-get install -y --no-install-recommends \
    debhelper dh-python devscripts \
    python3-all python3-setuptools python3-setuptools-scm \
    python3-certbot python3-requests python3-pytest \
    build-essential pybuild-plugin-pyproject && \
  dpkg-buildpackage -us -uc -b && \
  cp ../*.deb /src/
"
```

The resulting `.deb` is placed in the repo root (`../`).


## Building a release

Versioning is handled by `setuptools_scm` from git tags. To build a distribution:

```bash
pip install build
python -m build
```

## Configuration

See [infoblox.sample.ini](infoblox.sample.ini) for an example credentials file, and [README.md](README.md) for full usage instructions.
