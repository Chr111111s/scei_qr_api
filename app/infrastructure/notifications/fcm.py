import base64
import json
import logging
from typing import Any

from anyio import to_thread

from app.core.config import Settings

logger = logging.getLogger(__name__)


class FcmNotifier:
    """Degraded-mode FCM notifier: registration works without credentials.

    Push delivery is only enabled when ``FIREBASE_SERVICE_ACCOUNT`` (base64 JSON)
    is configured and the optional ``firebase-admin`` dependency is installed.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.enabled = False
        self._messaging: Any = None

    def initialize(self) -> None:
        if not self.settings.firebase_service_account:
            logger.warning(
                "FIREBASE_SERVICE_ACCOUNT no configurado: notificaciones push deshabilitadas."
            )
            return
        try:
            import firebase_admin
            from firebase_admin import credentials, messaging

            service_account = json.loads(
                base64.b64decode(self.settings.firebase_service_account).decode("utf-8")
            )
            if not firebase_admin._apps:
                firebase_admin.initialize_app(credentials.Cert(service_account))
            self._messaging = messaging
            self.enabled = True
            logger.info("Firebase Admin inicializado: push habilitado.")
        except Exception:
            logger.exception("Error inicializando Firebase Admin")

    async def send_incident_update(
        self,
        *,
        incident_id: int,
        message: str,
        tokens: list[str],
    ) -> None:
        if not self.enabled or not tokens:
            return

        def _send() -> None:
            self._messaging.send_each_for_multicast(
                messaging_multicast_message(tokens, message, incident_id)
            )

        try:
            await to_thread.run_sync(_send)
        except Exception:
            logger.exception("Error enviando push")


def messaging_multicast_message(tokens: list[str], message: str, incident_id: int) -> Any:
    from firebase_admin import messaging

    return messaging.MulticastMessage(
        tokens=tokens,
        notification=messaging.Notification(title="scei_qr", body=message),
        data={"incidenciaId": str(incident_id)},
    )
