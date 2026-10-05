class ApiError(Exception):
    """Error de negocio/validación que se convierte en una respuesta JSON {"detail": ...}."""

    def __init__(self, status_code: int, detail):
        super().__init__(str(detail))
        self.status_code = status_code
        self.detail = detail
