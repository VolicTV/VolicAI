from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class ValorantPlayer:
    """Model representing a Valorant player"""
    puuid: str
    riot_id: str
    region: str
    last_updated: datetime = field(default_factory=datetime.utcnow)
    rank_data: Dict[str, Any] = field(default_factory=dict)
    match_history: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValorantPlayer':
        """Create player instance from dictionary data"""
        return cls(
            puuid=data.get('puuid', ''),
            riot_id=data.get('riot_id', ''),
            region=data.get('region', ''),
            last_updated=data.get('last_updated', datetime.utcnow()),
            rank_data=data.get('rank_data', {}),
            match_history=data.get('match_history', [])
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert player instance to dictionary"""
        return {
            'puuid': self.puuid,
            'riot_id': self.riot_id,
            'region': self.region,
            'last_updated': self.last_updated,
            'rank_data': self.rank_data,
            'match_history': self.match_history
        }

    def is_data_stale(self, max_age_seconds: int = 300) -> bool:
        """Check if player data needs updating"""
        if not self.last_updated:
            return True
        age = datetime.utcnow() - self.last_updated
        return age.total_seconds() > max_age_seconds

@dataclass
class ValorantMatch:
    """Model representing a Valorant match"""
    match_id: str
    game_start: datetime
    map_id: str
    game_mode: str
    players: List[Dict[str, Any]] = field(default_factory=list)
    teams: Dict[str, Any] = field(default_factory=dict)
    rounds: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValorantMatch':
        """Create match instance from dictionary data"""
        return cls(
            match_id=data.get('match_id', ''),
            game_start=datetime.fromisoformat(data.get('game_start', datetime.utcnow().isoformat())),
            map_id=data.get('map_id', ''),
            game_mode=data.get('game_mode', ''),
            players=data.get('players', []),
            teams=data.get('teams', {}),
            rounds=data.get('rounds', []),
            metadata=data.get('metadata', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert match instance to dictionary"""
        return {
            'match_id': self.match_id,
            'game_start': self.game_start.isoformat(),
            'map_id': self.map_id,
            'game_mode': self.game_mode,
            'players': self.players,
            'teams': self.teams,
            'rounds': self.rounds,
            'metadata': self.metadata
        }

    def get_player_stats(self, puuid: str) -> Optional[Dict[str, Any]]:
        """Get stats for a specific player in the match"""
        for player in self.players:
            if player.get('puuid') == puuid:
                return player
        return None

    def get_team_score(self, team_id: str) -> int:
        """Get score for a specific team"""
        return self.teams.get(team_id, {}).get('score', 0)

    def calculate_match_duration(self) -> int:
        """Calculate match duration in seconds"""
        if not self.rounds:
            return 0
        first_round = self.rounds[0].get('start_time', 0)
        last_round = self.rounds[-1].get('end_time', 0)
        return last_round - first_round

@dataclass
class ValorantStats:
    """Model representing player statistics"""
    puuid: str
    matches_played: int = 0
    wins: int = 0
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    headshots: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    rank_history: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def kda_ratio(self) -> float:
        """Calculate KDA ratio"""
        if self.deaths == 0:
            return float(self.kills + self.assists)
        return round((self.kills + self.assists) / self.deaths, 2)

    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage"""
        if self.matches_played == 0:
            return 0.0
        return round((self.wins / self.matches_played) * 100, 2)

    @property
    def headshot_percentage(self) -> float:
        """Calculate headshot percentage"""
        if self.kills == 0:
            return 0.0
        return round((self.headshots / self.kills) * 100, 2) 