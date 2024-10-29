from twitchio.ext import commands
from typing import Optional
from datetime import datetime
import asyncio
from api.Valorant.valorant_formatter import ResponseFormatter
from .valorant_base_commands import ValorantBaseCommand
from api.Valorant.valorant_exceptions import ValorantError
from utils.valorant.valorant_analysis import MatchAnalyzer
from utils.logger import command_logger
import aiohttp

class ValorantCommands(commands.Cog, ValorantBaseCommand):
    def __init__(self, bot):
        commands.Cog.__init__(self)  # Initialize Cog
        ValorantBaseCommand.__init__(self, bot)  # Initialize ValorantBaseCommand with bot
        self.bot = bot
        self.valorant_manager = bot.valorant_manager

    @commands.command(name='setriotid', aliases=['setid'])
    async def set_riot_id(self, ctx: commands.Context, *, riot_id: str):
        """Set a user's Riot ID for Valorant tracking"""
        try:
            # Basic validation of Riot ID format
            if '#' not in riot_id:
                await ctx.send(f"@{ctx.author.name}, please provide your Riot ID in the format: Name#Tag")
                return

            # Try to set the Riot ID
            result = await self.valorant_manager.set_riot_id(ctx.author.name, riot_id)
            
            if result:
                await ctx.send(f"@{ctx.author.name}, successfully set your Riot ID to: {riot_id}")
            else:
                await ctx.send(f"@{ctx.author.name}, couldn't verify that Riot ID. Please check if it's correct.")
                
        except aiohttp.ClientConnectorError:
            error_msg = f"@{ctx.author.name}, couldn't connect to Riot servers right now. Please try again later."
            command_logger.error(f"Network error setting Riot ID for {ctx.author.name}: Connection failed")
            await ctx.send(error_msg)
        except Exception as e:
            command_logger.error(f"Error setting Riot ID: {str(e)}")
            await ctx.send(f"@{ctx.author.name}, something went wrong setting your Riot ID. Please try again later.")

    @commands.command(name='rank')
    async def get_rank(self, ctx: commands.Context, *, riot_id: Optional[str] = None):
        """Get player's competitive rank"""
        riot_id = await self.get_riot_id(ctx, riot_id)
        if not riot_id:
            return

        try:
            stats, error = await self.valorant_manager.get_player_stats(riot_id)
            if error:
                await ctx.send(f"@{ctx.author.name}, {error}")
                return

            response = ResponseFormatter.format_stats(riot_id, stats)
            await ctx.send(response)
            
        except ValorantError as e:
            await ctx.send(f"@{ctx.author.name}, {str(e)}")
        except Exception as e:
            command_logger.error(f"Error in get_rank: {str(e)}")
            await self.handle_error(ctx, "fetching rank")

    @commands.command(name='matches', aliases=['history'])
    async def get_matches(self, ctx: commands.Context, *, riot_id: Optional[str] = None):
        """Get player's recent matches"""
        try:
            riot_id = await self.get_riot_id(ctx, riot_id)
            if not riot_id:
                return

            # Get account info first
            name, tag = riot_id.split('#')
            account = await self.valorant_manager.client.get_account_by_riot_id(name, tag)
            
            if not account:
                await ctx.send(f"@{ctx.author.name}, couldn't find that account.")
                return

            # Get recent matches
            matches = await self.valorant_manager.client.get_recent_matches(account['puuid'])
            
            if not matches:
                await ctx.send(f"@{ctx.author.name}, no recent matches found.")
                return

            # Format match history
            recent_match = matches[0]  # Most recent match
            map_name = recent_match.get('matchInfo', {}).get('mapId', 'Unknown Map')
            game_mode = recent_match.get('matchInfo', {}).get('queueId', 'Unknown Mode')
            
            response = f"@{ctx.author.name}, Last match: {map_name} ({game_mode}). "
            response += f"Total matches found: {len(matches)}."
            
            await ctx.send(response)

        except Exception as e:
            command_logger.error(f"Error getting matches: {str(e)}")
            await ctx.send(f"@{ctx.author.name}, something went wrong getting match history.")

    @commands.command(name='stats')
    async def get_stats(self, ctx: commands.Context, *, riot_id: Optional[str] = None):
        """Get player's detailed stats"""
        riot_id = await self.get_riot_id(ctx, riot_id)
        if not riot_id:
            return

        try:
            stats, error = await self.valorant_manager.get_player_stats(riot_id)
            if error:
                await ctx.send(f"@{ctx.author.name}, {error}")
                return

            matches = await self.valorant_manager.get_match_history(riot_id, 5)
            response = ResponseFormatter.format_stats(riot_id, {
                "stats": stats,
                "matches": matches
            })
            await self.send_paginated_response(ctx, response)
            
        except ValorantError as e:
            await ctx.send(f"@{ctx.author.name}, {str(e)}")
        except Exception as e:
            command_logger.error(f"Error in get_stats: {str(e)}")
            await self.handle_error(ctx, "fetching stats")

    @commands.command(name='valorantstats')
    async def valorant_stats(self, ctx: commands.Context, *, riot_id: Optional[str] = None):
        """Comprehensive view of Valorant stats"""
        riot_id = await self.get_riot_id(ctx, riot_id)
        if not riot_id:
            return

        try:
            # Get both stats and recent matches
            stats, error = await self.valorant_manager.get_player_stats(riot_id)
            if error:
                await ctx.send(f"@{ctx.author.name}, {error}")
                return

            matches = await self.valorant_manager.get_match_history(riot_id, 5)
            
            # Format comprehensive response
            stats_response = ResponseFormatter.format_stats(riot_id, stats)
            matches_response = ResponseFormatter.format_match_history(
                ctx.author.name,
                riot_id,
                matches[:3] if matches else [],
                3
            )
            
            # Send paginated response
            await self.send_paginated_response(ctx, f"{stats_response}\n\n{matches_response}")
            
        except ValorantError as e:
            await ctx.send(f"@{ctx.author.name}, {str(e)}")
        except Exception as e:
            command_logger.error(f"Error in valorant_stats: {str(e)}")
            await self.handle_error(ctx, "fetching Valorant stats")

    @commands.command(name='valomatch')
    async def last_match(self, ctx: commands.Context, *, riot_id: Optional[str] = None):
        """Detailed info about the last match"""
        riot_id = await self.get_riot_id(ctx, riot_id)
        if not riot_id:
            return

        try:
            matches = await self.valorant_manager.get_match_history(riot_id, 1)
            if not matches:
                await ctx.send(f"@{ctx.author.name}, no recent matches found for {riot_id}")
                return

            # Format detailed match response
            response = ResponseFormatter.format_match_details(riot_id, matches[0])
            await ctx.send(response)
            
        except ValorantError as e:
            await ctx.send(f"@{ctx.author.name}, {str(e)}")
        except Exception as e:
            command_logger.error(f"Error in last_match: {str(e)}")
            await self.handle_error(ctx, "fetching last match")

    @commands.command(name='valocoach')
    async def get_coaching_tips(self, ctx: commands.Context, *, riot_id: Optional[str] = None):
        """Get personalized coaching tips"""
        riot_id = await self.get_riot_id(ctx, riot_id)
        if not riot_id:
            return

        try:
            # Get comprehensive data for analysis
            stats, error = await self.valorant_manager.get_player_stats(riot_id)
            if error:
                await ctx.send(f"@{ctx.author.name}, {error}")
                return

            matches = await self.valorant_manager.get_match_history(riot_id, 10)
            if not matches:
                await ctx.send(f"@{ctx.author.name}, no recent matches found to analyze")
                return

            # Use MatchAnalyzer for detailed analysis
            analysis = MatchAnalyzer.analyze_matches(stats, matches)
            if not analysis:
                await ctx.send(f"@{ctx.author.name}, couldn't analyze your matches")
                return

            # Format and send coaching tips
            response = ResponseFormatter.format_coaching_tips(analysis)
            await self.send_paginated_response(ctx, response)
            
        except ValorantError as e:
            await ctx.send(f"@{ctx.author.name}, {str(e)}")
        except Exception as e:
            command_logger.error(f"Error in get_coaching_tips: {str(e)}")
            await self.handle_error(ctx, "generating coaching tips")
















