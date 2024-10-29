from typing import Dict, List, Optional, Any
import aiohttp
import json
import config
from utils.logger import command_logger
from .auth.valorant_auth_client import ValorantAuthClient

class ValorantClient:
    def __init__(self, auth_client: ValorantAuthClient):
        self.auth = auth_client
        self.regions = {
            'na': 'na.api.riotgames.com',
            'americas': 'americas.api.riotgames.com'
        }
        # Initialize headers
        self.riot_headers = {
            'X-Riot-Token': config.RIOT_API_KEY
        }
        self.val_headers = {
            'X-Riot-Entitlements-JWT': '',
            'Authorization': ''
        }

    async def initialize(self) -> bool:
        """Initialize the client with auth tokens"""
        try:
            if not self.auth.auth_keys:
                return False
            
            self.val_headers = {
                'X-Riot-Entitlements-JWT': self.auth.auth_keys.get('entitlements_token', ''),
                'Authorization': f"Bearer {self.auth.auth_keys.get('access_token', '')}"
            }
            return True
        except Exception as e:
            command_logger.error(f"Failed to initialize ValorantClient: {str(e)}")
            return False

    async def get_account_by_riot_id(self, name: str, tag: str) -> Optional[Dict[str, Any]]:
        """Get account information by Riot ID using Riot API"""
        try:
            url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.riot_headers) as response:
                    if response.status == 200:
                        return await response.json()
                    command_logger.error(f"Account lookup failed: Status {response.status}")
                    return None
        except Exception as e:
            command_logger.error(f"Error in get_account_by_riot_id: {str(e)}")
            return None

    async def get_match_history(self, puuid: str) -> Optional[Dict[str, Any]]:
        """Get match history using Riot API"""
        try:
            url = f"https://na.api.riotgames.com/val/match/v1/matchlists/by-puuid/{puuid}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.riot_headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        command_logger.info(f"Retrieved match history for {puuid}")
                        return data
                    else:
                        body = await response.text()
                        command_logger.error(f"Match history error: Status {response.status}, Response: {body}")
                        return None
        except Exception as e:
            command_logger.error(f"Error in get_match_history: {str(e)}")
            return None

    async def get_match_details(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get match details using VALORANT client API"""
        try:
            url = f"https://pd.{self.auth.region}.a.pvp.net/match-details/v1/matches/{match_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.val_headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        command_logger.info(f"Retrieved match details for {match_id}")
                        return data
                    else:
                        body = await response.text()
                        command_logger.error(f"Match details error: Status {response.status}, Response: {body}")
                        return None

        except Exception as e:
            command_logger.error(f"Exception in get_match_details: {str(e)}")
            return None

    async def get_recent_matches(self, puuid: str, size: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        Get recent matches with full details
        
        Args:
            puuid: Player UUID
            size: Number of recent matches to fetch
        """
        try:
            # Get match history
            matches = await self.get_match_history(puuid)
            if not matches:
                command_logger.error(f"No match history found for {puuid}")
                return None

            # Get details for the most recent matches
            detailed_matches = []
            for match in matches[:size]:
                match_id = match.get('matchId')
                if match_id:
                    match_details = await self.get_match_details(match_id)
                    if match_details:
                        detailed_matches.append(match_details)

            command_logger.info(f"Retrieved {len(detailed_matches)} recent matches for {puuid}")
            return detailed_matches

        except Exception as e:
            command_logger.error(f"Exception in get_recent_matches: {str(e)}")
            return None

    async def get_mmr(self, puuid: str) -> Optional[Dict[str, Any]]:
        """Get MMR data for a player"""
        url = f"https://na.api.riotgames.com/val/ranked/v1/by-puuid/{puuid}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                command_logger.error(f"MMR error: Status {response.status}")
                return None

    async def get_leaderboard(self, act_id: str, size: int = 10, startIndex: int = 0) -> Optional[Dict[str, Any]]:
        """Get competitive leaderboard"""
        url = f"https://na.api.riotgames.com/val/ranked/v1/leaderboards/by-act/{act_id}?size={size}&startIndex={startIndex}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                command_logger.error(f"Leaderboard error: Status {response.status}")
                return None

    async def get_content(self) -> Optional[Dict[str, Any]]:
        """Get current game content (maps, agents, etc.)"""
        endpoint = "/content/v1/contents"
        return await self._make_request(endpoint)

    def _validate_region(self, region: str) -> bool:
        """Validate if a region is supported"""
        return region.lower() in self.regions