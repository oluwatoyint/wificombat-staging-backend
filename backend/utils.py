# core/utils.py
from decimal import Decimal
from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    ValidationError,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
)


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, ValidationError):
            # Collect all error messages into a list
            error_messages = []
            for field, errors in exc.detail.items():
                for error in errors:
                    if field == "non_field_errors":
                        error_messages.append(f"{error}")
                    else:
                        error_messages.append(
                            f"Error with {field.replace('_', ' ')}: {error}"
                        )

            # Create a single human-readable string
            human_readable_error = " \n".join(error_messages)

            # Construct the response
            response.data = {
                "success": False,
                "message": human_readable_error,
                "data": None,
            }

        elif isinstance(exc, AuthenticationFailed) or isinstance(exc, NotAuthenticated):
            response.data = {
                "success": False,
                "message": "Authentication credentials were not provided or are invalid.",
                "data": None,
            }

        elif isinstance(exc, PermissionDenied):
            response.data = {
                "success": False,
                "message": "You do not have permission to perform this action.",
                "data": None,
            }

        # Additional error types can be handled here as needed

    return response