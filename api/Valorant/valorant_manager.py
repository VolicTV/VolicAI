from typing import Optional, Tuple, Dict, List, Any
from datetime import datetime
import aiohttp
import asyncio
import socket
import ssl
import config

from .valorant_client import ValorantClient
from .auth.valorant_auth_client import ValorantAuthClient
from .valorant_cache import ValorantCache
from .valorant_formatter import ResponseFormatter
from utils.valorant.valorant_analysis import MatchAnalyzer
from .valorant_rate_limiter import APIThrottler
from .valorant_validator import ValorantValidator
from .valorant_transformer import ValorantTransformer

from utils.logger import command_logger

class ValorantManager:
    """Main manager class for Valorant integration"""
    
    def __init__(self, db):
        self.db = db
        self.auth_client = ValorantAuthClient()
        self.client = ValorantClient(self.auth_client)
        self.cache = ValorantCache(self.db)
        self.formatter = ResponseFormatter()
        self.throttler = APIThrottler()
        self.validator = ValorantValidator()
        self.transformer = ValorantTransformer()

    async def initialize(self) -> bool:
        """Initialize the Valorant manager and its components"""
        try:
            # Initialize auth client
            auth_success = await self.auth_client.initialize(
                config.VALORANT_USERNAME, 
                config.VALORANT_PASSWORD
            )
            if not auth_success:
                command_logger.error("Failed to initialize auth client")
                return False

            # Initialize main client with auth tokens
            client_success = await self.client.initialize()
            if not client_success:
                command_logger.error("Failed to initialize Valorant client")
                return False

            return True
        except Exception as e:
            command_logger.error(f"Failed to initialize ValorantManager: {str(e)}")
            return False

    async def get_riot_id(self, twitch_username: str) -> Optional[str]:
        """Get stored Riot ID for a Twitch user"""
        try:
            return await self.cache.get_user_riot_id(twitch_username.lower())
        except Exception as e:
            command_logger.error(f"Error getting Riot ID for {twitch_username}: {str(e)}")
            return None

    async def store_riot_id(self, twitch_username: str, riot_id: str) -> Tuple[bool, str]:
        """Store and validate Riot ID for a Twitch user"""
        try:
            # Validate Riot ID format
            self.validator.validate_riot_id(riot_id)
            
            # Verify account exists
            name, tag = riot_id.split('#')
            account = await self.throttler.execute(
                self.client.get_account_by_riot_id,
                f"account_{riot_id}",
                300,  # 5-minute cooldown
                name, 
                tag
            )
            
            if not account:
                return False, "Could not verify Riot ID. Please check if it's correct"
                
            # Store in cache
            success = await self.cache.store_user_riot_id(twitch_username.lower(), riot_id)
            return success, "Riot ID updated successfully" if success else "Error storing Riot ID"
            
        except InvalidRiotIDError as e:
            return False, str(e)
        except RateLimitError as e:
            return False, str(e)
        except Exception as e:
            command_logger.error(f"Error storing Riot ID for {twitch_username}: {str(e)}")
            return False, f"Error storing Riot ID: {str(e)}"

    async def get_player_stats(self, riot_id: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Get comprehensive player stats"""
        try:
            # Validate Riot ID
            self.validator.validate_riot_id(riot_id)
            
            # Get account info
            name, tag = riot_id.split('#')
            account = await self.throttler.execute(
                self.client.get_account_by_riot_id,
                f"account_{riot_id}",
                300,
                name, 
                tag
            )
            
            if not account:
                return None, "Could not find account"

            puuid = account['puuid']
            
            # Check cache first
            cached_stats = await self.cache.get_cached_stats(puuid)
            if cached_stats:
                return cached_stats, None

            # Fetch fresh data
            mmr_data = await self.throttler.execute(
                self.client.get_mmr,
                f"mmr_{puuid}",
                60,
                account['region'],
                puuid
            )
            
            if not mmr_data:
                return None, "Could not fetch MMR data"

            # Transform and cache the data
            stats = self.transformer.transform_player_stats(mmr_data)
            await self.cache.store_stats(puuid, stats)
            
            return stats, None

        except ValorantError as e:
            return None, str(e)
        except Exception as e:
            command_logger.error(f"Error fetching player stats: {str(e)}")
            return None, str(e)

    async def get_match_history(self, riot_id: str, num_matches: int = 5) -> Optional[List[Dict]]:
        """Get player's recent matches"""
        try:
            # Validate inputs
            self.validator.validate_riot_id(riot_id)
            self.validator.validate_match_count(num_matches)
            
            # Get account info
            name, tag = riot_id.split('#')
            account = await self.throttler.execute(
                self.client.get_account_by_riot_id,
                f"account_{riot_id}",
                300,
                name, 
                tag
            )
            
            if not account:
                return None

            puuid = account['puuid']
            
            # Check cache first
            cached_matches = await self.cache.get_cached_matches(puuid)
            if cached_matches:
                return cached_matches[:num_matches]

            # Fetch fresh match history
            matches = await self.throttler.execute(
                self.client.get_match_history,
                f"matches_{puuid}",
                60,
                puuid
            )
            
            if not matches:
                return None

            # Get detailed match data and transform
            detailed_matches = []
            for match in matches['matches'][:num_matches]:
                match_details = await self.throttler.execute(
                    self.client.get_match_details,
                    f"match_{match['matchId']}",
                    60,
                    match['matchId']
                )
                if match_details:
                    transformed_match = self.transformer.transform_match_data(match_details)
                    detailed_matches.append(transformed_match)

            if detailed_matches:
                await self.cache.store_matches(puuid, detailed_matches)
                
            return detailed_matches

        except ValorantError as e:
            command_logger.error(f"Valorant error in match history: {str(e)}")
            return None
        except Exception as e:
            command_logger.error(f"Error fetching match history: {str(e)}")
            return None

    async def clear_player_cache(self, riot_id: str) -> bool:
        """Clear cached data for a player"""
        try:
            self.validator.validate_riot_id(riot_id)
            name, tag = riot_id.split('#')
            account = await self.client.get_account_by_riot_id(name, tag)
            if account:
                return await self.cache.clear_cache(account['puuid'])
            return False
        except Exception as e:
            command_logger.error(f"Error clearing cache: {str(e)}")
            return False

    async def test_riot_api_connection(self) -> Tuple[bool, str]:
        """Test connection to Riot API"""
        try:
            # Try to resolve the hostname
            ip = socket.gethostbyname('api.riotgames.com')
            command_logger.info(f"Successfully resolved api.riotgames.com to {ip}")
            
            # Try to establish a connection
            sock = socket.create_connection((ip, 443), timeout=5)
            sock.close()
            return True, "Connection successful"
        except socket.gaierror as e:
            return False, f"DNS resolution failed: {str(e)}"
        except socket.timeout:
            return False, "Connection timed out"
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"

    async def set_riot_id(self, username: str, riot_id: str) -> bool:
        """Set and verify a user's Riot ID"""
        try:
            # Check if user already has this Riot ID
            existing_user = await self.db.users.find_one({"username": username.lower()})
            if existing_user and existing_user.get('riot_id') == riot_id:
                command_logger.info(f"Riot ID {riot_id} already set for {username}")
                return True

            # Test connection before making API call
            connection_ok, error_msg = await self.test_riot_api_connection()
            if not connection_ok:
                command_logger.error(f"Riot API connection test failed: {error_msg}")
                # Store the ID without verification if we can't connect
                await self.cache.store_user_riot_id(username, riot_id, verified=False)
                return True

            # Validate Riot ID format
            name, tag = riot_id.split('#')
            if not name or not tag:
                return False

            # Try to verify the Riot ID exists with retries
            for attempt in range(self.max_retries):
                try:
                    connector = aiohttp.TCPConnector(
                        ssl=ssl.create_default_context(),
                        family=socket.AF_INET,  # Force IPv4
                        verify_ssl=False  # Only if necessary
                    )
                    
                    async with aiohttp.ClientSession(connector=connector) as session:
                        headers = {
                            "X-Riot-Token": config.RIOT_API_KEY
                        }
                        url = f"https://api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
                        
                        async with session.get(url, headers=headers, timeout=10) as response:
                            if response.status == 200:
                                await self.cache.store_user_riot_id(username, riot_id)
                                command_logger.info(f"Set Riot ID for {username}: {riot_id}")
                                return True
                            elif response.status == 404:
                                command_logger.error(f"Riot ID not found: {riot_id}")
                                return False
                            else:
                                command_logger.error(f"Failed to verify Riot ID {riot_id}. Status: {response.status}")
                                if attempt < self.max_retries - 1:
                                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                                    continue
                                return False

                except Exception as e:
                    command_logger.error(f"API request attempt {attempt + 1} failed: {str(e)}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                    # If all retries failed, store the ID anyway
                    await self.cache.store_user_riot_id(username, riot_id, verified=False)
                    return True

            return False

        except Exception as e:
            command_logger.error(f"Error setting Riot ID: {str(e)}")
            return False