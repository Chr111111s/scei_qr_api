from datetime import UTC, datetime
from typing import Any, Literal

from app.domain.entities import ReportData
from app.domain.ports.exports import PdfExporterPort, XlsxExporterPort
from app.domain.ports.repositories import ReportRepository


class ReportesService:
    def __init__(
        self,
        reports: ReportRepository,
        xlsx_exporter: XlsxExporterPort,
        pdf_exporter: PdfExporterPort,
    ) -> None:
        self.reports = reports
        self.xlsx_exporter = xlsx_exporter
        self.pdf_exporter = pdf_exporter

    async def get_estadisticas(self) -> dict[str, Any]:
        return await self.reports.get_estadisticas()

    async def exportar(self, formato: Literal["xlsx", "pdf"]) -> tuple[bytes, str, str]:
        data = ReportData(
            equipos=await self.reports.get_equipment_usage_counts(),
            usos=await self.reports.list_usages_for_export(),
            incidencias=await self.reports.list_incidents_for_export(),
        )
        fecha = datetime.now(UTC).date().isoformat()
        if formato == "pdf":
            buffer = self.pdf_exporter.build(data)
            return buffer, f"reporte-scei-qr-{fecha}.pdf", "application/pdf"
        buffer = self.xlsx_exporter.build(data)
        return (
            buffer,
            f"reporte-scei-qr-{fecha}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
