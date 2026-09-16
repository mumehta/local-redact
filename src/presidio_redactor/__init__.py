"""
presidio_redactor
=================

Local redaction toolkit for removing PII and DevOps secrets from text files
and images, built on Microsoft Presidio.

Public API:

    from presidio_redactor.recognizers import (
        get_devops_recognizers,
        register_devops_recognizers,
    )
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    # Single source of truth: the version declared in pyproject.toml, read
    # from the installed distribution metadata.
    __version__ = version("local-redactor")
except PackageNotFoundError:  # pragma: no cover - only when running uninstalled
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
