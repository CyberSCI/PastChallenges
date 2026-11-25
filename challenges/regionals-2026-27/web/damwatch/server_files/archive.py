import posixpath
from dataclasses import dataclass


class ReportNotFound(Exception):
    pass


class InvalidReportPath(Exception):
    pass


@dataclass(frozen=True)
class ReportMeta:
    path: str
    title: str


@dataclass(frozen=True)
class Report:
    path: str
    title: str
    body: str


class Archive:
    def __init__(self, flag_2: str):
        self._reports = {
            "public/status.txt": Report(
                "public/status.txt",
                "Shift status",
                "Public gauge: 59 cm. Baseline: 100 cm. The dashboard still marks the reservoir NORMAL.",
            ),
            "public/spillway-test.txt": Report(
                "public/spillway-test.txt",
                "Spillway test",
                "Routine gate cycling is complete. The report archive opens records by their public path.",
            ),
            "internal/coolant-diversion.memo": Report(
                "internal/coolant-diversion.memo",
                "Cooling Annex diversion",
                "The Cooling Annex diversion draws from the nursery pool. "
                "The manual lock closes the intake. Slots A and B need receipts, "
                "but each emergency ticket issues one receipt. Regular approval is unavailable.\n"
                f"Inspector's evidence mark: {flag_2}\n"
                "The public warning remains held by maintenance automation.",
            ),
        }

    def list_public(self) -> list[ReportMeta]:
        return [
            ReportMeta(report.path, report.title)
            for path, report in self._reports.items()
            if path.startswith("public/")
        ]

    def read(self, raw_path: str) -> Report:
        if (
            len(raw_path) > 256
            or "\\" in raw_path
            or "\x00" in raw_path
            or "%" in raw_path
        ):
            raise InvalidReportPath
        # Deliberate flaw: the prefix check happens before logical normalization.
        if not raw_path.startswith("public/"):
            raise ReportNotFound
        normalized = posixpath.normpath(raw_path)
        try:
            return self._reports[normalized]
        except KeyError as error:
            raise ReportNotFound from error
