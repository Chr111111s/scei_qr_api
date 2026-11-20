from typing import Protocol

from app.domain.entities import Equipment, ReportData


class XlsxExporterPort(Protocol):
    def build(self, data: ReportData) -> bytes: ...


class PdfExporterPort(Protocol):
    def build(self, data: ReportData) -> bytes: ...


class QrLabelExporterPort(Protocol):
    def single_label(self, equipment: Equipment) -> bytes: ...

    def labels_sheet(self, equipos: list[Equipment]) -> bytes: ...
