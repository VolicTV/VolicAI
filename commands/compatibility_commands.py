from twitchio.ext import commands

class CompatibilityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='compatibility', aliases=['compatible', 'compatable', 'compatability', 'ship', 'match'])
    async def compatibility_command(self, ctx: commands.Context, user1: str = None, user2: str = None):
        # Case 1: No arguments provided
        if not user1:
            usage_message = "❓ How to use the compatibility command:\n"
            usage_message += "• Compare yourself with someone else: !compatibility @theirusername\n"
            usage_message += "• Compare two other users: !compatibility @user1 @user2\n"
            usage_message += "Remember, usernames are case-sensitive and the '@' symbol is optional!"
            await self.bot.send_message(ctx.channel, usage_message)
            return

        # Clean usernames
        user1 = self.bot.clean_username(user1)
        user2 = self.bot.clean_username(user2) if user2 else ctx.author.name

        # Case 4: Both arguments are the user's name
        if user1.lower() == ctx.author.name.lower() and user2.lower() == ctx.author.name.lower():
            result = await self.bot.compatibility_manager.generate_self_compatibility_response(user1)
            await self.bot.send_message(ctx.channel, result)
            return

        # Case 5: First argument is the user's name
        if user1.lower() == ctx.author.name.lower():
            result = await self.bot.compatibility_manager.generate_self_compatibility_response(user1)
            await self.bot.send_message(ctx.channel, result)
            return

        # Case 2 & 3: One or both arguments provided
        result = await self.bot.compatibility_manager.generate_compatibility_report(user1, user2)
        await self.bot.send_message(ctx.channel, result)
