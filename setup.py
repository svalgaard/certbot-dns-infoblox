
from setuptools import find_packages, setup

install_requires = [
    "acme>=0.29.0",
    "certbot>=0.34.0",
    'infoblox-client>=0.5.0',
    "setuptools",
]

# read the contents of the README file
with open("README.md") as f:
    long_description = f.read()

docs_extras = [
]

setup(
    name="certbot-dns-infoblox",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],

    description="Infoblox DNS Authenticator plugin for Certbot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/svalgaard/certbot-dns-infoblox",
    author="Jens Svalgaard Kohrt",
    author_email="github@svalgaard.net",
    license="Apache License 2.0",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Plugins",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],

    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    entry_points={
        "certbot.plugins": [
            "dns-infoblox = certbot_dns_infoblox.dns_infoblox:Authenticator",
        ]
    },
)
