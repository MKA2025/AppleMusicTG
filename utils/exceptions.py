class BotException(Exception):
    """Base exception for bot errors"""
    pass

class ConfigError(BotException):
    """Configuration related errors"""
    pass

class DownloadError(BotException):
    """Download related errors"""
    pass

class AuthorizationError(BotException):
    """Authorization related errors"""
    pass

class RegionError(BotException):
    """Region related errors"""
    pass

class AppleMusicAPIError(BotException):
    """Apple Music API related errors"""
    pass

class RateLimitError(BotException):
    """Rate limit related errors"""
    pass
