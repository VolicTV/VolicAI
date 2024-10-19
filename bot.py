import twitchio
from twitchio.ext import commands
import config
from api.quote_manager import QuoteManager
import random

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=config.TMI_TOKEN, prefix='!', initial_channels=[config.CHANNEL])
        self.quote_manager = QuoteManager(config.CHANNEL)

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')
        await self.fetch_new_quotes()

    async def event_message(self, message):
        await self.quote_manager.process_message(message)
        # Only handle commands if the message has an author
        if message.author:
            await self.handle_commands(message)

    async def fetch_new_quotes(self):
        print("Checking for new quotes...")
        await self.quote_manager.fetch_new_quotes(self, max_checks=200)
        print("Finished checking for new quotes.")

    @commands.command(name='quote')
    async def quote_command(self, ctx: commands.Context):
        quote = self.quote_manager.get_random_quote()
        if quote:
            await ctx.send(f"Quote #{quote['id']}: {quote['text']} - {quote['author']}")
        else:
            await ctx.send("No quotes found.")

    @commands.command(name='quoteid')
    async def quote_id_command(self, ctx: commands.Context, quote_id: str):
        try:
            int(quote_id)  # Check if quote_id is a valid integer
            quote = self.quote_manager.get_quote_by_id(quote_id)
            if quote:
                await ctx.send(f"Quote #{quote['id']}: {quote['text']} - {quote['author']}")
            else:
                await ctx.send(f"No quote found with ID {quote_id}.")
        except ValueError:
            await ctx.send(f"Invalid quote ID: {quote_id}. Please provide a valid number.")

    @commands.command(name='quotesearch')
    async def quote_search_command(self, ctx: commands.Context, *, search_term: str):
        quotes = self.quote_manager.search_quotes(search_term)
        if quotes:
            quote = random.choice(quotes)
            await ctx.send(f"Quote #{quote['id']}: {quote['text']} - {quote['author']}")
        else:
            await ctx.send(f"No quotes found matching '{search_term}'.")

    @commands.command(name='quotecount')
    async def quote_count_command(self, ctx: commands.Context):
        author = ctx.author.name
        count = self.quote_manager.count_quotes_by_author(f'@{author}')
        await ctx.send(f"@{author}, you have {count} quote(s) in the database.")

if __name__ == "__main__":
    bot = Bot()
    bot.run()
