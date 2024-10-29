from typing import Optional, Dict, Any, Union, List
from datetime import datetime
import re
from .valorant_exceptions import (
    InvalidRiotIDError,
    InvalidRegionError,
    InvalidArgumentError
)
from .valorant_constants import RANKS, MAPS, AGENTS, GAME_MODES

class ValorantValidator:
    """Validates and sanitizes Valorant-related data"""

    @staticmethod
    def validate_riot_id(riot_id: str) -> bool:
        """
        Validate Riot ID format (name#tag)
        
        Args:
            riot_id: Riot ID to validate
            
        Returns:
            bool: True if valid, raises InvalidRiotIDError if not
        """
        if not riot_id or '#' not in riot_id:
            raise InvalidRiotIDError(riot_id)
            
        name, tag = riot_id.split('#')
        if not name or not tag or len(tag) > 5:
            raise InvalidRiotIDError(riot_id)
            
        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9\s]{1,16}#[a-zA-Z0-9]{3,5}$', riot_id):
            raise InvalidRiotIDError(riot_id)
            
        return True

    @staticmethod
    def validate_region(region: str) -> str:
        """
        Validate and normalize region code
        
        Args:
            region: Region code to validate
            
        Returns:
            str: Normalized region code
        """
        valid_regions = ['na', 'eu', 'ap', 'kr', 'latam', 'br']
        region = region.lower()
        
        if region not in valid_regions:
            raise InvalidRegionError(region)
            
        return region

    @staticmethod
    def sanitize_player_name(name: str) -> str:
        """
        Sanitize player name for display
        
        Args:
            name: Player name to sanitize
            
        Returns:
            str: Sanitized player name
        """
        # Remove excessive whitespace
        name = ' '.join(name.split())
        # Remove special characters
        name = re.sub(r'[^\w\s#]', '', name)
        return name.strip()

    @staticmethod
    def validate_match_data(match: Dict[str, Any]) -> bool:
        """
        Validate match data structure
        
        Args:
            match: Match data to validate
            
        Returns:
            bool: True if valid, raises InvalidArgumentError if not
        """
        required_fields = ['metadata', 'players', 'teams', 'rounds']
        
        for field in required_fields:
            if field not in match:
                raise InvalidArgumentError(f"Missing required field: {field}")
                
        if 'map' not in match['metadata'] or match['metadata']['map'] not in MAPS:
            raise InvalidArgumentError(f"Invalid map in match data")
            
        if 'mode' not in match['metadata'] or match['metadata']['mode'] not in GAME_MODES:
            raise InvalidArgumentError(f"Invalid game mode in match data")
            
        return True

    @staticmethod
    def validate_stats_data(stats: Dict[str, Any]) -> bool:
        """
        Validate player stats data structure
        
        Args:
            stats: Stats data to validate
            
        Returns:
            bool: True if valid, raises InvalidArgumentError if not
        """
        required_fields = ['performance', 'rank', 'matches_played']
        
        for field in required_fields:
            if field not in stats:
                raise InvalidArgumentError(f"Missing required field: {field}")
                
        return True

    @staticmethod
    def validate_rank(rank: str) -> bool:
        """
        Validate rank name
        
        Args:
            rank: Rank name to validate
            
        Returns:
            bool: True if valid, raises InvalidArgumentError if not
        """
        if rank not in RANKS:
            raise InvalidArgumentError(f"Invalid rank: {rank}", list(RANKS.keys()))
            
        return True

    @staticmethod
    def validate_agent(agent: str) -> bool:
        """
        Validate agent name
        
        Args:
            agent: Agent name to validate
            
        Returns:
            bool: True if valid, raises InvalidArgumentError if not
        """
        if agent not in AGENTS:
            raise InvalidArgumentError(f"Invalid agent: {agent}", list(AGENTS.keys()))
            
        return True

    @staticmethod
    def validate_match_count(count: int, min_count: int = 1, max_count: int = 10) -> bool:
        """
        Validate requested match count
        
        Args:
            count: Number of matches requested
            min_count: Minimum allowed matches
            max_count: Maximum allowed matches
            
        Returns:
            bool: True if valid, raises InvalidArgumentError if not
        """
        if not isinstance(count, int) or count < min_count or count > max_count:
            raise InvalidArgumentError(
                f"Match count must be between {min_count} and {max_count}"
            )
            
        return True 