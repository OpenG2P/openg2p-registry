from odoo.exceptions import UserError, ValidationError


class G2PReSTException(UserError):
    def __init__(
        self, error_message, error_code=None, error_description=None, **kwargs
    ):
        self.error_message = error_message
        self.error_code = error_code
        self.error_description = error_description
        super().__init__(error_message, **kwargs)


class G2PReSTValidationError(G2PReSTException, ValidationError):
    def __init__(
        self, error_message, error_code=None, error_description=None, **kwargs
    ):
        super(ValidationError, self).__init__(error_message, **kwargs)
        super().__init__(error_message, error_code, error_description, **kwargs)
