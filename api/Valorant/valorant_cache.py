from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from .valorant_constants import CACHE_DURATIONS
from utils.logger import command_logger

class ValorantCache:
    """Cache handler for Valorant data"""

    def __init__(self, db: AsyncIOMotorClient):
        """Initialize cache with database connection"""
        self.db = db
        self.valorant_db = db.twitch_bot_db
        self.riot_ids = self.valorant_db.riot_ids
        self.player_stats = self.valorant_db.player_stats
        self.match_history = self.valorant_db.match_history

        # Create indexes
        self.riot_ids.create_index("twitch_username", unique=True)
        self.player_stats.create_index("puuid", unique=True)
        self.player_stats.create_index("last_updated")
        self.match_history.create_index("puuid")
        self.match_history.create_index("match_id", unique=True)

    async def get_user_riot_id(self, twitch_username: str) -> Optional[str]:
        """Get stored Riot ID from user profile or dedicated riot_ids collection"""
        try:
            # First check the dedicated riot_ids collection
            user = await self.riot_ids.find_one(
                {"twitch_username": twitch_username.lower()},
                {"riot_id": 1}
            )
            if user and 'riot_id' in user:
                return user['riot_id']

            # If not found, check the users collection
            user = await self.valorant_db.users.find_one(
                {"username": twitch_username.lower()},
                {"riot_id": 1}
            )
            if user and 'riot_id' in user:
                # Also store in riot_ids collection for future lookups
                await self.store_user_riot_id(twitch_username, user['riot_id'])
                return user['riot_id']

            return None
        except Exception as e:
            command_logger.error(f"Error fetching Riot ID for {twitch_username}: {str(e)}")
            return None

    async def store_user_riot_id(self, twitch_username: str, riot_id: str, verified: bool = True) -> bool:
        """Store Riot ID in both collections"""
        try:
            update_data = {
                "riot_id": riot_id,
                "riot_id_updated_at": datetime.utcnow(),
                "verified": verified
            }

            # Store in dedicated riot_ids collection
            await self.riot_ids.update_one(
                {"twitch_username": twitch_username.lower()},
                {"$set": update_data},
                upsert=True
            )

            # Store in users collection
            await self.valorant_db.users.update_one(
                {"username": twitch_username.lower()},
                {"$set": update_data},
                upsert=True
            )
            return True
        except Exception as e:
            command_logger.error(f"Error storing Riot ID: {str(e)}")
            return False

    async def get_cached_matches(self, puuid: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached match history for a player"""
        try:
            cached = await self.match_history.find_one({"puuid": puuid})
            if cached and datetime.utcnow() - cached['last_updated'] < timedelta(seconds=CACHE_DURATIONS['MATCHES']):
                return cached['matches']
            return None
        except Exception as e:
            command_logger.error(f"Error fetching cached matches: {str(e)}")
            return None

    async def store_matches(self, puuid: str, matches: List[Dict[str, Any]]) -> bool:
        """Store match history for a player"""
        try:
            await self.match_history.update_one(
                {"puuid": puuid},
                {"$set": {
                    "matches": matches,
                    "last_updated": datetime.utcnow()
                }},
                upsert=True
            )
            return True
        except Exception as e:
            command_logger.error(f"Error storing matches: {str(e)}")
            return False

    async def get_cached_mmr(self, puuid: str) -> Optional[Dict[str, Any]]:
        """Get cached MMR data for a player"""
        try:
            cached = await self.player_stats.find_one({"puuid": puuid})
            if cached and datetime.utcnow() - cached['last_updated'] < timedelta(seconds=CACHE_DURATIONS['MMR']):
                return cached['mmr']
            return None
        except Exception as e:
            command_logger.error(f"Error fetching cached MMR: {str(e)}")
            return None

    async def store_mmr(self, puuid: str, mmr_data: Dict[str, Any]) -> bool:
        """Store MMR data for a player"""
        try:
            await self.player_stats.update_one(
                {"puuid": puuid},
                {"$set": {
                    "mmr": mmr_data,
                    "last_updated": datetime.utcnow()
                }},
                upsert=True
            )
            return True
        except Exception as e:
            command_logger.error(f"Error storing MMR: {str(e)}")
            return False

    async def get_cached_stats(self, puuid: str) -> Optional[Dict[str, Any]]:
        """Get cached player stats"""
        try:
            cached = await self.player_stats.find_one({"puuid": puuid})
            if cached and datetime.utcnow() - cached['last_updated'] < timedelta(seconds=CACHE_DURATIONS['ACCOUNT']):
                return cached['stats']
            return None
        except Exception as e:
            command_logger.error(f"Error fetching cached stats: {str(e)}")
            return None

    async def store_stats(self, puuid: str, stats: Dict[str, Any]) -> bool:
        """Store player stats"""
        try:
            await self.player_stats.update_one(
                {"puuid": puuid},
                {"$set": {
                    "stats": stats,
                    "last_updated": datetime.utcnow()
                }},
                upsert=True
            )
            return True
        except Exception as e:
            command_logger.error(f"Error storing stats: {str(e)}")
            return False

    async def clear_cache(self, puuid: str) -> bool:
        """Clear all cached data for a player"""
        try:
            await self.match_history.delete_one({"puuid": puuid})
            await self.player_stats.delete_one({"puuid": puuid})
            return True
        except Exception as e:
            command_logger.error(f"Error clearing cache: {str(e)}")
            return False