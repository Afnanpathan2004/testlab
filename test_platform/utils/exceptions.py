"""Custom exception hierarchy for the application."""


class ApplicationException(Exception):
    """Base class for application-level exceptions."""


class AuthenticationError(ApplicationException):
    """Raised when authentication or authorization fails."""


class ValidationError(ApplicationException):
    """Raised when input validation fails."""


class DatabaseError(ApplicationException):
    """Raised for database operation errors."""


class RateLimitError(ApplicationException):
    """Raised when rate limits are exceeded."""
