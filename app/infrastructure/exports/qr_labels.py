"""Etiquetas imprimibles de equipos (HU-AD-07).

Cada etiqueta contiene el QR escaneable y el identificador legible del equipo.
La hoja por lote usa una cuadrícula de etiquetas de 63.5 x 38.1 mm (Avery 5160)
sobre una página A4, con un QR de 28 mm: suficiente para escanear desde un
teléfono sin dificultad.
"""

from io import BytesIO

import qrcode
from qrcode.constants import ERROR_CORRECT_M
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.domain.entities import Equipment
from app.domain.ports.exports import QrLabelExporterPort

_LABEL_WIDTH = 63.5 * mm
_LABEL_HEIGHT = 38.1 * mm
_COLUMNS = 3
_ROWS = 7
_PAGE_MARGIN_X = (A4[0] - (_COLUMNS * _LABEL_WIDTH)) / 2
_PAGE_MARGIN_Y = 8 * mm


class QrLabelExporter(QrLabelExporterPort):
    def single_label(self, equipment: Equipment) -> bytes:
        page_width, page_height = 70 * mm, 50 * mm
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=(page_width, page_height))
        pdf.setTitle(f"Etiqueta QR {equipment.codigo}")

        qr_size = 34 * mm
        qr_x = 5 * mm
        qr_y = (page_height - qr_size) / 2
        self._draw_qr(pdf, equipment.qr_token, qr_x, qr_y, qr_size)

        self._draw_text(
            pdf,
            equipment,
            x=qr_x + qr_size + 4 * mm,
            top=page_height - 10 * mm,
            width=page_width - (qr_x + qr_size + 4 * mm) - 5 * mm,
            code_size=9,
            body_size=6.5,
        )
        pdf.showPage()
        pdf.save()
        return buffer.getvalue()

    def labels_sheet(self, equipos: list[Equipment]) -> bytes:
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        pdf.setTitle("Etiquetas QR de equipos")

        per_page = _COLUMNS * _ROWS
        for index, equipment in enumerate(equipos):
            position = index % per_page
            if position == 0 and index > 0:
                pdf.showPage()
                pdf.setTitle("Etiquetas QR de equipos")

            column = position % _COLUMNS
            row = position // _COLUMNS
            x = _PAGE_MARGIN_X + column * _LABEL_WIDTH
            y = A4[1] - _PAGE_MARGIN_Y - (row + 1) * _LABEL_HEIGHT

            self._draw_batch_label(pdf, equipment, x, y)

        if not equipos:
            pdf.setFont("Helvetica", 11)
            pdf.drawString(_PAGE_MARGIN_X, A4[1] - 20 * mm, "No hay equipos para imprimir.")

        pdf.showPage()
        pdf.save()
        return buffer.getvalue()

    def _draw_batch_label(
        self, pdf: canvas.Canvas, equipment: Equipment, x: float, y: float
    ) -> None:
        padding = 3 * mm
        qr_size = 28 * mm
        qr_x = x + padding
        qr_y = y + (_LABEL_HEIGHT - qr_size) / 2
        self._draw_qr(pdf, equipment.qr_token, qr_x, qr_y, qr_size)

        text_x = qr_x + qr_size + 3 * mm
        text_width = x + _LABEL_WIDTH - padding - text_x
        self._draw_text(
            pdf,
            equipment,
            x=text_x,
            top=y + _LABEL_HEIGHT - 6 * mm,
            width=text_width,
            code_size=8,
            body_size=5.5,
        )

        # Guía tenue de corte; no se imprime encima del contenido.
        pdf.setStrokeColorRGB(0.85, 0.85, 0.85)
        pdf.setDash(1, 2)
        pdf.rect(x + 0.5, y + 0.5, _LABEL_WIDTH - 1, _LABEL_HEIGHT - 1)
        pdf.setDash()

    def _draw_qr(self, pdf: canvas.Canvas, payload: str, x: float, y: float, size: float) -> None:
        qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=12, border=1)
        qr.add_data(payload)
        qr.make(fit=True)
        image = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        pdf.drawImage(
            ImageReader(buffer),
            x,
            y,
            width=size,
            height=size,
            preserveAspectRatio=True,
            mask="auto",
        )

    def _draw_text(
        self,
        pdf: canvas.Canvas,
        equipment: Equipment,
        *,
        x: float,
        top: float,
        width: float,
        code_size: float,
        body_size: float,
    ) -> None:
        y = top
        y = self._wrap_text(
            pdf,
            equipment.codigo,
            x=x,
            y=y,
            width=width,
            font="Helvetica-Bold",
            size=code_size,
            max_lines=2,
        )
        y -= 1.5 * mm

        if equipment.nombre and equipment.nombre.strip() != equipment.codigo:
            y = self._wrap_text(
                pdf,
                equipment.nombre,
                x=x,
                y=y,
                width=width,
                font="Helvetica",
                size=body_size,
                max_lines=3,
            )
            y -= 1 * mm

        if equipment.laboratorio:
            y = self._wrap_text(
                pdf,
                equipment.laboratorio,
                x=x,
                y=y,
                width=width,
                font="Helvetica",
                size=body_size,
                max_lines=2,
            )
            y -= 0.5 * mm

        self._wrap_text(
            pdf,
            equipment.ubicacion,
            x=x,
            y=y,
            width=width,
            font="Helvetica-Oblique",
            size=body_size,
            max_lines=2,
        )

    def _wrap_text(
        self,
        pdf: canvas.Canvas,
        text: str,
        *,
        x: float,
        y: float,
        width: float,
        font: str,
        size: float,
        max_lines: int,
    ) -> float:
        leading = size * 1.2
        pdf.setFont(font, size)
        words = text.split()
        lines: list[str] = []
        current = ""

        for word in words:
            candidate = f"{current} {word}".strip()
            if pdf.stringWidth(candidate, font, size) <= width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word

        if current:
            lines.append(current)

        for line in lines[:max_lines]:
            pdf.drawString(x, y, line)
            y -= leading
        return y
