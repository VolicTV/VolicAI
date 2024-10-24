import asyncio
import csv
import re
from twitchio.ext import commands
import config
import os

class QuoteFetcher(commands.Bot):
    def __init__(self):
        super().__init__(token=config.TMI_TOKEN, prefix='!', initial_channels=[config.CHANNEL])
        self.csv_file = f"{config.CHANNEL}_quotes.csv"
        self.quote_received = asyncio.Event()
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5
        self.existing_quotes = self.load_existing_quotes()
        self.current_id = 1
        self.fetching = True

    def load_existing_quotes(self):
        quotes = {}
        if os.path.exists(self.csv_file):
            with open(self.csv_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader, None)  # Skip header
                for row in reader:
                    if row and row[0].isdigit():
                        quotes[int(row[0])] = {'id': row[0], 'text': row[1], 'author': row[2]}
        return quotes

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')
        await self.fetch_all_quotes()

    async def event_message(self, message):
        author_name = message.author.name if message.author else "Unknown"
        print(f"Received message: {message.content} from {author_name}")  # Debug print

        if message.echo:
            return

        if self.fetching and (author_name.lower() == 'streamelements' or 'streamelements' in message.content.lower()):
            quote = self.parse_quote_response(message.content)
            if quote:
                self.save_quote_to_csv(quote)
                print(f"Fetched and stored quote #{quote['id']}: {quote}")
                self.consecutive_failures = 0
            else:
                print(f"Failed to parse quote from message: {message.content}")
                self.consecutive_failures += 1
            
            self.quote_received.set()

    async def fetch_all_quotes(self):
        channel = self.get_channel(config.CHANNEL)
        while self.fetching:
            while self.current_id in self.existing_quotes:
                self.current_id += 1

            self.quote_received.clear()
            print(f"Requesting quote #{self.current_id}")
            await channel.send(f"!quote {self.current_id}")
            
            try:
                await asyncio.wait_for(self.quote_received.wait(), timeout=15)
                print(f"Received response for quote #{self.current_id}")
            except asyncio.TimeoutError:
                print(f"No response for quote #{self.current_id}. Moving to next.")
                self.consecutive_failures += 1

            if self.consecutive_failures >= self.max_consecutive_failures:
                print(f"Reached {self.max_consecutive_failures} consecutive failures. Stopping fetch.")
                self.fetching = False
            
            self.current_id += 1
            await asyncio.sleep(5)  # Delay between quote requests

        await self.finish_fetching()

    async def finish_fetching(self):
        print("Finished fetching quotes.")
        print(f"Quotes have been saved to {self.csv_file}")
        await self.close()

    def parse_quote_response(self, message):
        # Try to match the full format first
        match = re.match(r'@\w+, #(\d+): (?:([^:]+): )?"?(.*?)"?(?:\s*-\s*(.+))?$', message)
        if match:
            quote_id, author, text, additional_info = match.groups()
            if not author and additional_info:
                author = additional_info
            elif not author:
                author = "Unknown"
            
            # Add '@' to the author if it's missing
            if author and not author.startswith('@'):
                author = f'@{author}'
            
            return {
                "id": quote_id,
                "text": text.strip(),
                "author": author.strip()
            }
        
        # If full format doesn't match, try to extract just the ID and text
        simple_match = re.match(r'@\w+, #(\d+): (.+)$', message)
        if simple_match:
            quote_id, text = simple_match.groups()
            return {
                "id": quote_id,
                "text": text.strip(),
                "author": "Unknown"
            }
        
        return None

    def save_quote_to_csv(self, quote):
        self.existing_quotes[int(quote['id'])] = quote
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, quoting=csv.QUOTE_ALL)
            writer.writerow(['id', 'text', 'author'])
            for quote_id in sorted(self.existing_quotes.keys()):
                q = self.existing_quotes[quote_id]
                writer.writerow([q['id'], q['text'], q['author']])

fetcher = QuoteFetcher()
asyncio.run(fetcher.run())