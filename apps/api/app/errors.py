"""
Compatibility shim.

Some modules import StandardizedAIError from app.errors.
We re-export it from the canonical location to keep imports stable.
"""

# TODO: Update the import path below when StandardizedAIError is defined
# Example: from app.error_contract import StandardizedAIError

# Placeholder definition to restore test collection
class StandardizedAIError(Exception):
    def __init__(self, code, message, detail=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail

__all__ = ["StandardizedAIError"]
