"""
Custom Presidio recognizers for presidio_redactor.
"""

from __future__ import annotations

from presidio_redactor.recognizers.devops import (
    AssignmentValueRecognizer,
    BearerValueRecognizer,
    get_devops_recognizers,
    register_devops_recognizers,
)

__all__ = [
    "AssignmentValueRecognizer",
    "BearerValueRecognizer",
    "get_devops_recognizers",
    "register_devops_recognizers",
]
