from twitchio.ext import commands
import random
from utils import command_logger

class QuoteCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='quote')
    async def quote_command(self, ctx: commands.Context):
        command_logger.info(f"Quote command used by {ctx.author.name}")
        quote = await self.bot.quote_manager.get_random_quote()
        if quote:
            core_response = f"📜 Quote #{quote['_id']}: \"{quote['text']}\" - {quote['author']}"
            await self.bot.send_message(ctx.channel.name, core_response)
            
            context = "Responding to a request for a random quote"
            witty_response = await self.bot.ai_manager.generate_enhanced_personalized_response(core_response, context)
            if witty_response and witty_response != core_response:
                await self.bot.send_message(ctx.channel.name, f"💬 {witty_response}")
        else:
            core_response = "📭 No quotes found."
            await self.bot.send_message(ctx.channel.name, core_response)
            
            context = "No quotes available in the database"
            witty_response = await self.bot.ai_manager.generate_enhanced_personalized_response(core_response, context)
            if witty_response and witty_response != core_response:
                await self.bot.send_message(ctx.channel.name, f"💬 {witty_response}")

    @commands.command(name='quoteid')
    async def quote_id_command(self, ctx: commands.Context, quote_id: str):
        quote = await self.bot.quote_manager.get_quote_by_id(quote_id)
        if quote:
            await self.bot.send_message(ctx.channel, f"Quote #{quote['_id']}: {quote['text']} - {quote['author']}")
        else:
            await self.bot.send_message(ctx.channel, f"No quote found with ID {quote_id}.")

    @commands.command(name='quotesearch')
    async def quote_search_command(self, ctx: commands.Context, *search_terms):
        if not search_terms:
            await self.bot.send_message(ctx.channel.name, "Please provide a search term.")
            return

        search_term = ' '.join(search_terms)
        quotes = await self.bot.quote_manager.search_quotes(search_term)
        
        if quotes:
            random_quote = random.choice(quotes)
            core_response = f"📜 Quote #{random_quote['_id']}: \"{random_quote['text']}\" - {random_quote['author']}"
            context = f"Responding to a quote search for '{search_term}'"
            witty_response = await self.bot.ai_manager.generate_enhanced_personalized_response(core_response, context)
            
            # Format the response
            formatted_response = f"{core_response}\n💬 {witty_response}"
            
            # Ensure the response fits within Twitch's character limit
            if len(formatted_response) > 500:  # Twitch has a 500 character limit
                formatted_response = formatted_response[:497] + "..."
            
            await self.bot.send_message(ctx.channel.name, formatted_response)
        else:
            await self.bot.send_message(ctx.channel.name, f"🔍 No quotes found containing '{search_term}'.")

    @commands.command(name='quotecount')
    async def quote_count_command(self, ctx: commands.Context):
        author = ctx.author.name
        count = await self.bot.quote_manager.count_quotes_by_author(f'@{author}')
        total_quotes, avg_quotes = await self.bot.quote_manager.get_quote_statistics()
        
        emoji = "📚" if count > 0 else "📭"
        core_response = f"{emoji} @{author}, you have {count} quote(s) in the database!"
        
        comparison = ""
        if count > avg_quotes:
            comparison = f"You're above average! The mean is {avg_quotes:.2f} quotes per user."
        elif count < avg_quotes:
            comparison = f"You're below average. The mean is {avg_quotes:.2f} quotes per user. Step it up!"
        else:
            comparison = f"You're exactly average! The mean is {avg_quotes:.2f} quotes per user."
        
        context = f"Commenting on {author}'s quote count ({count}) compared to the average ({avg_quotes:.2f})"
        witty_response = await self.bot.ai_manager.generate_enhanced_personalized_response(comparison, context)
        
        full_response = f"{core_response}\n💬 {witty_response}"
        
        # Ensure the response fits within Twitch's character limit
        if len(full_response) > 500:
            full_response = full_response[:497] + "..."
        
        await self.bot.send_message(ctx.channel, full_response)

    @commands.command(name='lastquote')
    async def last_quote_command(self, ctx: commands.Context):
        last_quote_info = await self.bot.quote_manager.get_last_quote()
        await self.bot.send_message(ctx.channel, last_quote_info)

    @commands.command(name='checkquotes')
    async def check_quotes_command(self, ctx: commands.Context):
        last_id = await self.bot.quote_manager.get_last_quote_number()
        total_quotes = await self.bot.quote_manager.quotes_collection.count_documents({"channel": self.bot.quote_manager.channel_name})
        await ctx.send(f"Last quote ID: {last_id}, Total quotes: {total_quotes}")
