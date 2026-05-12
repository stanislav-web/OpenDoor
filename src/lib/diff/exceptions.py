# -*- coding: utf-8 -*-

"""Differential report comparison exceptions."""


class DiffError(Exception):
    """Base differential scan error."""


class DiffValidationError(DiffError):
    """Raised when diff input reports are invalid or unsupported."""
