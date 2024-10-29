import twitchio
from twitchio.ext import commands
import config
import json
import os
import logging
import sys
import io
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp
import random
import asyncio

# Local imports
from api.quote_manager import QuoteManager
from User.user_data_manager import UserDataManager
from api.ai_manager import AIManager
from api.compatibility_manager import CompatibilityManager
from commands.quote_commands import QuoteCommands
from commands.user_commands import UserCommands
from commands.ai_commands import AICommands
from commands.compatibility_commands import CompatibilityCommands
from api.Valorant.valorant_manager import ValorantManager
from commands.Valorant.valorant_commands import ValorantCommands
from utils.logger import bot_logger

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot_debug.log')  # This will also save logs to a file
    ]
)

# Define UnicodeStreamHandler
class UnicodeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = io.TextIOWrapper(self.stream.buffer, encoding='utf-8', errors='ignore')
            stream.write(msg + self.terminator)
            stream.detach()
            self.flush()
        except Exception:
            self.handleError(record)

# Replace the default handler with the UnicodeStreamHandler
logging.getLogger().handlers = [UnicodeStreamHandler(sys.stdout)]

class Bot(commands.Bot):

    def __init__(self):
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Initialize ignored_users.json if it doesn't exist
        if not os.path.exists('data/ignored_users.json'):
            with open('data/ignored_users.json', 'w') as f:
                json.dump([], f)
        
        # Initialize database connection
        self.db = AsyncIOMotorClient(config.MONGO_URI)
        
        # Initialize managers
        self.quote_manager = QuoteManager(self.db)
        self.user_data_manager = UserDataManager(
            self.db['users'],
            ignored_users_file='data/ignored_users.json'
        )
        self.valorant_manager = ValorantManager(self.db)
        self.ai_manager = AIManager(self, self.valorant_manager)
        self.compatibility_manager = CompatibilityManager(
            user_data_manager=self.user_data_manager,
            ai_manager=self.ai_manager
        )
        
        # Track processed users
        self.processed_users = set()
        
        # Initialize bot with Twitch credentials
        super().__init__(
            token=config.TMI_TOKEN,
            prefix='!',
            initial_channels=[config.TWITCH_CHANNEL]
        )
        
        # Add commands immediately after initialization
        self.add_cog(QuoteCommands(self))
        self.add_cog(UserCommands(self))
        self.add_cog(AICommands(self))
        self.add_cog(CompatibilityCommands(self))
        self.add_cog(ValorantCommands(self))

    async def event_ready(self):
        """Called once when the bot goes online."""
        print(f"Logged in as | {self.nick}")
        print(f"User id is | {self.user_id}")
        
        try:
            await self.quote_manager.print_all_quote_ids()
        except Exception as e:
            print(f"Error printing quote IDs: {str(e)}")
            logging.error(f"Error in event_ready: {str(e)}")

    async def event_message(self, message):
        if message.author is None:
            bot_logger.warning("Received a message with no author.")
            return

        author_name = message.author.name if message.author else "Unknown"
        bot_logger.info(f"Received message: {message.content} from {author_name}")

        await self.user_data_manager.update_user_chat_data(
            message.author.id, message.author.name, message.content, message.timestamp
        )

        if message.echo:
            return

        ctx = await self.get_context(message)
        if ctx.prefix is not None:
            try:
                await self.invoke(ctx)
            except commands.CommandNotFound:
                pass
        else:
            await self.handle_regular_message(message)

    async def handle_regular_message(self, message):
        bot_logger.info(f"Handling regular message from {message.author.name}")
        await self.quote_manager.process_message(message)
        if message.author:
            await self.user_data_manager.update_user_chat_data(
                message.author.id,
                message.author.name,
                message.content,
                message.timestamp
            )
            
            if message.author.id not in self.processed_users:
                await self.process_first_message(message)
            
            if random.random() < 0.01:  # 5% chance to respond to non-command messages
                context = f"Responding to a chat message: '{message.content}'"
                response = await self.ai_manager.generate_enhanced_personalized_response(message.content, context)
                await self.send_message(message.channel.name, f"@{message.author.name}, {response}")

    async def send_message(self, channel, content):
        if isinstance(channel, str):
            channel_obj = self.get_channel(channel)
            if channel_obj is None:
                try:
                    channel_obj = await self.fetch_channel(channel)
                except Exception as e:
                    print(f"Error fetching channel {channel}: {e}")
                    return
        else:
            channel_obj = channel

        if channel_obj:
            await channel_obj.send(content)
        else:
            print(f"Error: Channel {channel} not found")

    async def fetch_new_quotes(self):
        await self.quote_manager.fetch_new_quotes(self, max_checks=200)

    async def process_first_message(self, message):
        user_summary = await self.user_data_manager.get_user_summary(message.author.id, message.channel.name)
        print(f"User summary for {message.author.name}: {user_summary}")
        self.processed_users.add(message.author.id)

    def clean_username(self, username):
        return username.lstrip('@')

    async def get_user_by_name(self, username):
        clean_name = self.clean_username(username)
        # Use Twitch API to get the user's actual ID
        user_id = await self.user_data_manager.get_user_info_by_name_or_id(clean_name)
        return clean_name, user_id

    async def background_update_task(self):
        while True:
            await self.update_local_data()
            await asyncio.sleep(300)  # Run every 5 minutes

    async def update_local_data(self):
        # Update frequently accessed data
        await self.quote_manager.update_quote_cache()
        await self.user_data_manager.update_user_cache()

    async def fetch_user_id_from_twitch_api(self, username):
        url = f"https://api.twitch.tv/helix/users?login={username}"
        headers = {
            "Client-ID": config.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {await self.user_data_manager.ensure_valid_access_token()}"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['data']:
                        return data['data'][0]['id']
                print(f"Failed to get user ID for {username}. Status: {response.status}")
        return None

def main():
    bot = Bot()
    bot.run()

if __name__ == "__main__":
    main()
