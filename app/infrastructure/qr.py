from io import BytesIO

import qrcode
from qrcode.image.svg import SvgPathImage


class QrCodeGenerator:
    """Local QR generator matching the Node ``qrcode`` output parameters."""

    def png(self, payload: str) -> bytes:
        qr = qrcode.QRCode(border=2, box_size=10)
        qr.add_data(payload)
        qr.make(fit=True)
        image = qr.make_image(fill_color="black", back_color="white")
        pil_image = image.get_image() if hasattr(image, "get_image") else image
        pil_image = pil_image.convert("RGB").resize((400, 400))
        buffer = BytesIO()
        pil_image.save(buffer, format="PNG")
        return buffer.getvalue()

    def svg(self, payload: str) -> bytes:
        image = qrcode.make(payload, image_factory=SvgPathImage)
        buffer = BytesIO()
        image.save(buffer)
        return buffer.getvalue()
