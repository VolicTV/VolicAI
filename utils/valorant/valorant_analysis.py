from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict
import logging
from datetime import datetime, timedelta
from utils.logger import command_logger

class MatchAnalyzer:
    """Analyzes Valorant match data for insights and patterns"""

    @staticmethod
    def analyze_matches(stats: Dict, matches: List[Dict]) -> Optional[Dict]:
        """
        Analyze a set of Valorant matches for a player
        
        Args:
            stats: Player's overall statistics
            matches: List of match data to analyze
            
        Returns:
            Dict containing analysis results or None on error
        """
        try:
            analysis = {
                "total_matches": len(matches),
                "modes": [],
                "agents": [],
                "maps": [],
                "avg_kda": [0, 0, 0],
                "avg_score": 0,
                "win_rate": 0,
                "headshot_percentage": 0,
                "most_used_weapon": "",
                "best_agent": "",
                "match_details": [],
                "performance_trends": {},
                "map_performance": {},
                "agent_performance": {},
                "time_of_day_performance": {}
            }

            wins = 0
            total_headshots = 0
            total_kills = 0
            weapon_kills = defaultdict(int)
            agent_stats = defaultdict(lambda: {"kills": 0, "deaths": 0, "wins": 0, "matches": 0})
            map_stats = defaultdict(lambda: {"wins": 0, "matches": 0})
            time_stats = defaultdict(lambda: {"wins": 0, "matches": 0})

            for match in matches:
                # Get player data from match
                player = next((p for p in match['players']['all_players'] 
                             if p['name'] == stats['name'] and p['tag'] == stats['tag']), None)
                if not player:
                    continue

                # Basic match data
                analysis["modes"].append(match['metadata']['mode'])
                analysis["agents"].append(player['character'])
                analysis["maps"].append(match['metadata']['map'])
                
                # KDA and score
                analysis["avg_kda"][0] += player['stats']['kills']
                analysis["avg_kda"][1] += player['stats']['deaths']
                analysis["avg_kda"][2] += player['stats']['assists']
                analysis["avg_score"] += player['stats']['score']

                # Track weapon usage and headshots
                for kill in match.get('kills', []):
                    if kill.get('killer_puuid') == player['puuid']:
                        weapon_kills[kill['killer_weapon_name']] += 1
                        if kill.get('headshot', False):
                            total_headshots += 1
                        total_kills += 1

                # Track win/loss
                team = player['team'].lower()
                won = match['teams'][team]['has_won']
                if won:
                    wins += 1

                # Track agent performance
                agent = player['character']
                agent_stats[agent]["kills"] += player['stats']['kills']
                agent_stats[agent]["deaths"] += player['stats']['deaths']
                agent_stats[agent]["matches"] += 1
                if won:
                    agent_stats[agent]["wins"] += 1

                # Track map performance
                map_name = match['metadata']['map']
                map_stats[map_name]["matches"] += 1
                if won:
                    map_stats[map_name]["wins"] += 1

                # Track time of day performance
                match_time = datetime.fromisoformat(match['metadata']['game_start'])
                hour = match_time.hour
                time_period = f"{hour:02d}:00"
                time_stats[time_period]["matches"] += 1
                if won:
                    time_stats[time_period]["wins"] += 1

                # Store match details
                match_detail = {
                    "mode": match['metadata']['mode'],
                    "map": match['metadata']['map'],
                    "agent": player['character'],
                    "kda": f"{player['stats']['kills']}/{player['stats']['deaths']}/{player['stats']['assists']}",
                    "score": player['stats']['score'],
                    "result": "Win" if won else "Loss",
                    "headshots": sum(1 for k in match.get('kills', []) 
                                   if k.get('killer_puuid') == player['puuid'] and k.get('headshot', False))
                }
                analysis["match_details"].append(match_detail)

            # Calculate averages and percentages
            num_matches = len(matches)
            if num_matches > 0:
                analysis["avg_kda"] = [round(k / num_matches, 2) for k in analysis["avg_kda"]]
                analysis["avg_score"] = round(analysis["avg_score"] / num_matches, 0)
                analysis["win_rate"] = round((wins / num_matches) * 100, 2)
                analysis["headshot_percentage"] = round((total_headshots / total_kills * 100), 2) if total_kills > 0 else 0

            # Calculate most played and best performing
            analysis["most_played_mode"] = Counter(analysis["modes"]).most_common(1)[0][0]
            analysis["most_played_agent"] = Counter(analysis["agents"]).most_common(1)[0][0]
            analysis["most_played_map"] = Counter(analysis["maps"]).most_common(1)[0][0]
            analysis["most_used_weapon"] = Counter(weapon_kills).most_common(1)[0][0]

            # Calculate performance by agent
            analysis["agent_performance"] = {
                agent: {
                    "matches": stats["matches"],
                    "wins": stats["wins"],
                    "win_rate": round((stats["wins"] / stats["matches"] * 100), 2),
                    "kd_ratio": round(stats["kills"] / stats["deaths"], 2) if stats["deaths"] > 0 else stats["kills"]
                }
                for agent, stats in agent_stats.items()
            }

            # Calculate map performance
            analysis["map_performance"] = {
                map_name: {
                    "matches": stats["matches"],
                    "wins": stats["wins"],
                    "win_rate": round((stats["wins"] / stats["matches"] * 100), 2)
                }
                for map_name, stats in map_stats.items()
            }

            # Calculate time of day performance
            analysis["time_of_day_performance"] = {
                time: {
                    "matches": stats["matches"],
                    "wins": stats["wins"],
                    "win_rate": round((stats["wins"] / stats["matches"] * 100), 2)
                }
                for time, stats in time_stats.items()
            }

            return analysis

        except Exception as e:
            command_logger.error(f"Error analyzing matches: {str(e)}")
            return None

    @staticmethod
    def get_performance_insights(analysis: Dict) -> List[str]:
        """Generate insights from match analysis"""
        insights = []
        
        # Win rate insights
        if analysis["win_rate"] >= 55:
            insights.append("🏆 Strong overall performance with above average win rate")
        elif analysis["win_rate"] <= 45:
            insights.append("📉 Room for improvement in overall win rate")

        # Headshot percentage insights
        if analysis["headshot_percentage"] >= 25:
            insights.append("🎯 Excellent aim with high headshot percentage")
        elif analysis["headshot_percentage"] <= 15:
            insights.append("🎯 Consider aim training to improve headshot accuracy")

        # Agent insights
        best_agent = max(analysis["agent_performance"].items(), 
                        key=lambda x: x[1]["win_rate"])
        insights.append(f"👤 Best performance with {best_agent[0]} ({best_agent[1]['win_rate']}% win rate)")

        # Map insights
        best_map = max(analysis["map_performance"].items(),
                      key=lambda x: x[1]["win_rate"])
        insights.append(f"🗺️ Strongest on {best_map[0]} ({best_map[1]['win_rate']}% win rate)")

        return insights