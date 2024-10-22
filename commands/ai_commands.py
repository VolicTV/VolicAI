from twitchio.ext import commands

class AICommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='airesponse')
    async def ai_response(self, ctx: commands.Context, *, question: str = None):
        user_summary = await self.bot.user_data_manager.generate_user_summary(ctx.author.id, ctx.channel.name)
        
        if "No chat history available" in user_summary:
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
    async def roast_command(self, ctx: commands.Context, *, target: str = None):
        if not target:
            await self.bot.send_message(ctx.channel, "Give me a target to roast, or are you too scared?")
            return
        
        clean_target = self.bot.clean_username(target)
        
        if clean_target.lower() == self.bot.nick.lower():
            await self.bot.send_message(ctx.channel, "Nice try, but I'm too awesome to roast myself.")
        elif clean_target.lower() == ctx.author.name.lower():
            await self.bot.send_message(ctx.channel, f"@{ctx.author.name}, roasting yourself? That's my job!")
        else:
            target_user = await self.bot.get_user_by_name(clean_target)
            if target_user:
                user_summary = await self.bot.user_data_manager.generate_user_summary(target_user.id, clean_target)
                prompt = f"Generate a witty, playful roast for the user '{clean_target}'. Keep it light-hearted and not too mean. Include an appropriate emoji."
                roast = await self.bot.ai_manager.generate_personalized_response(user_summary, prompt)
                await self.bot.send_message(ctx.channel, f"@{clean_target}, {roast}")
            else:
                await self.bot.send_message(ctx.channel, f"I can't find {clean_target} to roast. Are they hiding?")

    @commands.command(name='compliment')
    async def compliment_command(self, ctx: commands.Context, *, target: str = None):
        if not target:
            target = ctx.author.name
        
        clean_target = self.bot.clean_username(target)
        target_user = await self.bot.get_user_by_name(clean_target)
        if target_user:
            prompt = f"Generate a witty, personalized compliment for the user '{clean_target}'. Make it clever and uplifting. Include an appropriate emoji."
            compliment = await self.bot.generate_personalized_response(target_user.id, clean_target, prompt)
            await self.bot.send_message(ctx.channel, f"@{clean_target}, {compliment}")
        else:
            await self.bot.send_message(ctx.channel, f"I can't find {clean_target} to compliment. They must be too awesome to be seen!")
