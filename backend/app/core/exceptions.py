"""Custom exceptions for the application"""


class ApplicationError(Exception):
    """Base application exception"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(ApplicationError):
    """Validation error (400)"""
    def __init__(self, message: str):
        super().__init__(message, 400)


class MongoDBConnectionError(ApplicationError):
    """MongoDB connection error (400)"""
    def __init__(self, message: str):
        super().__init__(message, 400)


class MongoDBOperationError(ApplicationError):
    """MongoDB operation error (500)"""
    def __init__(self, message: str):
        super().__init__(message, 500)


class EmptyCollectionError(ApplicationError):
    """No documents found (404)"""
    def __init__(self, db: str, collection: str):
        message = f"No documents found in collection '{collection}' of database '{db}'."
        super().__init__(message, 404)


class CloudUploadError(ApplicationError):
    """Cloud upload error (500)"""
    def __init__(self, provider: str, message: str):
        super().__init__(f"Cloud upload error ({provider}): {message}", 500)


class SchedulerError(ApplicationError):
    """Scheduler error (500)"""
    def __init__(self, message: str):
        super().__init__(message, 500)


class CSVGenerationError(ApplicationError):
    """CSV generation error (500)"""
    def __init__(self, message: str):
        super().__init__(message, 500)
