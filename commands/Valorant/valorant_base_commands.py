from twitchio.ext import commands
from typing import Optional, Tuple, Dict, List
from datetime import datetime

from api.Valorant.valorant_exceptions import (
    ValorantError,
    InvalidRiotIDError,
    PlayerNotFoundError,
    RateLimitError
)
from utils.logger import command_logger

class ValorantBaseCommand:
    """Base class for Valorant commands providing common functionality"""
    
    def __init__(self, bot):
        """Initialize base command with bot instance"""
        self.bot = bot
        self.valorant_manager = bot.valorant_manager

    async def get_riot_id(self, ctx: commands.Context, provided_id: Optional[str] = None) -> Optional[str]:
        """Get Riot ID either from provided argument or stored user data"""
        try:
            if provided_id:
                try:
                    # Will raise InvalidRiotIDError if format is invalid
                    return await self.valorant_manager.validate_riot_id(provided_id)
                except InvalidRiotIDError:
                    await ctx.send(f"@{ctx.author.name}, invalid Riot ID format. Must be name#tag")
                    return None
                    
            # Try to get stored Riot ID
            riot_id = await self.valorant_manager.get_riot_id(ctx.author.name)
            if not riot_id:
                await ctx.send(
                    f"@{ctx.author.name}, no Riot ID stored. "
                    f"Use !setid <riot_id> or provide Riot ID with command"
                )
                return None
                
            return riot_id
            
        except Exception as e:
            command_logger.error(f"Error in get_riot_id: {str(e)}")
            await self.handle_error(ctx, "getting Riot ID")
            return None

    async def handle_error(self, ctx: commands.Context, action: str):
        """Handle errors consistently across commands"""
        await ctx.send(
            f"@{ctx.author.name}, an error occurred while {action}. Please try again later."
        )

    async def send_paginated_response(self, ctx: commands.Context, response: str, 
                                    max_length: int = 500) -> None:
        """Split and send long messages in chunks"""
        messages = []
        while response:
            if len(response) <= max_length:
                messages.append(response)
                break
                
            split_index = response.rfind('\n\n', 0, max_length)
            if split_index == -1:
                split_index = response.rfind('\n', 0, max_length)
            if split_index == -1:
                split_index = max_length

            messages.append(response[:split_index])
            response = response[split_index:].lstrip()

        for message in messages:
            await ctx.send(message)