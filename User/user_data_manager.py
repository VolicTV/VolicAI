import os
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp
import config
import asyncio
from datetime import datetime, timedelta
from utils.logger import bot_logger
from functools import lru_cache
import time

class UserDataManager:
    def __init__(self, db):
        self.db = db
        self.users_collection = self.db['users']
        self.access_token = None
        self.token_expiry = datetime.now()
        self.ignored_users_file = 'ignored_users.txt'
        self.ignored_users = self.load_ignored_users()
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes

    def load_ignored_users(self):
        ignored_users = set()
        try:
            with open(self.ignored_users_file, 'r') as file:
                for line in file:
                    ignored_users.add(line.strip().lower())
        except FileNotFoundError:
            print(f"Ignored users file not found: {self.ignored_users_file}")
        return ignored_users

    async def collect_chat_data(self, user_id, username, message_content, timestamp):
        bot_logger.info(f"Collecting chat data for user: {username} (ID: {user_id})")
        if username.lstrip('@').lower() in self.ignored_users:
            bot_logger.info(f"Ignoring message from {username} (ID: {user_id})")
            return

        if isinstance(message_content, list):
            message_content = ' '.join(message_content)  # Join list items if content is a list

        user_data = await self.users_collection.find_one({'_id': user_id})
        if not user_data:
            profile_data = await self.fetch_user_profile(user_id)
            historical_messages = await self.fetch_historical_chat_data(user_id, config.TWITCH_CHANNEL)
            user_data = {
                '_id': user_id,
                'username': username,
                'profile': profile_data,
                'messages': [
                    {
                        'content': msg['message'],
                        'timestamp': msg['sent_at']
                    } for msg in historical_messages
                ]
            }
            print(f"Created new user profile for {username} (ID: {user_id}) with {len(historical_messages)} historical messages")
        elif not user_data.get('profile'):
            profile_data = await self.fetch_user_profile(user_id)
            user_data['profile'] = profile_data
            print(f"Added profile data for existing user {username} (ID: {user_id})")

        new_message = {
            'content': message_content,
            'timestamp': timestamp.isoformat()
        }

        result = await self.users_collection.update_one(
            {'_id': user_id},
            {
                '$set': {
                    'username': username,
                    'profile': user_data['profile']
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

        if result.modified_count > 0 or result.upserted_id:
            bot_logger.info(f"Stored message for user {username} (ID: {user_id}): {message_content[:50]}...")
        else:
            bot_logger.warning(f"Failed to store message for user {username} (ID: {user_id})")

    async def fetch_user_profile(self, user_id, max_retries=3):
        for attempt in range(max_retries):
            try:
                access_token = await self.get_valid_access_token()
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
                            await self.refresh_access_token()
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
            return self.cache[user_id]['data']

        user_data = await self.users_collection.find_one({'_id': user_id})
        if user_data:
            self.cache[user_id] = {'data': user_data, 'timestamp': current_time}
        return user_data

    def save_ignored_users(self):
        with open(self.ignored_users_file, 'w') as file:
            for user in self.ignored_users:
                file.write(f"{user}\n")

    async def add_ignored_user(self, username):
        username = username.lstrip('@').lower()
        if username not in self.ignored_users:
            self.ignored_users.add(username)
            self.save_ignored_users()
            return f"Added {username} to the ignored users list."
        return f"{username} is already in the ignored users list."

    async def remove_ignored_user(self, username):
        username = username.lstrip('@').lower()
        if username in self.ignored_users:
            self.ignored_users.remove(username)
            self.save_ignored_users()
            return f"Removed {username} from the ignored users list."
        return f"{username} is not in the ignored users list."

    async def list_ignored_users(self):
        return list(self.ignored_users)

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

    async def get_valid_access_token(self):
        if datetime.now() >= self.token_expiry:
            await self.refresh_access_token()
        return self.access_token

    async def get_user_quotes(self, user_id):
        user_data = await self.users_collection.find_one({'_id': user_id})
        if user_data and 'quotes' in user_data:
            quotes_collection = self.db['quotes']
            return await quotes_collection.find({'_id': {'$in': user_data['quotes']}}).to_list(length=None)
        return []

    @lru_cache(maxsize=100)
    async def generate_user_summary(self, user_id, channel_name):
        bot_logger.info(f"Generating user summary for user ID: {user_id}")
        
        # Try to find the user by ID first
        user_data = await self.users_collection.find_one({'_id': user_id})
        
        # If not found, try to find by username
        if not user_data:
            bot_logger.info(f"User not found by ID, trying username: {user_id}")
            user_data = await self.users_collection.find_one({'username': user_id.lower()})
        
        if user_data:
            message_count = len(user_data.get('messages', []))
            quotes_count = len(user_data.get('quotes', []))
            recent_messages = await self.fetch_recent_messages(user_id, limit=5)
            summary = f"User has sent {message_count} messages and has {quotes_count} quotes. "
            if recent_messages:
                recent_topics = []
                for msg in recent_messages:
                    content = msg['content']
                    if isinstance(content, list):
                        content = ' '.join(content)
                    words = content.split()[:3]
                    recent_topics.append(' '.join(words))
                summary += f"Recent topics: {', '.join(recent_topics)}"
            return summary
        elif channel_name.lower() == 'volictv':
            return "VolicTV is the awesome broadcaster of this channel. Known for their incredible (or not so incredible?) Valorant skills and witty commentary."
        return "No chat history available for this user."

    async def fetch_recent_messages(self, user_id, limit=5):
        user_data = await self.users_collection.find_one({'_id': user_id})
        if user_data and 'messages' in user_data:
            return user_data['messages'][-limit:]
        return []

    async def get_historical_chat_data(self, user_id, limit=10):
        user_data = await self.users_collection.find_one({'_id': user_id})
        if user_data and 'messages' in user_data:
            messages = user_data['messages']
            return messages[-limit:] if len(messages) > limit else messages
        return []

    async def get_user_chat_history(self, user_id, channel_name, limit=50):
        recent_streams = await self.get_recent_streams(channel_name)
        all_messages = []
        
        for stream in recent_streams:
            messages = await self.get_chat_messages(channel_name, user_id, stream["id"])
            all_messages.extend(messages)
            if len(all_messages) >= limit:
                break

        return all_messages[:limit]

    async def get_recent_streams(self, channel_name, limit=5):
        url = f"https://api.twitch.tv/helix/streams"
        params = {
            "user_id": channel_name,
            "first": limit
        }
        headers = {
            "Client-ID": config.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {await self.get_valid_access_token()}"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                else:
                    print(f"Failed to fetch recent streams. Status: {response.status}")
                    return []

    async def get_chat_messages(self, channel_name, user_id, stream_id):
        url = f"https://api.twitch.tv/helix/chat/messages"
        params = {
            "broadcaster_id": channel_name,
            "user_id": user_id,
            "first": 100  # Adjust as needed
        }
        if stream_id:
            params["stream_id"] = stream_id
        headers = {
            "Client-ID": config.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {await self.get_valid_access_token()}"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                else:
                    print(f"Failed to fetch chat messages. Status: {response.status}")
                    return []

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
                "Authorization": f"Bearer {await self.get_valid_access_token()}"
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
            "Authorization": f"Bearer {await self.get_valid_access_token()}"
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
        # First, try to find the user by their current username
        user = await self.users_collection.find_one({"username": username})
        
        if user:
            return user
        
        # If not found, try to find by checking the 'login' field in the profile
        user = await self.users_collection.find_one({"profile.login": username.lower()})
        
        if user:
            return user
        
        # If still not found, fetch the user data from Twitch API
        user_id = await self.get_user_id(username)
        if user_id:
            user_data = await self.fetch_user_profile(user_id)
            if user_data:
                # Store the fetched user data in the database
                await self.users_collection.update_one(
                    {"_id": user_id},
                    {"$set": {"profile": user_data, "username": username}},
                    upsert=True
                )
                return await self.users_collection.find_one({"_id": user_id})
        
        return None

