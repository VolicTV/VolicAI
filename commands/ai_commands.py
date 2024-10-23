from twitchio.ext import commands
import logging
from utils.logger import bot_logger

class AICommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='airesponse')
    async def ai_response(self, ctx: commands.Context, *, question: str = None):
        bot_logger.info(f"AI response requested by {ctx.author.name}")
        user_summary = await self.bot.user_data_manager.generate_user_summary(ctx.author.id, ctx.channel.name)
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
    async def roast_command(self, ctx: commands.Context, target: str):
        if not target:
            await ctx.send(f"@{ctx.author.name}, you need to specify someone to roast!")
            return

        target = target.lstrip('@').lower()

        if target == 'volictv' or target == self.bot.nick.lower():
            # Special case for roasting VolicTV/the bot
            roast = await self.generate_volictv_roast()
        else:
            user = await self.bot.get_user_by_name(target)
            if not user:
                await ctx.send(f"@{ctx.author.name}, I couldn't find the user {target}. Make sure you spelled the name correctly!")
                return

            user_summary = await self.bot.user_data_manager.generate_user_summary(user.id, ctx.channel.name)
            roast = await self.bot.ai_manager.generate_roast(user_summary, target)

        await ctx.send(f"@{target}, {roast}")

    async def generate_volictv_roast(self):
        prompt = """
        Generate a witty and playful roast for VolicTV, the streamer and owner of this channel. 
        The roast should be:
        1. Funny and clever, but not overly mean
        2. Related to streaming, gaming (especially Valorant), or being a Twitch personality
        3. Self-deprecating, as if the bot is roasting its own creator
        4. No more than 4 sentences
        5. Suitable for Twitch chat (can swear)
        6. Include many appropriate emojis

        Example: "VolicTV's Valorant skills are so bad, even his own bot could probably beat him. Maybe he should stick to debugging code instead of defusing bombs! 😂"
        """
        return await self.bot.ai_manager.generate_response("", prompt)

    @commands.command(name='compliment')
    async def compliment_command(self, ctx: commands.Context, target_user: str):
        bot_logger.info(f"Compliment command requested by {ctx.author.name} for {target_user}")
        
        clean_target = self.bot.clean_username(target_user)
        user_obj = await self.bot.get_user_by_name(clean_target)
        
        if user_obj:
            user_id = user_obj.id
        else:
            user_id = clean_target  # Fallback to username if user object not found
        
        user_summary = await self.bot.user_data_manager.generate_user_summary(user_id, clean_target)
        bot_logger.info(f"User summary for {clean_target}: {user_summary}")
        
        prompt = f"""
        Generate a spicy, witty, and slightly edgy compliment for '{clean_target}' based on this user summary: {user_summary}
        The compliment should:
        1. Be clever and unexpected
        2. Include a touch of playful sarcasm or backhanded praise
        3. Reference gaming or Twitch culture if possible
        4. Be slightly flirtatious but not creepy (keep it PG-13)
        5. Include at least one emoji
        6. Be no longer than 300 characters
        Make it memorable and funny!
        """
        compliment = await self.bot.ai_manager.generate_personalized_response(user_summary, prompt)
        await self.bot.send_message(ctx.channel, f"@{clean_target}, {compliment}")
