import datetime
from twitchio.ext import commands
from utils.logger import command_logger
import asyncio
from aiohttp import ClientError
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
from api.ai_manager import AIManager
from datetime import datetime
import logging
from valorant import Client
from collections import Counter

class ValorantCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_manager = bot.ai_manager    

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

    @commands.command(name='valostat')
    async def valorant_stats(self, ctx: commands.Context, *, riot_id: str = None):
        if not riot_id:
            riot_id = await self.bot.valorant_manager.get_riot_id(ctx.author.name)
            if not riot_id:
                await ctx.send(f"@{ctx.author.name}, I don't have your Riot ID stored. Use !confirmupdateriotid to set it.")
                return

        stats = await self.bot.valorant_manager.get_player_stats(riot_id)
        if stats:
            account = stats['account']
            
            response = f"@{ctx.author.name}, here's the basic Valorant info for {riot_id}:\n"
            response += f"Name: {account.name}\n"
            response += f"Tag: {account.tag}\n"
            response += f"Region: {account.region}\n"
            response += f"Account Level: {account.account_level}\n"
            
            await ctx.send(response)
        else:
            await ctx.send(f"@{ctx.author.name}, I couldn't fetch the Valorant stats for {riot_id}. Please check if the Riot ID is correct.")

    @commands.command(name='valomatch')
    async def valorant_recent_match(self, ctx: commands.Context, *, riot_id: str = None):
        if not riot_id:
            riot_id = await self.bot.valorant_manager.get_riot_id(ctx.author.name)
            command_logger.debug(f"Retrieved Riot ID for {ctx.author.name}: {riot_id}")
        
        if not riot_id:
            await ctx.send(f"@{ctx.author.name}, I don't have your Riot ID stored. Use !confirmupdateriotid to set it.")
            return

        command_logger.debug(f"Fetching recent match data for Riot ID: {riot_id}")
        match_data = await self.bot.valorant_manager.get_player_recent_matches(riot_id, num_matches=1)
        
        if match_data and match_data[0]:
            recent_match = match_data[0]
            
            meta = recent_match.get('meta', {})
            stats = recent_match.get('stats', {})
            teams = recent_match.get('teams', {})
            
            response = f"@{ctx.author.name}, here's your most recent Valorant match stats:\n"
            response += f"🗺️ Map: {meta.get('map', {}).get('name', 'Unknown')}\n"
            response += f"🎮 Mode: {meta.get('mode', 'Unknown')}\n"
            response += f"👤 Agent: {stats.get('character', {}).get('name', 'Unknown')}\n"
            response += f"📊 K/D/A: {stats.get('kills', 'N/A')}/{stats.get('deaths', 'N/A')}/{stats.get('assists', 'N/A')}\n"
            response += f"💯 Score: {stats.get('score', 'N/A')}\n"
            
            if meta.get('mode') == 'Deathmatch':
                total_players = teams.get('red', 0) + teams.get('blue', 0)
                response += f"🏆 Placement: {stats.get('rank', 'N/A')}/{total_players}\n"
            else:
                response += f"🔴🔵 Team Score: Red {teams.get('red', 'N/A')} - Blue {teams.get('blue', 'N/A')}\n"
            
            await ctx.send(response)
        else:
            await ctx.send(f"@{ctx.author.name}, I couldn't fetch the recent match data for {riot_id}. The API might be down or the Riot ID might be incorrect.")

    @commands.command(name='valomatches')
    async def valorant_recent_matches(self, ctx: commands.Context, *, args: str = None):
        num_matches = 3  # Default value
        riot_id = None

        if args:
            parts = args.split()
            for part in parts:
                if part.isdigit():
                    num_matches = int(part)
                elif '#' in part:
                    riot_id = part

        if num_matches < 1 or num_matches > 5:
            await ctx.send(f"@{ctx.author.name}, please specify a number of matches between 1 and 5.")
            return

        if not riot_id:
            riot_id = await self.bot.valorant_manager.get_riot_id(ctx.author.name)
            if not riot_id:
                await ctx.send(f"@{ctx.author.name}, I don't have your Riot ID stored. Use !confirmupdateriotid to set it.")
                return

        matches_data = await self.bot.valorant_manager.get_player_recent_matches(riot_id, num_matches=num_matches)
        if matches_data:
            response = f"@{ctx.author.name}, here are your {num_matches} most recent Valorant matches:\n\n"
            
            for i, match in enumerate(matches_data, 1):
                meta = match.get('meta', {})
                stats = match.get('stats', {})
                teams = match.get('teams', {})
                
                match_time = datetime.fromisoformat(meta.get('started_at', '').rstrip('Z'))
                time_ago = (datetime.utcnow() - match_time).days

                response += f"Match {i} ({time_ago} days ago):\n"
                response += f"🗺️ {meta.get('map', {}).get('name', 'Unknown')} | "
                response += f"🎮 {meta.get('mode', 'Unknown')} | "
                response += f"👤 {stats.get('character', {}).get('name', 'Unknown')}\n"
                response += f"📊 K/D/A: {stats.get('kills', 'N/A')}/{stats.get('deaths', 'N/A')}/{stats.get('assists', 'N/A')} | "
                response += f" Score: {stats.get('score', 'N/A')}\n"
                
                if meta.get('mode') == 'Deathmatch':
                    total_players = teams.get('red', 0) + teams.get('blue', 0)
                    response += f"🏆 Position: {teams.get('red', 'N/A')}/{total_players}\n"
                else:
                    response += f"🔴🔵 Team Score: Red {teams.get('red', 'N/A')} - Blue {teams.get('blue', 'N/A')}\n"
                
                response += "\n"

            # Split the response into multiple messages if it's too long
            max_length = 500  # Twitch has a character limit for messages
            messages = []
            while len(response) > max_length:
                split_index = response.rfind('\n\n', 0, max_length)
                if split_index == -1:
                    split_index = response.rfind('\n', 0, max_length)
                if split_index == -1:
                    split_index = max_length
                messages.append(response[:split_index])
                response = response[split_index:].lstrip()
            messages.append(response)
            
            for message in messages:
                await ctx.send(message)
        else:
            await ctx.send(f"@{ctx.author.name}, I couldn't fetch the recent match data for {riot_id}. The API might be down or the Riot ID might be incorrect.")

    @commands.command(name='valocoach')
    async def valorant_coach(self, ctx: commands.Context, *, args: str = None):
        num_matches = 5  # Default value
        riot_id = None

        if args:
            parts = args.split()
            for part in parts:
                if part.isdigit():
                    num_matches = int(part)
                elif '#' in part:
                    riot_id = part

        if num_matches < 1 or num_matches > 10:
            await ctx.send(f"@{ctx.author.name}, please specify a number of matches between 1 and 10.")
            return

        if not riot_id:
            riot_id = await self.bot.valorant_manager.get_riot_id(ctx.author.name)
            if not riot_id:
                await ctx.send(f"@{ctx.author.name}, I don't have your Riot ID stored. Use !confirmupdateriotid to set it.")
                return

        stats, stats_error = await self.bot.valorant_manager.get_player_stats(riot_id)
        matches, matches_error = await self.bot.valorant_manager.get_player_recent_matches(riot_id, num_matches)

        if stats_error or matches_error:
            error_message = stats_error or matches_error
            await ctx.send(f"@{ctx.author.name}, {error_message}")
            return

        if stats and matches:
            analysis = self.analyze_matches(stats, matches)
            
            stats_message = f"📊 Stats for {riot_id} (last {num_matches} matches):\n"
            stats_message += f"K/D/A: {analysis['avg_kda'][0]:.1f}/{analysis['avg_kda'][1]:.1f}/{analysis['avg_kda'][2]:.1f} | "
            stats_message += f"Avg Score: {analysis['avg_score']:.0f} | "
            stats_message += f"Win Rate: {analysis['win_rate']:.1f}% | "
            stats_message += f"Headshot %: {analysis['headshot_percentage']:.1f}%\n"
            stats_message += f"Most Played: {analysis['most_played_agent']} on {analysis['most_played_map']} ({analysis['most_played_mode']})\n"
            stats_message += f"Best Agent: {analysis['best_agent']} | Most Used Weapon: {analysis['most_used_weapon']}"

            await ctx.send(stats_message)

            prompt = f"Act as a Valorant coach. Based on the following player stats from their last {num_matches} matches, provide a brief analysis and some tips for improvement:\n"
            prompt += stats_message + "\n"
            prompt += "Recent Match Details:\n"
            for i, match in enumerate(analysis['match_details'], 1):
                prompt += f"Match {i}: {match['mode']} on {match['map']} as {match['agent']}, KDA: {match['kda']}, Score: {match['score']}, Result: {match['result']}\n"
            prompt += "\nProvide a concise analysis of the player's performance, including strengths, weaknesses, and specific tips for improvement. Consider their best agent, most used weapon, and headshot percentage. Use emojis to separate different points. Keep the response under 350 characters."

            coach_response = await self.ai_manager.generate_response("", prompt)
            analysis_message = f"🎮 Coach's analysis:\n{coach_response}"

            await ctx.send(analysis_message)
        else:
            await ctx.send(f"@{ctx.author.name}, I couldn't analyze the recent matches for {riot_id}. The API might be down or the Riot ID might be incorrect.")

    def analyze_matches(self, stats, matches):
        analysis = {
            "total_matches": len(matches),
            "modes": [],
            "agents": [],
            "maps": [],
            "avg_kda": [0, 0, 0],
            "avg_score": 0,
            "win_rate": 0,
            "headshot_percentage": 0,
            "most_used_weapon": "",
            "best_agent": "",
            "match_details": []
        }

        for match in matches:
            player = next((p for p in match['players']['all_players'] if p['name'] == stats['name'] and p['tag'] == stats['tag']), None)
            if not player:
                continue

            analysis["modes"].append(match['metadata']['mode'])
            analysis["agents"].append(player['character'])
            analysis["maps"].append(match['metadata']['map'])
            
            analysis["avg_kda"][0] += player['stats']['kills']
            analysis["avg_kda"][1] += player['stats']['deaths']
            analysis["avg_kda"][2] += player['stats']['assists']
            analysis["avg_score"] += player['stats']['score']
            analysis["win_rate"] += 1 if player['team'] == match['teams'][player['team'].lower()]['has_won'] else 0
            analysis["headshot_percentage"] += player['stats']['headshots'] / player['stats']['kills'] if player['stats']['kills'] > 0 else 0

            match_detail = {
                "mode": match['metadata']['mode'],
                "map": match['metadata']['map'],
                "agent": player['character'],
                "kda": f"{player['stats']['kills']}/{player['stats']['deaths']}/{player['stats']['assists']}",
                "score": player['stats']['score'],
                "result": "Win" if player['team'] == match['teams'][player['team'].lower()]['has_won'] else "Loss"
            }
            analysis["match_details"].append(match_detail)

        num_matches = len(matches)
        if num_matches > 0:
            analysis["avg_kda"] = [round(k / num_matches, 2) for k in analysis["avg_kda"]]
            analysis["avg_score"] = round(analysis["avg_score"] / num_matches, 0)
            analysis["win_rate"] = round((analysis["win_rate"] / num_matches) * 100, 2)
            analysis["headshot_percentage"] = round((analysis["headshot_percentage"] / num_matches) * 100, 2)

        analysis["most_played_mode"] = max(set(analysis["modes"]), key=analysis["modes"].count)
        analysis["most_played_agent"] = max(set(analysis["agents"]), key=analysis["agents"].count)
        analysis["most_played_map"] = max(set(analysis["maps"]), key=analysis["maps"].count)

        weapons = [kill['killer_weapon_name'] for match in matches for kill in match.get('kills', []) if kill.get('killer_puuid') == player.get('puuid')]
        analysis["most_used_weapon"] = max(set(weapons), key=weapons.count) if weapons else "Unknown"

        agent_stats = Counter(analysis["agents"])
        analysis["best_agent"] = max(agent_stats, key=agent_stats.get)

        return analysis

    @commands.command(name='rank')
    async def valorant_rank(self, ctx: commands.Context, *, riot_id: str = None):
        if not riot_id:
            riot_id = await self.bot.valorant_manager.get_riot_id(ctx.author.name)
            if not riot_id:
                await ctx.send(f"@{ctx.author.name}, I don't have your Riot ID stored. Use !confirmupdateriotid to set it.")
                return

        stats = await self.bot.valorant_manager.get_player_stats(riot_id)
        if stats:
            mmr = stats['mmr']
            if not mmr:
                await ctx.send(f"@{ctx.author.name}, I couldn't fetch the rank for {riot_id}. The API might be down or the Riot ID might be incorrect.")
                return

            response = f"@{ctx.author.name}, here is the rank for {riot_id}:\n"
            response += f"Rank: {mmr.get('currenttierpatched', 'Unranked')}\n"
            response += f"RR: {mmr.get('ranking_in_tier', 'N/A')}\n"
            response += f"Peak Rank: {mmr.get('highest_rank', {}).get('patched_tier', 'N/A')}"
            await ctx.send(response)
        else:
            await ctx.send(f"@{ctx.author.name}, I couldn't fetch the rank for {riot_id}. Please check if the Riot ID is correct (format: name#tag).")
















