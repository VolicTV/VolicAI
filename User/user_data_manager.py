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

    async def fetch_user_id_from_twitch_api(self, username):
        url = f"https://api.twitch.tv/helix/users?login={username}"
        headers = {
            "Client-ID": config.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {await self.get_or_refresh_access_token()}"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['data']:
                        return data['data'][0]['id']
                print(f"Failed to get user ID for {username}. Status: {response.status}")
        return None
    
    async def collect_chat_data(self, user_id, username, message_content, timestamp):
        bot_logger.info(f"Collecting chat data for user: {username} (ID: {user_id})")
        if username.lstrip('@').lower() in self.ignored_user_manager.ignored_users:
            bot_logger.info(f"Ignoring message from {username} (ID: {user_id})")
            return

        if isinstance(message_content, list):
            message_content = ' '.join(message_content)

        user_data = await self.users_collection.find_one({'_id': user_id})
        if not user_data:
            bot_logger.info(f"Creating new user profile for {username} (ID: {user_id})")
            profile_data = await self.fetch_user_profile(user_id)
            user_data = {
                '_id': user_id,
                'username': username,
                'profile': profile_data,
                'messages': []
            }

        new_message = {
            'content': message_content,
            'timestamp': timestamp.isoformat()
        }

        result = await self.users_collection.update_one(
            {'_id': user_id},
            {
                '$set': {
                    'username': username.lower(),
                    'profile': user_data.get('profile', {})
                },
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

        # Clear the cache for this user
        self.generate_user_summary.cache_clear()

    async def fetch_user_profile(self, user_id, max_retries=3):
        for attempt in range(max_retries):
            try:
                access_token = await self.get_or_refresh_access_token()
                headers = {
                    'Client-ID': config.TWITCH_CLIENT_ID,
                    'Authorization': f'Bearer {access_token}'
                }
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'https://api.twitch.tv/helix/users?id={user_id}', headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data['data']:
                                user_data = data['data'][0]
                                return {
                                    'id': user_data['id'],
                                    'login': user_data['login'],
                                    'display_name': user_data['display_name'],
                                    'type': user_data['type'],
                                    'broadcaster_type': user_data['broadcaster_type'],
                                    'description': user_data['description'],
                                    'profile_image_url': user_data['profile_image_url'],
                                    'offline_image_url': user_data['offline_image_url'],
                                    'view_count': user_data['view_count'],
                                    'created_at': user_data['created_at']
                                }
                            return {}
                        elif response.status == 401:
                            print(f"Attempt {attempt + 1}: Access token expired. Refreshing...")
                            await self.get_or_refresh_access_token()
                        else:
                            error_message = await response.text()
                            print(f"Attempt {attempt + 1}: Failed to fetch user data for {user_id}. Status: {response.status}, Error: {error_message}")
            except aiohttp.ClientError as e:
                print(f"Attempt {attempt + 1}: Network error when fetching user data for {user_id}: {str(e)}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        print(f"Failed to fetch user data for {user_id} after {max_retries} attempts")
        return {}

    async def get_user_info(self, user_id):
        current_time = time.time()
        if user_id in self.cache and current_time - self.cache[user_id]['timestamp'] < self.cache_timeout:
            bot_logger.debug(f"Cache hit for user_id: {user_id}")
            return self.cache[user_id]['data']

        user_data = await self.users_collection.find_one({'_id': user_id})
        
        # Log a detailed info message
        bot_logger.info(f"User data found for ID {user_id}")

        # Log a summary as a debug message
        if user_data:
            username = user_data.get('username', 'Unknown')
            message_count = len(user_data.get('messages', []))
            recent_message = user_data['messages'][-1]['content'] if user_data.get('messages') else 'No messages'
            bot_logger.debug(f"User data summary for ID {user_id}: username: {username}, message count: {message_count}, recent message: {recent_message}")
        else:
            bot_logger.debug(f"No user data found for user_id: {user_id}")

        if user_data:
            self.cache[user_id] = {'data': user_data, 'timestamp': current_time}
        return user_data

    async def refresh_access_token(self):
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
                    self.token_expiry = datetime.now() + timedelta(seconds=data['expires_in'] - 300)  # Subtract 5 minutes for safety
                    print("Successfully refreshed Twitch access token")
                else:
                    print(f"Failed to refresh access token. Status: {response.status}")

    async def get_or_refresh_access_token(self):
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
                        self.token_expiry = datetime.now() + timedelta(seconds=data['expires_in'] - 300)  # Subtract 5 minutes for safety
                        print("Successfully refreshed Twitch access token")
                    else:
                        print(f"Failed to refresh access token. Status: {response.status}")
        return self.access_token

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

    @timed_lru_cache(seconds=300, maxsize=1000)  # Cache for 5 minutes, store up to 1000 items
    async def generate_user_summary(self, user_id, channel_name):
        bot_logger.info(f"Generating user summary for user ID: {user_id}")
        user_data = await self.users_collection.find_one({'_id': user_id})
        
        if not user_data:
            bot_logger.warning(f"No data available for user ID: {user_id}")
            return f"No data available for user ID: {user_id}"

        bot_logger.info(f"User data found for ID {user_id}")

        summary = f"User ID: {user_id}, Channel: {channel_name}\n"
        summary += f"Username: {user_data.get('username', 'Unknown')}\n"
        
        messages = user_data.get('messages', [])
        summary += f"Messages sent: {len(messages)}\n"
        
        # Add recent messages
        recent_messages = messages[-20:]  # Get last 20 messages
        if recent_messages:
            summary += "Recent messages:\n"
            for msg in recent_messages:
                summary += f"- {msg['content']}\n"
        else:
            summary += "No recent messages available.\n"
        
        # Add quotes
        quotes = await self.get_user_quotes(user_id)
        if quotes:
            summary += f"Number of quotes: {len(quotes)}\n"
            summary += "Recent quotes:\n"
            for quote in quotes[:3]:  # Get up to 3 recent quotes
                summary += f"- {quote['text']}\n"
        else:
            summary += "No quotes available.\n"
        
        bot_logger.info(f"Generated user summary for user ID: {user_id}")
        bot_logger.debug(f"User summary: {summary}")
        return summary

    async def fetch_stream_chat_data(self, channel_name, user_id, stream_limit=5, message_limit=100):
        # Fetch recent streams
        url_streams = f"https://api.twitch.tv/helix/streams"
        params_streams = {
            "user_id": channel_name,
            "first": stream_limit
        }
        headers = {
            "Client-ID": config.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {await self.get_or_refresh_access_token()}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url_streams, params=params_streams, headers=headers) as response:
                if response.status == 200:
                    stream_data = await response.json()
                    recent_streams = stream_data.get("data", [])
                else:
                    print(f"Failed to fetch recent streams. Status: {response.status}")
                    return []

        # Fetch chat messages for each stream
        all_messages = []
        for stream in recent_streams:
            stream_id = stream["id"]
            url_messages = f"https://api.twitch.tv/helix/chat/messages"
            params_messages = {
                "broadcaster_id": channel_name,
                "user_id": user_id,
                "first": message_limit,
                "stream_id": stream_id
            }
            
            async with session.get(url_messages, params=params_messages, headers=headers) as response:
                if response.status == 200:
                    message_data = await response.json()
                    messages = message_data.get("data", [])
                    all_messages.extend(messages)
                else:
                    print(f"Failed to fetch chat messages for stream {stream_id}. Status: {response.status}")

        return all_messages

    async def fetch_historical_chat_data(self, user_id, channel_name, limit=1000):
        all_messages = []
        pagination = None

        broadcaster_id = await self.get_user_id(channel_name)
        if not broadcaster_id:
            print(f"Could not fetch broadcaster ID for channel: {channel_name}")
            return all_messages

        while len(all_messages) < limit:
            url = "https://api.twitch.tv/helix/chat/messages"
            params = {
                "broadcaster_id": broadcaster_id,
                "user_id": user_id,
                "first": 100  # Max allowed by Twitch API
            }
            if pagination:
                params["after"] = pagination

            headers = {
                "Client-ID": config.TWITCH_CLIENT_ID,
                "Authorization": f"Bearer {await self.get_or_refresh_access_token()}"
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

    async def get_user_id(self, username):
        url = f"https://api.twitch.tv/helix/users?login={username}"
        headers = {
            "Client-ID": config.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {await self.get_or_refresh_access_token()}"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['data']:
                        return data['data'][0]['id']
                print(f"Failed to get user ID for {username}. Status: {response.status}")
        return None

    async def get_user_by_name(self, username):
        clean_name = self.clean_username(username).lower()
        user_id = await self.fetch_user_id_from_twitch_api(clean_name)
        if user_id is None:
            print(f"Failed to fetch user ID for {clean_name}")
            return None
        return {'name': clean_name, 'id': user_id}

    async def fetch_basic_user_info(self, user_id):
        url = f"https://api.twitch.tv/helix/users?id={user_id}"
        headers = {
            "Client-ID": config.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {await self.get_or_refresh_access_token()}"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['data']:
                        return data['data'][0]
        return {"display_name": "Unknown User"}

    def clear_user_summary_cache(self):
        self.generate_user_summary.cache_clear()
        bot_logger.info("User summary cache cleared")

    async def get_all_users(self):
        cursor = self.users_collection.find({}, {'_id': 1, 'username': 1})
        users = await cursor.to_list(length=None)
        return users

    async def update_user_quote(self, quote_id: str, author: str, session=None):
        user_collection = self.db['users']
        await user_collection.update_one(
            {"username": author.lstrip('@').lower()},
            {"$addToSet": {"quotes": quote_id}},
            upsert=True,
            session=session
        )
        # Also update the user's document in the users collection
        await self.bot.user_data_manager.users_collection.update_one(
            {"username": author.lstrip('@').lower()},
            {"$addToSet": {"quotes": quote_id}},
            upsert=True
        )

    def clean_username(self, username):
        """Cleans the username by removing any leading '@' and converting to lowercase."""
        return username.lstrip('@').lower()
















