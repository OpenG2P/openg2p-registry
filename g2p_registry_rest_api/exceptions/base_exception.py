from odoo.exceptions import UserError, ValidationError


class G2PApiException(UserError):
    def __init__(self, error_message="", error_code=None, error_description=None, **kwargs):
        self.error_message = error_message
        self.error_code = error_code
        self.error_description = error_description
        super().__init__(error_message, **kwargs)


class G2PApiValidationError(G2PApiException, ValidationError):
    def __init__(self, error_message="", error_code=None, error_description=None, **kwargs):
        super().__init__(
            error_message=error_message, error_code=error_code, error_description=error_description, **kwargs
        )
