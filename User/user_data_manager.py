import os
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp
import config
import asyncio
from datetime import datetime, timedelta
from utils.logger import bot_logger
from functools import lru_cache, wraps
import time
from datetime import datetime, timedelta
from User.ignored_user_manager import IgnoredUserManager
import json
from typing import List, Dict, Optional, Any
from utils.logger import command_logger

def timed_lru_cache(seconds: int, maxsize: int = 128):
    def wrapper_cache(func):
        cached_func = lru_cache(maxsize=maxsize)(func)
        cached_func.lifetime = timedelta(seconds=seconds)
        cached_func.expiration = datetime.utcnow() + cached_func.lifetime

        @wraps(cached_func)
        def wrapped_func(*args, **kwargs):
            if datetime.utcnow() >= cached_func.expiration:
                cached_func.cache_clear()
                cached_func.expiration = datetime.utcnow() + cached_func.lifetime

            return cached_func(*args, **kwargs)

        wrapped_func.cache_clear = cached_func.cache_clear  # Ensure cache_clear is accessible
        return wrapped_func

    return wrapper_cache

class UserDataManager:
    def __init__(self, db, ignored_users_file='data/ignored_users.json'):
        self.db = db
        self.ignored_users_file = ignored_users_file
        self.ignored_users = self.load_ignored_users()
        self.user_cache = {}
        self.cache = {}  # For user info cache
        self.cache_timeout = timedelta(minutes=5)

    def load_ignored_users(self) -> List[str]:
        """Load list of ignored users from JSON file"""
        try:
            with open(self.ignored_users_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create file if it doesn't exist
            with open(self.ignored_users_file, 'w') as f:
                json.dump([], f)
            return []
        except Exception as e:
            command_logger.error(f"Error loading ignored users: {str(e)}")
            return []

    def save_ignored_users(self):
        """Save current list of ignored users to JSON file"""
        try:
            with open(self.ignored_users_file, 'w') as f:
                json.dump(self.ignored_users, f)
        except Exception as e:
            command_logger.error(f"Error saving ignored users: {str(e)}")

    async def get_user_profile(self, username: str) -> dict:
        """Get a user's profile from the database"""
        try:
            # First check cache
            if username in self.user_cache:
                return self.user_cache[username]

            # If not in cache, get from database
            user_data = await self.db.users.find_one({"username": username.lower()})
            if user_data:
                self.user_cache[username] = user_data
                return user_data
            
            # If user doesn't exist, create basic profile
            basic_profile = {
                "username": username.lower(),
                "first_seen": datetime.utcnow(),
                "messages": [],
                "message_count": 0
            }
            await self.db.users.insert_one(basic_profile)
            self.user_cache[username] = basic_profile
            return basic_profile

        except Exception as e:
            command_logger.error(f"Error getting user profile for {username}: {str(e)}")
            return {}

    def clean_username(self, username):
        return username.lstrip('@').lower()

    async def ensure_valid_access_token(self):
        if datetime.now() >= self.token_expiry:
            url = 'https://id.twitch.tv/oauth2/token'
            params = {
                'client_id': config.TWITCH_CLIENT_ID,
                'client_secret': config.TWITCH_CLIENT_SECRET,
                'grant_type': 'client_credentials'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.access_token = data['access_token']
                        self.token_expiry = datetime.now() + timedelta(seconds=data['expires_in'] - 300)
                        print("Successfully refreshed Twitch access token")
                    else:
                        print(f"Failed to refresh access token. Status: {response.status}")
        return self.access_token

    async def get_user_info_by_name_or_id(self, identifier):
        if isinstance(identifier, str):
            url = f"https://api.twitch.tv/helix/users?login={identifier}"
        else:
            url = f"https://api.twitch.tv/helix/users?id={identifier}"
        
        headers = {
            "Client-ID": config.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {await self.ensure_valid_access_token()}"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['data']:
                        return data['data'][0]['id']
                print(f"Failed to get user ID for {identifier}. Status: {response.status}")
        return None

    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get cached or fresh user info"""
        try:
            current_time = datetime.utcnow()
            
            # Check cache first
            if user_id in self.cache:
                cache_entry = self.cache[user_id]
                if current_time - cache_entry['timestamp'] < self.cache_timeout:
                    return cache_entry['data']

            # Get fresh data
            user_data = await self.get_user_profile(user_id)
            
            # Update cache
            self.cache[user_id] = {
                'data': user_data,
                'timestamp': current_time
            }
            
            return user_data

        except Exception as e:
            command_logger.error(f"Error getting user info: {str(e)}")
            return {}

    async def get_user_data(self, user_id):
        user_data = await self.get_user_info(user_id)
        if not user_data:
            return {'all_messages': [], 'all_quotes': []}
        
        all_messages = [msg['content'] for msg in user_data.get('messages', [])]
        all_quotes = await self.get_user_quotes(user_id)
        return {
            'all_messages': all_messages,
            'all_quotes': [quote['text'] for quote in all_quotes]
    }

    async def update_user_chat_data(self, user_id: str, username: str, message: str, timestamp: datetime):
        """Update user's chat data in the database"""
        try:
            update_data = {
                "$set": {
                    "username": username.lower(),
                    "last_seen": timestamp
                },
                "$inc": {
                    "message_count": 1
                },
                "$push": {
                    "messages": {
                        "content": message,
                        "timestamp": timestamp
                    }
                }
            }
            result = await self.db.users.update_one(
                {"username": username.lower()},
                update_data,
                upsert=True
            )
            command_logger.info(f"Updated user data for {username} (ID: {user_id}). Modified count: {result.modified_count}")
            
            # Update cache
            if username in self.user_cache:
                del self.user_cache[username]  # Invalidate cache entry
                
        except Exception as e:
            command_logger.error(f"Error updating user chat data: {str(e)}")

    async def is_user_ignored(self, username: str) -> bool:
        """Check if a user is in the ignored list"""
        return username.lower() in [u.lower() for u in self.ignored_users]

    async def add_ignored_user(self, username: str) -> bool:
        """Add a user to the ignored list"""
        if not await self.is_user_ignored(username):
            self.ignored_users.append(username.lower())
            self.save_ignored_users()
            return True
        return False

    async def remove_ignored_user(self, username: str) -> bool:
        """Remove a user from the ignored list"""
        username = username.lower()
        if username in self.ignored_users:
            self.ignored_users.remove(username)
            self.save_ignored_users()
            return True
        return False

    async def get_ignored_users(self) -> List[str]:
        """Get the list of ignored users"""
        return self.ignored_users.copy()

    async def get_user_quotes(self, user_id):
        user_data = await self.users_collection.find_one({'_id': user_id})
        if not user_data or 'quotes' not in user_data:
            return []
        
        quote_ids = user_data['quotes']
        quotes = []
        for quote_id in quote_ids:
            quote = await self.bot.quote_manager.quotes_collection.find_one({'_id': quote_id})
            if quote:
                quotes.append(quote)
        
        return quotes
    
    @timed_lru_cache(seconds=300, maxsize=1000)
    async def get_user_summary(self, user_id: str, channel_name: str) -> Dict[str, Any]:
        """Get a summary of user data including chat stats and Valorant info"""
        try:
            # Get basic user info
            user_data = await self.get_user_profile(user_id)
            if not user_data:
                return {}

            # Calculate chat stats
            chat_stats = {
                "message_count": user_data.get("message_count", 0),
                "first_seen": user_data.get("first_seen", datetime.utcnow()),
                "last_seen": user_data.get("last_seen", datetime.utcnow())
            }

            return {
                "username": user_data.get("username", "Unknown"),
                "chat_stats": chat_stats,
                "channel": channel_name
            }

        except Exception as e:
            command_logger.error(f"Error getting user summary: {str(e)}")
            return {}

    async def fetch_user_chat_history(self, user_id, channel_name, limit=1000):
        all_messages = []
        pagination = None

        broadcaster_id = await self.get_user_info_by_name_or_id(channel_name)
        if not broadcaster_id:
            print(f"Could not fetch broadcaster ID for channel: {channel_name}")
            return all_messages

        while len(all_messages) < limit:
            url = "https://api.twitch.tv/helix/chat/messages"
            params = {
                "broadcaster_id": broadcaster_id['id'],
                "user_id": user_id,
                "first": 100
            }
            if pagination:
                params["after"] = pagination

            headers = {
                "Client-ID": config.TWITCH_CLIENT_ID,
                "Authorization": f"Bearer {await self.ensure_valid_access_token()}"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        messages = data.get("data", [])
                        all_messages.extend(messages)
                        pagination = data.get("pagination", {}).get("cursor")
                        
                        if not pagination or not messages:
                            break
                    else:
                        print(f"Failed to fetch chat messages. Status: {response.status}")
                        break

            await asyncio.sleep(1)  # Respect rate limits

        return all_messages[:limit]

    async def get_all_users(self):
        cursor = self.users_collection.find({}, {'_id': 1, 'username': 1})
        users = await cursor.to_list(length=None)
        return users
    
    def clear_user_summary_cache(self):
        self.get_user_summary.cache_clear()
        bot_logger.info("User summary cache cleared")    


