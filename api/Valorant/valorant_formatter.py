from typing import Dict, List, Any, Optional
from datetime import datetime
from .valorant_constants import RANKS, MAPS, AGENTS, GAME_MODES

class ResponseFormatter:
    """Formats Valorant data into readable chat messages"""

    @staticmethod
    def format_stats(riot_id: str, stats: Dict[str, Any]) -> str:
        """Format player stats into a readable message"""
        try:
            rank_data = stats.get("rank", {})
            current_rank = rank_data.get("current", "Unranked")
            rank_rating = rank_data.get("rank_rating", 0)
            
            performance = stats.get("performance", {})
            kda = (
                f"K/D/A: {performance.get('kills', 0)}/"
                f"{performance.get('deaths', 0)}/"
                f"{performance.get('assists', 0)}"
            )
            
            hs_percentage = ResponseFormatter._calculate_headshot_percentage(performance)
            
            matches = stats.get("matches", {})
            win_rate = ResponseFormatter._calculate_win_rate(
                matches.get("wins", 0),
                matches.get("total", 0)
            )

            return (
                f"{riot_id} Stats 📊 | "
                f"Rank: {RANKS.get(current_rank, '❓')} {current_rank} ({rank_rating}RR) | "
                f"{kda} | "
                f"HS: {hs_percentage}% | "
                f"WR: {win_rate}% ({matches.get('wins', 0)}W/{matches.get('losses', 0)}L)"
            )
        except Exception as e:
            command_logger.error(f"Error formatting stats: {str(e)}")
            return f"Error formatting stats for {riot_id}"

    @staticmethod
    def format_match_history(
        username: str,
        riot_id: str,
        matches: List[Dict[str, Any]],
        num_matches: int
    ) -> str:
        """Format match history into a readable message"""
        try:
            if not matches:
                return f"No recent matches found for {riot_id}"

            response = f"Last {len(matches)} matches for {riot_id}:\n"
            
            for match in matches:
                map_name = match.get("map", "Unknown Map")
                mode = match.get("mode", "Unknown Mode")
                
                # Find player's performance in match
                player_data = None
                for player in match.get("players", []):
                    if player.get("name", "").lower() in riot_id.lower():
                        player_data = player
                        break

                if not player_data:
                    continue

                # Get match stats
                stats = player_data.get("stats", {})
                kda = f"{stats.get('kills', 0)}/{stats.get('deaths', 0)}/{stats.get('assists', 0)}"
                agent = player_data.get("character", "Unknown")
                score = stats.get("score", 0)
                
                # Get match result
                team = player_data.get("team", "").lower()
                teams = match.get("teams", {})
                won = teams.get(team, {}).get("has_won", False)
                result = "✅ Won" if won else "❌ Lost"
                
                response += (
                    f"\n{MAPS.get(map_name, '🗺️')} {map_name} ({mode}): "
                    f"{result} | "
                    f"{AGENTS.get(agent, '👤')} {agent} | "
                    f"KDA: {kda} | "
                    f"Score: {score}"
                )

            return response
            
        except Exception as e:
            command_logger.error(f"Error formatting match history: {str(e)}")
            return f"Error formatting match history for {riot_id}"

    @staticmethod
    def format_match_details(riot_id: str, match: Dict[str, Any]) -> str:
        """Format detailed match information"""
        try:
            map_name = match.get("map", "Unknown Map")
            mode = match.get("mode", "Unknown Mode")
            
            # Find player's data
            player_data = None
            for player in match.get("players", []):
                if player.get("name", "").lower() in riot_id.lower():
                    player_data = player
                    break

            if not player_data:
                return f"Could not find player data for {riot_id} in match"

            # Get detailed stats
            stats = player_data.get("stats", {})
            kda = f"{stats.get('kills', 0)}/{stats.get('deaths', 0)}/{stats.get('assists', 0)}"
            agent = player_data.get("character", "Unknown")
            score = stats.get("score", 0)
            
            # Calculate additional stats
            hs_percentage = ResponseFormatter._calculate_headshot_percentage(stats)
            econ = player_data.get("economy", {})
            avg_spend = econ.get("spent", 0) / max(match.get("rounds_played", 1), 1)
            
            # Get match result
            team = player_data.get("team", "").lower()
            teams = match.get("teams", {})
            team_data = teams.get(team, {})
            won = team_data.get("has_won", False)
            score_line = f"{team_data.get('rounds_won', 0)}-{team_data.get('rounds_lost', 0)}"
            
            return (
                f"Match Details on {MAPS.get(map_name, '🗺️')} {map_name} "
                f"({GAME_MODES.get(mode, mode)})\n"
                f"Result: {'✅ Won' if won else '❌ Lost'} {score_line} | "
                f"{AGENTS.get(agent, '👤')} {agent} | "
                f"KDA: {kda} | "
                f"HS: {hs_percentage}% | "
                f"Score: {score} | "
                f"Avg Spend: {avg_spend:,.0f}"
            )
            
        except Exception as e:
            command_logger.error(f"Error formatting match details: {str(e)}")
            return f"Error formatting match details for {riot_id}"

    @staticmethod
    def format_coaching_tips(stats: Dict[str, Any], matches: List[Dict[str, Any]]) -> str:
        """Format coaching tips based on player performance"""
        try:
            tips = []
            
            # Analyze aim
            performance = stats.get("performance", {})
            hs_percentage = ResponseFormatter._calculate_headshot_percentage(performance)
            if hs_percentage < 15:
                tips.append("🎯 Work on crosshair placement for better headshots")
            
            # Analyze economy
            total_spend = 0
            total_rounds = 0
            for match in matches:
                player_data = next(
                    (p for p in match.get("players", []) 
                     if p.get("name", "").lower() in stats.get("name", "").lower()),
                    None
                )
                if player_data:
                    total_spend += player_data.get("economy", {}).get("spent", 0)
                    total_rounds += match.get("rounds_played", 0)
            
            avg_spend = total_spend / max(total_rounds, 1)
            if avg_spend > 4000:
                tips.append("💰 Consider being more economic with purchases")
            
            # Analyze KDA
            kda_ratio = (
                (performance.get("kills", 0) + performance.get("assists", 0)) /
                max(performance.get("deaths", 1), 1)
            )
            if kda_ratio < 1.0:
                tips.append("⚔️ Focus on staying alive and trading kills")
            
            # Add general tips if needed
            if not tips:
                tips.append("👍 Keep up the good work! Try reviewing your gameplay recordings")
            
            return "Coaching Tips:\n" + "\n".join(tips)
            
        except Exception as e:
            command_logger.error(f"Error formatting coaching tips: {str(e)}")
            return "Error generating coaching tips"

    @staticmethod
    def _calculate_headshot_percentage(stats: Dict[str, Any]) -> float:
        """Calculate headshot percentage from stats"""
        total_hits = (
            stats.get("headshots", 0) +
            stats.get("bodyshots", 0) +
            stats.get("legshots", 0)
        )
        if total_hits == 0:
            return 0.0
        return round((stats.get("headshots", 0) / total_hits) * 100, 1)

    @staticmethod
    def _calculate_win_rate(wins: int, total: int) -> float:
        """Calculate win rate percentage"""
        if total == 0:
            return 0.0
        return round((wins / total) * 100, 1) 