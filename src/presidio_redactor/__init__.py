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

__version__ = "0.2.1"

__all__ = ["__version__"]
