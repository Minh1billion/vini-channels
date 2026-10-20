class ApplicationError(Exception):
    code = "application_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFound(ApplicationError):
    code = "not_found"


class Conflict(ApplicationError):
    code = "conflict"


class PermissionDenied(ApplicationError):
    code = "forbidden"


class AuthenticationFailed(ApplicationError):
    code = "unauthorized"


class AccountLocked(ApplicationError):
    code = "account_locked"

    def __init__(self, message: str, retry_after_sec: int) -> None:
        super().__init__(message)
        self.retry_after_sec = retry_after_sec


class DuplicateSyncRun(Conflict):
    code = "duplicate_sync_run"


class SecretUnreadable(Conflict):
    code = "secret_unreadable"


class ChannelUnverified(ApplicationError):
    code = "channel_unverified"
