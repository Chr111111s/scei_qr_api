class AppError(Exception):
    """Base error translated to the NestJS-style JSON error contract."""

    def __init__(self, status_code: int, message: str, error: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.error = error


class BadRequestError(AppError):
    def __init__(self, message: str = "Bad Request") -> None:
        super().__init__(400, message, "Bad Request")


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(401, message, "Unauthorized")


class ForbiddenError(AppError):
    def __init__(self, message: str = "No tiene permisos para realizar esta acción") -> None:
        super().__init__(403, message, "Forbidden")


class NotFoundError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(404, message, "Not Found")


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(409, message, "Conflict")


class PayloadTooLargeError(AppError):
    def __init__(self, message: str = "File too large") -> None:
        super().__init__(413, message, "Payload Too Large")
