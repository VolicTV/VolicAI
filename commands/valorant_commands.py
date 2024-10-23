from twitchio.ext import commands
from utils.logger import command_logger
import asyncio
from aiohttp import ClientError

class ValorantCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='setriotid')
    async def set_riot_id(self, ctx: commands.Context, *, riot_id: str):
        command_logger.info(f"Set Riot ID command used by {ctx.author.name}")
        existing_riot_id = await self.bot.valorant_manager.get_riot_id(ctx.author.name)
        
        if existing_riot_id:
            await ctx.send(f"@{ctx.author.name}, you already have a Riot ID set ({existing_riot_id}). Are you sure you want to update it? Use !confirmupdateriotid <new_riot_id> to confirm.")
            return

        try:
            success = await self.bot.valorant_manager.store_riot_id(ctx.author.name, riot_id)
            if success:
                await ctx.send(f"@{ctx.author.name}, your Riot ID has been set to {riot_id}.")
            else:
                await ctx.send(f"@{ctx.author.name}, there was an error setting your Riot ID. Please try again later.")
        except Exception as e:
            command_logger.error(f"Error setting Riot ID for {ctx.author.name}: {str(e)}")
            await ctx.send(f"@{ctx.author.name}, an unexpected error occurred. Please try again later.")

    @commands.command(name='confirmupdateriotid')
    async def confirm_update_riot_id(self, ctx: commands.Context, *, riot_id: str = None):
        command_logger.info(f"Confirm update Riot ID command used by {ctx.author.name}")
        if not riot_id:
            await ctx.send(f"@{ctx.author.name}, please provide your new Riot ID. Usage: !confirmupdateriotid <new_riot_id>")
            return
        try:
            success, message = await self.bot.valorant_manager.store_riot_id(ctx.author.name, riot_id)
            if success:
                await ctx.send(f"@{ctx.author.name}, your Riot ID has been updated to {riot_id}.")
            else:
                await ctx.send(f"@{ctx.author.name}, there was an error updating your Riot ID: {message}")
        except Exception as e:
            command_logger.error(f"Error updating Riot ID for {ctx.author.name}: {str(e)}")
            await ctx.send(f"@{ctx.author.name}, an unexpected error occurred: {str(e)}. Please try again later.")

    @commands.command(name='valostats')
    async def valorant_stats(self, ctx: commands.Context, *, username: str = None):
        command_logger.info(f"Valorant stats command used by {ctx.author.name}")
        target_user = username or ctx.author.name
        try:
            riot_id = await self.bot.valorant_manager.get_riot_id(target_user)

            if not riot_id:
                await ctx.send(f"@{ctx.author.name}, no Riot ID found for {target_user}. Use !setriotid to set your Riot ID.")
                return

            try:
                stats, error_message = await self.bot.valorant_manager.fetch_valorant_stats(riot_id)
            except Exception as e:
                command_logger.error(f"Error fetching stats for {target_user}: {str(e)}")
                await ctx.send(f"@{ctx.author.name}, there was an error fetching the stats. Please try again later.")
                return

            if stats:
                response = (f"Valorant stats for {target_user} (Riot ID: {riot_id}): "
                            f"Rank: {stats['rank']}, K/D: {stats['kd_ratio']}, "
                            f"Win Rate: {stats['win_rate']}, Avg Score: {stats['avg_score']}, "
                            f"Headshot %: {stats['headshot_pct']}")
                await ctx.send(response[:500])  # Truncate to 500 characters
            else:
                await ctx.send(f"@{ctx.author.name}, couldn't fetch Valorant stats for {target_user}. Please try again later.")
        except Exception as e:
            command_logger.error(f"Unexpected error in valorant_stats command: {str(e)}")
            await ctx.send(f"@{ctx.author.name}, an unexpected error occurred. Please try again later.")
