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
    def __init__(self, users_collection, ignored_users_file):
        self.users_collection = users_collection['users']
        self.ignored_user_manager = IgnoredUserManager(ignored_users_file)
        self.access_token = None
        self.token_expiry = datetime.now()
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes

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

    async def get_user_info(self, user_id):
        current_time = time.time()
        if user_id in self.cache and current_time - self.cache[user_id]['timestamp'] < self.cache_timeout:
            bot_logger.debug(f"Cache hit for user_id: {user_id}")
            return self.cache[user_id]['data']

        user_data = await self.users_collection.find_one({'_id': user_id})
        
        if user_data:
            self.cache[user_id] = {'data': user_data, 'timestamp': current_time}
            bot_logger.debug(f"User data summary for ID {user_id}: username: {user_data.get('username', 'Unknown')}, message count: {len(user_data.get('messages', []))}")
        else:
            bot_logger.debug(f"No user data found for user_id: {user_id}")

        return user_data

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

    async def update_user_chat_data(self, user_id, username, message_content, timestamp):
        if username.lstrip('@').lower() in self.ignored_user_manager.ignored_users:
            bot_logger.info(f"Ignoring message from {username} (ID: {user_id})")
            return

        if isinstance(message_content, list):
            message_content = ' '.join(message_content)

        new_message = {
            'content': message_content,
            'timestamp': timestamp.isoformat()
        }

        result = await self.users_collection.update_one(
            {'_id': user_id},
            {
                '$set': {'username': username.lower()},
                '$push': {
                    'messages': {
                        '$each': [new_message],
                        '$slice': -1000  # Keep only the last 1000 messages
                    }
                }
            },
            upsert=True
        )
        bot_logger.info(f"Updated user data for {username} (ID: {user_id}). Modified count: {result.modified_count}")
        self.get_user_summary.cache_clear()

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
    async def get_user_summary(self, user_id, channel_name):
        user_data = await self.get_user_info(user_id)
        
        if not user_data:
            return f"No data available for user ID: {user_id}"

        summary = f"User ID: {user_id}, Channel: {channel_name}\n"
        summary += f"Username: {user_data.get('username', 'Unknown')}\n"
        
        messages = user_data.get('messages', [])
        summary += f"Messages sent: {len(messages)}\n"
        
        recent_messages = messages[-100:]
        if recent_messages:
            summary += "Recent messages:\n"
            for msg in recent_messages:
                summary += f"- {msg['content']}\n"
        else:
            summary += "No recent messages available.\n"
        
        quotes = await self.get_user_quotes(user_id)
        if quotes:
            summary += f"Number of quotes: {len(quotes)}\n"
            summary += "Recent quotes:\n"
            for quote in quotes[:5]:
                summary += f"- {quote['text']}\n"
        else:
            summary += "No quotes available.\n"
        
        bot_logger.debug(f"User summary: {summary}")
        return summary
    
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


