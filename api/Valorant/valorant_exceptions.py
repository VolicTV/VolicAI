"""Custom exceptions for the Valorant integration"""

class ValorantError(Exception):
    """Base exception for Valorant-related errors"""
    pass

class APIError(ValorantError):
    """Raised when there's an error with the Riot API"""
    def __init__(self, message: str = "Error accessing Riot API", status_code: int = None):
        self.status_code = status_code
        self.message = f"{message} (Status: {status_code})" if status_code else message
        super().__init__(self.message)

class RateLimitError(APIError):
    """Raised when API rate limit is exceeded"""
    def __init__(self):
        super().__init__("Rate limit exceeded. Please try again later", 429)

class InvalidRiotIDError(ValorantError):
    """Raised when Riot ID format is invalid"""
    def __init__(self, riot_id: str):
        self.riot_id = riot_id
        super().__init__(f"Invalid Riot ID format: {riot_id}. Must be name#tag")

class PlayerNotFoundError(ValorantError):
    """Raised when player is not found"""
    def __init__(self, riot_id: str):
        self.riot_id = riot_id
        super().__init__(f"Could not find player: {riot_id}")

class CacheError(ValorantError):
    """Raised when there's an error with the cache"""
    def __init__(self, operation: str):
        self.operation = operation
        super().__init__(f"Cache error during {operation}")

class DataParsingError(ValorantError):
    """Raised when there's an error parsing API response data"""
    def __init__(self, data_type: str):
        self.data_type = data_type
        super().__init__(f"Error parsing {data_type} data")

class NoMatchesFoundError(ValorantError):
    """Raised when no matches are found for a player"""
    def __init__(self, riot_id: str):
        self.riot_id = riot_id
        super().__init__(f"No matches found for player: {riot_id}")

class NoStatsFoundError(ValorantError):
    """Raised when no stats are found for a player"""
    def __init__(self, riot_id: str):
        self.riot_id = riot_id
        super().__init__(f"No stats found for player: {riot_id}")

class InvalidRegionError(ValorantError):
    """Raised when an invalid region is provided"""
    def __init__(self, region: str):
        self.region = region
        super().__init__(f"Invalid region: {region}")

class CommandCooldownError(ValorantError):
    """Raised when a command is on cooldown"""
    def __init__(self, command: str, remaining_seconds: int):
        self.command = command
        self.remaining_seconds = remaining_seconds
        super().__init__(
            f"Command {command} is on cooldown. Try again in {remaining_seconds} seconds"
        )

class InvalidArgumentError(ValorantError):
    """Raised when invalid arguments are provided to a command"""
    def __init__(self, argument: str, valid_values: list = None):
        self.argument = argument
        self.valid_values = valid_values
        message = f"Invalid argument: {argument}"
        if valid_values:
            message += f". Valid values are: {', '.join(str(v) for v in valid_values)}"
        super().__init__(message)

class AuthenticationError(ValorantError):
    """Raised when there's an authentication error with the Riot API"""
    def __init__(self):
        super().__init__("Authentication failed. Please check your API key")

class NetworkError(ValorantError):
    """Raised when there's a network-related error"""
    def __init__(self, details: str = None):
        message = "Network error occurred"
        if details:
            message += f": {details}"
        super().__init__(message)

class TimeoutError(ValorantError):
    """Raised when an operation times out"""
    def __init__(self, operation: str):
        super().__init__(f"Operation timed out: {operation}")

class MaintenanceError(ValorantError):
    """Raised when the Riot API is under maintenance"""
    def __init__(self):
        super().__init__("Riot API is currently under maintenance")
