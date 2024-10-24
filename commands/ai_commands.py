from twitchio.ext import commands
import logging
from utils.logger import bot_logger

class AICommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='airesponse')
    async def ai_response(self, ctx: commands.Context, *, question: str = None):
        bot_logger.info(f"AI response requested by {ctx.author.name}")
        user_summary = await self.bot.user_data_manager.get_user_summary(ctx.author.id, ctx.channel.name)
        bot_logger.info(f"User summary for {ctx.author.name}: {user_summary}")
        
        if "No chat history available" in user_summary:
            bot_logger.warning(f"No chat history available for {ctx.author.name}")
            await self.bot.send_message(ctx.channel, f"@{ctx.author.name}, I don't have enough information about you yet. Chat more and try again later!")
            return

        if question:
            prompt = f"The user asks: {question}\nPlease provide a concise response based on their profile and chat history."
        else:
            prompt = f"Generate a brief personalized greeting for the user based on their profile and chat history."

        ai_response = await self.bot.ai_manager.generate_response(user_summary, prompt)
        
        # Truncate the response if it's too long
        max_response_length = 450  # Leave some room for the username and formatting
        if len(ai_response) > max_response_length:
            ai_response = ai_response[:max_response_length] + "..."

        await self.bot.send_message(ctx.channel, f"@{ctx.author.name}, {ai_response}")

    @commands.command(name='roast')
    async def roast_command(self, ctx: commands.Context, target: str = None):
        if not target:
            target = ctx.author.name

        target = target.lstrip('@').lower()

        user_name, user_id = await self.bot.get_user_by_name(target)
        if not user_id:
            await ctx.send(f"@{ctx.author.name}, I couldn't find the user {target}. Are you sure they exist?")
            return

        bot_logger.info(f"Generating roast for target: {target}, User ID: {user_id}")
        user_data = await self.bot.user_data_manager.get_user_data(user_id)
        bot_logger.info(f"User data retrieved for {target}")

        roast = await self.bot.ai_manager.generate_roast(user_data, target)
        await ctx.send(f"@{target}, {roast}")
    
    @commands.command(name='compliment')
    async def compliment_command(self, ctx: commands.Context, target_user: str = None):
        if not target_user:
            target_user = ctx.author.name

        target_user = self.bot.clean_username(target_user)

        user_name, user_id = await self.bot.get_user_by_name(target_user)
        if not user_id:
            await ctx.send(f"@{ctx.author.name}, I couldn't find the user {target_user}. Are you sure they exist?")
            return

        bot_logger.info(f"Compliment command requested by {ctx.author.name} for {target_user}")

        user_summary = await self.bot.user_data_manager.get_user_summary(user_id, target_user)
        bot_logger.info(f"User summary for {target_user}: {user_summary}")

        compliment = await self.bot.ai_manager.generate_compliment(user_summary, target_user)
        await ctx.send(f"@{target_user}, {compliment}")

    @commands.command(name='about')
    async def about_command(self, ctx: commands.Context):
        about_message = (
            "🤖 Hello! I'm VolicAI, an AI-powered Twitch bot designed to enhance your chat experience. "
            "I can manage quotes, provide AI-driven interactions, track Valorant stats, and more! "
            "Use commands like !quote, !valocoach, !rank, and !roast to interact with me. "
            "I'm here to make the stream more engaging and fun! 🎮"
        )
        await ctx.send(about_message)

    @commands.command(name='commands')
    async def list_commands(self, ctx: commands.Context):
        command_list = [
            "!quote - Manage quotes",
            "!quotesearch - Search quotes",
            "!quotecount - Your quote count",
            "!airesponse - AI response",
            "!roast - Playful roast",
            "!compliment - Get a compliment",
            "!compatibility - Check compatibility",
            "!setriotid - Set Riot ID",
            "!valorantstats - Valorant stats",
            "!valocoach - Coaching tips",
            "!rank - Check rank",
            "!about - About the bot",
            "!rizz - Get a rizz line",
            "!commands - List all commands"
        ]

        commands_message = "📜 Commands: " + " | ".join(command_list)
        await ctx.send(commands_message)

    @commands.command(name='rizz')
    async def rizz_command(self, ctx: commands.Context, target_user: str = None):
        if not target_user:
            target_user = ctx.author.name

        target_user = self.bot.clean_username(target_user)

        user_name, user_id = await self.bot.get_user_by_name(target_user)
        if not user_id:
            await ctx.send(f"@{ctx.author.name}, I couldn't find the user {target_user}. Are you sure they exist?")
            return

        bot_logger.info(f"Rizz command requested by {ctx.author.name} for {target_user}")

        user_summary = await self.bot.user_data_manager.get_user_summary(user_id, target_user)
        bot_logger.info(f"User summary for {target_user}: {user_summary}")

        rizz_message = await self.bot.ai_manager.generate_rizz(user_summary, target_user)
        await ctx.send(f"@{target_user}, {rizz_message}")






