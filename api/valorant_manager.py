import aiohttp
from bs4 import BeautifulSoup
from motor.motor_asyncio import AsyncIOMotorClient
import config
from utils.logger import api_logger
import urllib.parse
from aiolimiter import AsyncLimiter
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import asyncio
import random
import time
from fake_useragent import UserAgent
import sys
import os

# Add the path to the cloned repository
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'valorant_tracker', 'Valorant-Tracker-Web-Scraper'))
from valorant_scraper import ValorantScraper

class ValorantManager:
    def __init__(self, db):
        self.db = db
        self.users_collection = self.db['users']
        self.api_key = config.RIOT_API_KEY
        self.base_url = "https://api.riotgames.com"
        self.scraper = ValorantScraper()

    def setup_webdriver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        ua = UserAgent()
        chrome_options.add_argument(f"user-agent={ua.random}")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    async def store_riot_id(self, twitch_username, riot_id):
        try:
            result = await self.users_collection.update_one(
                {"username": twitch_username.lower()},
                {"$set": {"riot_id": riot_id}},
                upsert=True
            )
            if result.modified_count > 0 or result.upserted_id is not None:
                return True, "Riot ID updated successfully"
            else:
                return False, "No changes were made to the database"
        except Exception as e:
            api_logger.error(f"Error storing Riot ID for {twitch_username}: {str(e)}")
            return False, f"Database error: {str(e)}"

    async def get_riot_id(self, twitch_username):
        user = await self.users_collection.find_one({"username": twitch_username.lower()})
        return user.get('riot_id') if user else None

    async def fetch_valorant_stats(self, riot_id):
        name, tag = riot_id.split('#')
        try:
            stats = await self.scraper.get_player_stats(name, tag)
            return stats, None
        except Exception as e:
            api_logger.error(f"Failed to fetch Valorant stats for {riot_id}. Error: {str(e)}")
            return None, f"An error occurred while fetching stats: {str(e)}"

    async def _make_api_request(self, url):
        headers = {"X-Riot-Token": self.api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API request failed with status {response.status}")

    def _process_valorant_stats(self, stats_data):
        # Process the stats_data and return a dictionary of relevant stats
        # This will depend on the structure of the Riot API response
        # You'll need to adjust this based on the actual API response
        return {
            "rank": "Placeholder Rank",
            "kd_ratio": "Placeholder K/D",
            "win_rate": "Placeholder Win Rate",
            "avg_score": "Placeholder Avg Score",
            "headshot_pct": "Placeholder Headshot %"
        }
