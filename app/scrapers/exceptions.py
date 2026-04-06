class TransfermarktError(Exception):
    """Base class for Transfermarkt integration errors."""


class TransfermarktRequestError(TransfermarktError):
    """Raised when HTTP transport fails after retries."""


class TransfermarktResponseError(TransfermarktError):
    """Raised when server response is not usable."""


class TransfermarktParseError(TransfermarktError):
    """Raised when HTML parsing fails unexpectedly."""
