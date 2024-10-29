from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
from .valorant_constants import RANKS, MAPS, AGENTS, GAME_MODES
from .valorant_exceptions import DataParsingError

class ValorantTransformer:
    """Handles data transformations and conversions for Valorant data"""

    @staticmethod
    def transform_match_data(raw_match: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw match data into a standardized format
        
        Args:
            raw_match: Raw match data from API
            
        Returns:
            Dict: Transformed match data
        """
        try:
            return {
                "match_id": raw_match.get("matchInfo", {}).get("matchId", ""),
                "game_start": datetime.fromtimestamp(
                    raw_match.get("matchInfo", {}).get("gameStartMillis", 0) / 1000,
                    tz=timezone.utc
                ),
                "map": raw_match.get("matchInfo", {}).get("mapId", ""),
                "mode": raw_match.get("matchInfo", {}).get("queueId", ""),
                "rounds_played": raw_match.get("matchInfo", {}).get("roundsPlayed", 0),
                "teams": ValorantTransformer._transform_teams(raw_match.get("teams", [])),
                "players": ValorantTransformer._transform_players(raw_match.get("players", [])),
                "rounds": ValorantTransformer._transform_rounds(raw_match.get("roundResults", [])),
                "metadata": {
                    "cluster": raw_match.get("matchInfo", {}).get("cluster", ""),
                    "game_version": raw_match.get("matchInfo", {}).get("gameVersion", ""),
                    "queue_id": raw_match.get("matchInfo", {}).get("queueId", ""),
                }
            }
        except Exception as e:
            raise DataParsingError(f"match data: {str(e)}")

    @staticmethod
    def transform_player_stats(raw_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw player stats into a standardized format
        
        Args:
            raw_stats: Raw stats data from API
            
        Returns:
            Dict: Transformed stats data
        """
        try:
            return {
                "rank": {
                    "current": raw_stats.get("current_data", {}).get("currenttierpatched", "Unranked"),
                    "rank_rating": raw_stats.get("current_data", {}).get("ranking_in_tier", 0),
                    "elo": raw_stats.get("current_data", {}).get("elo", 0),
                },
                "performance": {
                    "kills": raw_stats.get("stats", {}).get("kills", 0),
                    "deaths": raw_stats.get("stats", {}).get("deaths", 0),
                    "assists": raw_stats.get("stats", {}).get("assists", 0),
                    "score": raw_stats.get("stats", {}).get("score", 0),
                    "headshots": raw_stats.get("stats", {}).get("headshots", 0),
                    "bodyshots": raw_stats.get("stats", {}).get("bodyshots", 0),
                    "legshots": raw_stats.get("stats", {}).get("legshots", 0),
                },
                "matches": {
                    "total": raw_stats.get("matches", {}).get("total", 0),
                    "wins": raw_stats.get("matches", {}).get("wins", 0),
                    "losses": raw_stats.get("matches", {}).get("losses", 0),
                }
            }
        except Exception as e:
            raise DataParsingError(f"player stats: {str(e)}")

    @staticmethod
    def _transform_teams(raw_teams: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Transform team data"""
        teams = {}
        for team in raw_teams:
            team_id = team.get("teamId", "").lower()
            teams[team_id] = {
                "rounds_won": team.get("roundsWon", 0),
                "rounds_lost": team.get("roundsLost", 0),
                "has_won": team.get("won", False),
                "score": team.get("numPoints", 0)
            }
        return teams

    @staticmethod
    def _transform_players(raw_players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform player data"""
        return [{
            "puuid": player.get("subject", ""),
            "name": player.get("gameName", ""),
            "tag": player.get("tagLine", ""),
            "team": player.get("teamId", "").lower(),
            "character": player.get("characterId", ""),
            "stats": {
                "score": player.get("stats", {}).get("score", 0),
                "kills": player.get("stats", {}).get("kills", 0),
                "deaths": player.get("stats", {}).get("deaths", 0),
                "assists": player.get("stats", {}).get("assists", 0),
                "headshots": player.get("stats", {}).get("headshots", 0),
                "bodyshots": player.get("stats", {}).get("bodyshots", 0),
                "legshots": player.get("stats", {}).get("legshots", 0)
            },
            "economy": {
                "spent": player.get("economy", {}).get("spent", {}).get("overall", 0),
                "loadout_value": player.get("economy", {}).get("loadout_value", 0)
            }
        } for player in raw_players]

    @staticmethod
    def _transform_rounds(raw_rounds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform round data"""
        return [{
            "winning_team": round.get("winningTeam", "").lower(),
            "end_type": round.get("endType", ""),
            "bomb_planted": round.get("bombPlanted", False),
            "bomb_defused": round.get("bombDefused", False),
            "plant_events": ValorantTransformer._transform_plant_events(
                round.get("plantEvents", {})
            ),
            "defuse_events": ValorantTransformer._transform_defuse_events(
                round.get("defuseEvents", {})
            )
        } for round in raw_rounds]

    @staticmethod
    def _transform_plant_events(raw_events: Dict[str, Any]) -> Dict[str, Any]:
        """Transform plant events"""
        return {
            "plant_site": raw_events.get("site", ""),
            "planted_by": raw_events.get("plantedBy", {}).get("puuid", ""),
            "plant_time": raw_events.get("plantTimeMillis", 0)
        }

    @staticmethod
    def _transform_defuse_events(raw_events: Dict[str, Any]) -> Dict[str, Any]:
        """Transform defuse events"""
        return {
            "defused_by": raw_events.get("defusedBy", {}).get("puuid", ""),
            "defuse_time": raw_events.get("defuseTimeMillis", 0)
        } 