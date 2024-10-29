from twitchio.ext import commands

class CompatibilityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='compatibility', aliases=['compatible', 'compatable', 'compatability', 'ship', 'match'])
    async def compatibility_command(self, ctx: commands.Context, user1: str = None, user2: str = None):
        """Check compatibility between two users including Valorant stats"""
        try:
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

            # Case 2: Self compatibility check
            if user1.lower() == ctx.author.name.lower() and (not user2 or user2.lower() == ctx.author.name.lower()):
                result = await self.bot.compatibility_manager.generate_self_compatibility_response(user1)
                await self.bot.send_message(ctx.channel, result)
                return

            # Case 3: Regular compatibility check
            # Get base compatibility
            base_score = await self.bot.compatibility_manager.calculate_base_compatibility(user1, user2)
            
            # Get Valorant compatibility
            valorant_score = await self.calculate_valorant_compatibility(user1, user2)
            
            # Combine scores
            final_score = (base_score + valorant_score) / 2 if valorant_score else base_score
            
            # Get detailed compatibility report
            result = await self.bot.compatibility_manager.generate_compatibility_report(user1, user2)
            await self.bot.send_message(ctx.channel, result)
            
        except Exception as e:
            command_logger.error(f"Error checking compatibility: {str(e)}")
            await ctx.send(f"@{ctx.author.name}, couldn't check compatibility")

    async def calculate_valorant_compatibility(self, user1: str, user2: str):
        try:
            # Get Valorant data for both users
            riot_id1 = await self.valorant_manager.get_riot_id(user1)
            riot_id2 = await self.valorant_manager.get_riot_id(user2)
            
            valorant_score = 0
            if riot_id1 and riot_id2:
                stats1, _ = await self.valorant_manager.get_player_stats(riot_id1)
                stats2, _ = await self.valorant_manager.get_player_stats(riot_id2)
                
                if stats1 and stats2:
                    # Compare ranks
                    if stats1.get('rank') == stats2.get('rank'):
                        valorant_score += 20
                    
                    # Compare playstyles
                    if stats1.get('most_played_agent') == stats2.get('most_played_agent'):
                        valorant_score += 10
                        
                    # Compare performance levels
                    kd1 = stats1.get('kd_ratio', 0)
                    kd2 = stats2.get('kd_ratio', 0)
                    if abs(kd1 - kd2) < 0.3:
                        valorant_score += 10

            return valorant_score
        except Exception as e:
            print(f"Error calculating Valorant compatibility: {e}")
            return "I'm sorry, I couldn't calculate Valorant compatibility at this time."

    def format_compatibility_response(self, user1: str, user2: str, score: float):
        # Format the compatibility response based on your requirements
        pass
