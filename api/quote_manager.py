import csv
import random
from typing import List, Dict, Optional
import asyncio
from twitchio.ext import commands
import re
import twitchio

class QuoteManager:
    def __init__(self, channel_name: str):
        self.channel_name = channel_name
        self.csv_file = f"{channel_name}_quotes.csv"
        self.quotes = []
        self.load_quotes_from_csv()
        self.quote_received = asyncio.Event()
        self.current_quote = None

    def load_quotes_from_csv(self):
        try:
            with open(self.csv_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                self.quotes = list(reader)
        except FileNotFoundError:
            self.quotes = []

    def save_quotes_to_csv(self):
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['id', 'text', 'author'])
            writer.writeheader()
            writer.writerows(self.quotes)

    def add_quote(self, quote_id: str, text: str, author: str):
        new_quote = {"id": quote_id, "text": text, "author": author}
        self.quotes.append(new_quote)
        self.save_quotes_to_csv()

    def get_random_quote(self) -> Optional[Dict[str, str]]:
        return random.choice(self.quotes) if self.quotes else None

    def get_quote_by_id(self, quote_id: str) -> Optional[Dict[str, str]]:
        print(f"Searching for quote with ID: {quote_id}")
        quote_id_int = int(quote_id)
        for quote in self.quotes:
            quote_id_in_list = int(quote['id'])
            print(f"Comparing with quote ID: {quote_id_in_list}, type: {type(quote_id_in_list)}")
            if quote_id_int == quote_id_in_list:
                print(f"Found matching quote: {quote}")
                return quote
        print(f"No quote found with ID: {quote_id}")
        return None

    def search_quotes(self, search_term: str) -> List[Dict[str, str]]:
        search_term = search_term.lower()
        return [q for q in self.quotes if search_term in q["text"].lower() or search_term in q["author"].lower()]

    async def fetch_new_quotes(self, bot: commands.Bot, max_checks: int = 200):
        channel = bot.get_channel(self.channel_name)
        last_id = max(int(quote['id']) for quote in self.quotes) if self.quotes else 0
        current_id = last_id + 1
        quotes_fetched = 0

        print(f"Starting to fetch new quotes from ID {current_id}")

        for check in range(max_checks):
            self.quote_received.clear()
            self.current_quote = None
            print(f"Checking quote ID: {current_id}")
            await channel.send(f"!quote {current_id}")
            
            try:
                await asyncio.wait_for(self.quote_received.wait(), timeout=5.0)
                if self.current_quote:
                    self.add_quote(self.current_quote['id'], self.current_quote['text'], self.current_quote['author'])
                    quotes_fetched += 1
                    print(f"Added quote #{self.current_quote['id']}: {self.current_quote['text']} - {self.current_quote['author']}")
                else:
                    print(f"No quote found for ID {current_id}. Stopping fetch.")
                    break  # Stop fetching after the first "No quote found"
            except asyncio.TimeoutError:
                print(f"Timeout while waiting for quote {current_id}. Stopping fetch.")
                break  # Stop fetching if there's a timeout

            current_id += 1
            await asyncio.sleep(2)  # Delay between requests

        print(f"Finished fetching quotes. Added {quotes_fetched} new quotes.")
        self.save_quotes_to_csv()

    def parse_quote_response(self, message: str) -> Optional[Dict[str, str]]:
        print(f"Parsing message: {message}")
        if "no quote found" in message.lower():
            return None
        
        # Try to match various formats
        patterns = [
            r'@\w+, #(\d+): (?:([^:]+): )?"?(.*?)"?(?:\s*-\s*(.+))?$',
            r'@\w+, Quote #(\d+): (.*?) - (.*)$',
            r'@\w+, #(\d+): (.+)$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, message)
            if match:
                groups = match.groups()
                if len(groups) == 4:
                    quote_id, author, text, additional_info = groups
                elif len(groups) == 3:
                    quote_id, text, author = groups
                else:
                    quote_id, text = groups
                    author = "Unknown"
                
                if not author:
                    author = additional_info if additional_info else "Unknown"
                
                if author and not author.startswith('@'):
                    author = f'@{author}'
                
                quote = {
                    "id": quote_id,
                    "text": text.strip(),
                    "author": author.strip()
                }
                print(f"Successfully parsed quote: {quote}")
                return quote
        
        print(f"Failed to parse quote: {message}")
        return None

    async def process_message(self, message: twitchio.Message):
        if message.author and message.author.name.lower() == 'streamelements':
            quote = self.parse_quote_response(message.content)
            if quote:
                self.current_quote = quote
                self.quote_received.set()
            else:
                print(f"Failed to parse quote from message: {message.content}")
                self.quote_received.set()  # Set the event even if parsing fails

    def count_quotes_by_author(self, author: str) -> int:
        author = author.lower()
        return sum(1 for quote in self.quotes if quote['author'].lower() == author)
