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
import asyncio
from valclient.client import Client
import valorant
import os

class ValorantManager:
    def __init__(self, db):
        self.db = db
        self.users_collection = self.db['users']
        self.base_url = "https://api.henrikdev.xyz/valorant"
        self.headers = {"Authorization": config.HENRIKDEV_API_KEY}

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
            logging.error(f"Error storing Riot ID for {twitch_username}: {str(e)}")
            return False, f"Error storing Riot ID: {str(e)}"

    async def get_player_stats(self, riot_id):
        try:
            name, tag = riot_id.split('#')
            encoded_name = urllib.parse.quote(name)
            encoded_tag = urllib.parse.quote(tag)

            url = f"{self.base_url}/v1/account/{encoded_name}/{encoded_tag}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 401:
                        logging.error("Unauthorized access to the API. Please check your API key.")
                        return None, "Unauthorized access to the API. Please check your API key."
                    elif response.status != 200:
                        error_text = await response.text()
                        logging.error(f"Error fetching player stats: {error_text}")
                        return None, f"Error fetching player stats: {error_text}"
                    data = await response.json()
                    return data.get('data'), None
        except Exception as e:
            logging.error(f"Error fetching player stats: {str(e)}")
            return None, f"Error fetching player stats: {str(e)}"

    async def get_player_recent_matches(self, riot_id, num_matches=5):
        try:
            name, tag = riot_id.split('#')
            encoded_name = urllib.parse.quote(name)
            encoded_tag = urllib.parse.quote(tag)

            url = f"{self.base_url}/v3/matches/eu/{encoded_name}/{encoded_tag}?filter=competitive&size={num_matches}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 401:
                        logging.error("Unauthorized access to the API. Please check your API key.")
                        return None, "Unauthorized access to the API. Please check your API key."
                    elif response.status != 200:
                        error_text = await response.text()
                        logging.error(f"Error fetching recent matches: {error_text}")
                        return None, f"Error fetching recent matches: {error_text}"
                    data = await response.json()
                    return data.get('data', []), None
        except Exception as e:
            logging.error(f"Error fetching recent matches: {str(e)}")
            return None, f"Error fetching recent matches: {str(e)}"

    async def analyze_recent_matches(self, riot_id, num_matches=5):
        stats = await self.get_player_stats(riot_id)
        matches = await self.get_player_recent_matches(riot_id, num_matches)
        
        if not stats or not matches:
            return None

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
            "match_details": []
        }

        for match in matches:
            player = next((p for p in match['players']['all_players'] if p['name'] == stats['name'] and p['tag'] == stats['tag']), None)
            if not player:
                continue

            analysis["modes"].append(match['metadata']['mode'])
            analysis["agents"].append(player['character'])
            analysis["maps"].append(match['metadata']['map'])
            
            analysis["avg_kda"][0] += player['stats']['kills']
            analysis["avg_kda"][1] += player['stats']['deaths']
            analysis["avg_kda"][2] += player['stats']['assists']
            analysis["avg_score"] += player['stats']['score']
            analysis["win_rate"] += 1 if player['team'] == match['teams'][player['team'].lower()]['has_won'] else 0
            analysis["headshot_percentage"] += player['stats']['headshots'] / player['stats']['kills'] if player['stats']['kills'] > 0 else 0

            match_detail = {
                "mode": match['metadata']['mode'],
                "map": match['metadata']['map'],
                "agent": player['character'],
                "kda": f"{player['stats']['kills']}/{player['stats']['deaths']}/{player['stats']['assists']}",
                "score": player['stats']['score'],
                "result": "Win" if player['team'] == match['teams'][player['team'].lower()]['has_won'] else "Loss"
            }
            analysis["match_details"].append(match_detail)

        num_matches = len(matches)
        if num_matches > 0:
            analysis["avg_kda"] = [round(k / num_matches, 2) for k in analysis["avg_kda"]]
            analysis["avg_score"] = round(analysis["avg_score"] / num_matches, 0)
            analysis["win_rate"] = round((analysis["win_rate"] / num_matches) * 100, 2)
            analysis["headshot_percentage"] = round((analysis["headshot_percentage"] / num_matches) * 100, 2)

        analysis["most_played_mode"] = max(set(analysis["modes"]), key=analysis["modes"].count)
        analysis["most_played_agent"] = max(set(analysis["agents"]), key=analysis["agents"].count)
        analysis["most_played_map"] = max(set(analysis["maps"]), key=analysis["maps"].count)

        # Analyze weapon stats (you might need to adjust this based on the actual data structure)
        weapons = [kill['killer_weapon_name'] for match in matches for kill in match['kills'] if kill['killer_puuid'] == player['puuid']]
        analysis["most_used_weapon"] = max(set(weapons), key=weapons.count) if weapons else "Unknown"

        # Analyze agent stats
        agent_stats = Counter(analysis["agents"])
        analysis["best_agent"] = max(agent_stats, key=agent_stats.get)

        return analysis
    
    async def fetch_valorant_pickup_lines(self):
        url = "https://psycatgames.com/magazine/conversation-starters/valorant-pick-up-lines/"
        valorant_pickup_lines = scrape_web_data(url, tag='h3')
        
        # Log the fetched pick-up lines
        logging.info(f"Fetched Valorant pick-up lines: {valorant_pickup_lines}")
        
        return valorant_pickup_lines
    





