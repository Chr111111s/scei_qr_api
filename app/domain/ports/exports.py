from typing import Protocol

from app.domain.entities import ReportData


class XlsxExporterPort(Protocol):
    def build(self, data: ReportData) -> bytes: ...


class PdfExporterPort(Protocol):
    def build(self, data: ReportData) -> bytes: ...
