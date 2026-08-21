"""Qualification framework exceptions."""


class QualificationError(Exception):
    pass


class QualificationSkip(
    QualificationError
):
    """Raised when a check cannot be executed."""
