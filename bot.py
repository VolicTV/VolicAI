import twitchio
from twitchio.ext import commands
import config
from api.quote_manager import QuoteManager
from User.user_data_manager import UserDataManager
import random
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp
from api.ai_manager import AIManager
from api.compatibility_manager import CompatibilityManager
from commands.quote_commands import QuoteCommands
from commands.user_commands import UserCommands
from commands.ai_commands import AICommands
from commands.compatibility_commands import CompatibilityCommands
from utils import bot_logger
import sys
import logging
import io

# Set up logging with UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
bot_logger.addHandler(logging.StreamHandler(sys.stdout))
bot_logger.handlers[0].setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=config.TWITCH_OAUTH_TOKEN, prefix='!', initial_channels=[config.TWITCH_CHANNEL])
        self.mongo_client = AsyncIOMotorClient(config.MONGO_URI)
        self.db = self.mongo_client['twitch_bot_db']
        self.quote_manager = QuoteManager(config.TWITCH_CHANNEL)
        self.user_data_manager = UserDataManager(self.db)
        self.processed_users = set()
        self.bot_messages = set()  # To keep track of messages sent by the bot
        self.ai_manager = AIManager()
        self.quotes_fetched = False
        self.compatibility_manager = CompatibilityManager(self.user_data_manager, self.ai_manager)
        # Add command groups
        self.add_cog(QuoteCommands(self))
        self.add_cog(UserCommands(self))
        self.add_cog(AICommands(self))
        self.add_cog(CompatibilityCommands(self))
        
        # Explicitly register all commands
        self.register_commands()
        
        bot_logger.info("Bot initialized")

    def register_commands(self):
        for command in self.commands.values():
            if command.name not in self.commands:
                self.add_command(command)
        bot_logger.info(f"Registered commands: {', '.join(cmd.name for cmd in self.commands.values())}")

    @property
    def prefix(self):
        return self._prefix

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')
        
        await self.quote_manager.print_all_quote_ids()
        last_quote_number = await self.quote_manager.get_last_quote_number()
        print(f"Last quote number in database: {last_quote_number}")
        
        if not self.quotes_fetched:
            await self.fetch_new_quotes()
            self.quotes_fetched = True


        print("All registered commands:")
        for command_name in self.commands:
            print(f"- {command_name}")

    async def event_message(self, message):
        bot_logger.info(f"Received message: {message.content} from {message.author.name if message.author else 'Unknown'}")
        if message.echo:
            return

        ctx = await self.get_context(message)
        if ctx.prefix is not None:
            try:
                await self.invoke(ctx)
            except commands.CommandNotFound:
                bot_logger.warning(f"Command not found: {ctx.message.content}")
        else:
            await self.handle_regular_message(message)

    async def handle_regular_message(self, message):
        await self.quote_manager.process_message(message)
        if message.author:
            await self.user_data_manager.collect_chat_data(
                message.author.id,
                message.author.name,
                message.content,
                message.timestamp
            )
            
            if message.author.id not in self.processed_users:
                await self.process_first_message(message)
            
            if random.random() < 0.05:  # 5% chance to respond to non-command messages
                context = f"Responding to a chat message: '{message.content}'"
                response = await self.ai_manager.generate_witty_response(message.content, context)
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
        user_summary = await self.user_data_manager.generate_user_summary(message.author.id, message.channel.name)
        print(f"User summary for {message.author.name}: {user_summary}")
        self.processed_users.add(message.author.id)

    def clean_username(self, username):
        return username.lstrip('@')

    async def get_user_by_name(self, username):
        clean_name = self.clean_username(username)
        # In a real implementation, you'd use Twitch API to get the user's ID
        # For now, we'll return a simple object with the cleaned name
        return SimpleUser(clean_name, clean_name.lower())

class SimpleUser:
    def __init__(self, name, id):
        self.name = name
        self.id = id

if __name__ == "__main__":
    bot = Bot()
    bot.run()
