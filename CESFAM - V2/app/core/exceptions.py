class AppError(Exception):
    """Excepción base de la aplicación."""


class NotFoundError(AppError):
    pass


class ProviderError(AppError):
    """Error al comunicarse con un proveedor externo (LLM, WhatsApp, etc.)."""
