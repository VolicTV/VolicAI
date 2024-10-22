from twitchio.ext import commands

class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ignorelist')
    async def ignore_list(self, ctx: commands.Context):
        ignored_users = await self.bot.user_data_manager.list_ignored_users()
        if ignored_users:
            await self.bot.send_message(ctx.channel, f"Ignored users: {', '.join(ignored_users)}")
        else:
            await self.bot.send_message(ctx.channel, "No users are currently being ignored.")

    @commands.command(name='ignore')
    async def ignore_user(self, ctx: commands.Context, username: str):
        if not ctx.author.is_mod and not ctx.author.is_broadcaster:
            await self.bot.send_message(ctx.channel, "Only moderators and the broadcaster can use this command.")
            return
        result = await self.bot.user_data_manager.add_ignored_user(username)
        await self.bot.send_message(ctx.channel, result)

    @commands.command(name='unignore')
    async def unignore_user(self, ctx: commands.Context, username: str):
        if not ctx.author.is_mod and not ctx.author.is_broadcaster:
            await self.bot.send_message(ctx.channel, "Only moderators and the broadcaster can use this command.")
            return
        result = await self.bot.user_data_manager.remove_ignored_user(username)
        await self.bot.send_message(ctx.channel, result)
