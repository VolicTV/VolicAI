import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient
import config
from utils.logger import api_logger
from utils.web_scraper import scrape_web_data   
import urllib.parse
from collections import Counter
import numpy as np
import requests
from bs4 import BeautifulSoup
import logging

class ValorantManager:
    def __init__(self, db):
        self.db = db
        self.users_collection = self.db['users']
        self.base_url = "https://api.henrikdev.xyz/valorant"

    async def get_riot_id(self, twitch_username):
        user = await self.users_collection.find_one({"username": twitch_username.lower()})
        return user.get('riot_id') if user else None

    async def store_riot_id(self, twitch_username, riot_id):
        try:
            result = await self.users_collection.update_one(
                {"username": twitch_username.lower()},
                {"$set": {"riot_id": riot_id}},
                upsert=True
            )
            return True, "Riot ID updated successfully"
        except Exception as e:
            api_logger.error(f"Error storing Riot ID for {twitch_username}: {str(e)}")
            return False, f"Error storing Riot ID: {str(e)}"

    async def get_player_stats(self, riot_id):
        try:
            name, tag = riot_id.split('#')
            encoded_name = urllib.parse.quote(name)
            encoded_tag = urllib.parse.quote(tag)

            headers = {"Authorization": config.HENRIKDEV_API_KEY}
            async with aiohttp.ClientSession() as session:
                # Get account info
                account_url = f"{self.base_url}/v1/account/{encoded_name}/{encoded_tag}"
                async with session.get(account_url, headers=headers) as response:
                    if response.status != 200:
                        api_logger.error(f"Error fetching account data: {await response.text()}")
                        return None
                    account_data = await response.json()

                # Get MMR info
                mmr_url = f"{self.base_url}/v2/mmr/eu/{encoded_name}/{encoded_tag}"
                async with session.get(mmr_url, headers=headers) as response:
                    if response.status != 200:
                        api_logger.error(f"Error fetching MMR data: {await response.text()}")
                        return None
                    mmr_data = await response.json()

            return {
                "account": account_data.get("data", {}),
                "mmr": mmr_data.get("data", {})
            }
        except Exception as e:
            api_logger.error(f"Error fetching Valorant stats for {riot_id}: {str(e)}", exc_info=True)
            return None

    async def get_player_recent_matches(self, riot_id, num_matches=5):
        try:
            if '#' not in riot_id:
                api_logger.error(f"Invalid Riot ID format: {riot_id}")
                return None

            name, tag = riot_id.split('#')
            encoded_name = urllib.parse.quote(name)
            encoded_tag = urllib.parse.quote(tag)

            headers = {"Authorization": config.HENRIKDEV_API_KEY}
            url = f"{self.base_url}/v1/stored-matches/eu/{encoded_name}/{encoded_tag}?size={num_matches}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        api_logger.error(f"Error fetching stored matches: {await response.text()}")
                        return None
                    data = await response.json()
                    return data.get('data', [])
        except Exception as e:
            api_logger.error(f"Error fetching stored matches for {riot_id}: {str(e)}", exc_info=True)
            return None

    async def analyze_recent_matches(self, riot_id, num_matches=5):
        matches_data = await self.get_player_recent_matches(riot_id, num_matches=num_matches)
        if not matches_data:
            return None

        analysis = {
            "total_matches": len(matches_data),
            "modes": [],
            "agents": [],
            "maps": [],
            "avg_kda": [0, 0, 0],
            "avg_score": 0,
            "win_rate": 0,
            "match_details": []
        }

        for match in matches_data:
            meta = match.get('meta', {})
            stats = match.get('stats', {})
            teams = match.get('teams', {})

            analysis["modes"].append(meta.get('mode', 'Unknown'))
            analysis["agents"].append(stats.get('character', {}).get('name', 'Unknown'))
            analysis["maps"].append(meta.get('map', {}).get('name', 'Unknown'))
            
            analysis["avg_kda"][0] += stats.get('kills', 0)
            analysis["avg_kda"][1] += stats.get('deaths', 0)
            analysis["avg_kda"][2] += stats.get('assists', 0)
            analysis["avg_score"] += stats.get('score', 0)

            if meta.get('mode') != 'Deathmatch':
                analysis["win_rate"] += 1 if stats.get('team') == meta.get('winner') else 0

            match_detail = {
                "mode": meta.get('mode', 'Unknown'),
                "map": meta.get('map', {}).get('name', 'Unknown'),
                "agent": stats.get('character', {}).get('name', 'Unknown'),
                "kda": f"{stats.get('kills', 0)}/{stats.get('deaths', 0)}/{stats.get('assists', 0)}",
                "score": stats.get('score', 0),
                "result": "Win" if stats.get('team') == meta.get('winner') else "Loss"
            }
            analysis["match_details"].append(match_detail)

        # Calculate averages
        num_matches = len(matches_data)
        if num_matches > 0:
            analysis["avg_kda"] = [round(k / num_matches, 2) for k in analysis["avg_kda"]]
            analysis["avg_score"] = round(analysis["avg_score"] / num_matches, 0)  # Changed to round to nearest integer
            analysis["win_rate"] = round((analysis["win_rate"] / num_matches) * 100, 2)

        analysis["most_played_mode"] = max(set(analysis["modes"]), key=analysis["modes"].count)
        analysis["most_played_agent"] = max(set(analysis["agents"]), key=analysis["agents"].count)
        analysis["most_played_map"] = max(set(analysis["maps"]), key=analysis["maps"].count)

        return analysis
    
    async def fetch_valorant_pickup_lines(self):
        url = "https://psycatgames.com/magazine/conversation-starters/valorant-pick-up-lines/"
        valorant_pickup_lines = scrape_web_data(url, tag='h3')
        
        # Log the fetched pick-up lines
        logging.info(f"Fetched Valorant pick-up lines: {valorant_pickup_lines}")
        
        return valorant_pickup_lines
    
