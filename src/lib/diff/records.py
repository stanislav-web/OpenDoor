# -*- coding: utf-8 -*-

"""Normalized report records for differential scan."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DiffReportFinding:
    """Normalized finding extracted from an OpenDoor report."""

    bucket: str
    url: str
    status: str
    size: str
    method: str = ''
    location: str = ''

    @property
    def identity(self):
        """Return stable endpoint identity used by the diff engine."""

        return (self.method, self.url)

    @property
    def comparable(self):
        """Return fields that can produce a changed finding."""

        return {
            'bucket': self.bucket,
            'status': self.status,
            'size': self.size,
            'location': self.location,
        }


@dataclass(frozen=True)
class DiffReport:
    """Normalized report ready for comparison."""

    path: str
    format: str
    target: str
    findings: tuple[DiffReportFinding, ...]
