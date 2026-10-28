from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.domain.entities import ReportData
from app.domain.ports.exports import PdfExporterPort


class PdfExporter(PdfExporterPort):
    def build(self, data: ReportData) -> bytes:
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=12 * mm,
            rightMargin=12 * mm,
            topMargin=12 * mm,
            bottomMargin=12 * mm,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            fontSize=16,
            leading=20,
            spaceAfter=4,
            alignment=0,
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#666666"),
            spaceAfter=10,
        )

        rows = [["Código", "Nombre", "Ubicación", "Activo", "Usos", "Incidencias"]]
        for item in data.equipos:
            equipo = item.equipment
            rows.append(
                [
                    equipo.codigo,
                    equipo.nombre,
                    equipo.ubicacion,
                    "Sí" if equipo.activo else "No",
                    str(item.usos),
                    str(item.incidencias),
                ]
            )

        table = Table(
            rows,
            colWidths=[70, 200, 200, 50, 50, 70],
            repeatRows=1,
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F54EB")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#F4F6FB")],
                    ),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        generated = datetime.now().strftime("%d/%m/%Y %H:%M")
        story = [
            Paragraph("Reporte General - scei_qr", title_style),
            Paragraph(f"Generado: {generated}", subtitle_style),
            table,
            Spacer(1, 10),
            Paragraph(
                f"Totales: {len(data.equipos)} equipos · "
                f"{len(data.usos)} usos · {len(data.incidencias)} incidencias",
                styles["Normal"],
            ),
        ]
        document.build(story)
        return buffer.getvalue()
