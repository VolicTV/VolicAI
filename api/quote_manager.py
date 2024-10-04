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

    async def fetch_new_quotes(self, bot: commands.Bot, max_checks: int = 100):
        channel = bot.get_channel(self.channel_name)
        last_id = max(int(quote['id']) for quote in self.quotes) if self.quotes else 0
        current_id = last_id + 1
        consecutive_failures = 0
        quotes_fetched = 0

        print(f"Starting to fetch new quotes from ID {current_id}")

        for check in range(max_checks):
            await channel.send(f"!quote {current_id}")
            try:
                messages = await bot.wait_for('message', timeout=5.0)
                message = messages[0] if isinstance(messages, tuple) else messages

                if message.author and message.author.name.lower() == 'streamelements':
                    quote = self.parse_quote_response(message.content)
                    if quote:
                        if int(quote['id']) != current_id:
                            print(f"Warning: Requested quote {current_id}, but received quote {quote['id']}")
                        self.add_quote(quote['id'], quote['text'], quote['author'])
                        consecutive_failures = 0
                        quotes_fetched += 1
                        if quotes_fetched % 10 == 0:
                            print(f"Fetched {quotes_fetched} new quotes...")
                    else:
                        if "no quote found" in message.content.lower():
                            print(f"No quote found for ID {current_id}. Stopping fetch.")
                            break
                        consecutive_failures += 1
                else:
                    consecutive_failures += 1
            except asyncio.TimeoutError:
                consecutive_failures += 1
                print(f"Timeout while waiting for quote {current_id}")
                            
            if consecutive_failures >= 2: #set this to however many times you want to check for quotes at startup
                print(f"Reached 5 consecutive failures. Stopping fetch.")
                break

            current_id += 1
            await asyncio.sleep(2)  # Delay between requests

        print(f"Finished fetching quotes. Added {quotes_fetched} new quotes.")
        self.save_quotes_to_csv()

    def parse_quote_response(self, message: str) -> Optional[Dict[str, str]]:
        if "no quote found" in message.lower():
            return None
        match = re.match(r'Quote #(\d+): (.*) - (.*)$', message)
        if match:
            quote_id, author, text, additional_info = match.groups()
            if not author and additional_info:
                author = additional_info
            elif not author:
                author = "Unknown"
            
            if author and not author.startswith('@'):
                author = f'@{author}'
            
            return {
                "id": quote_id,
                "text": text.strip(),
                "author": author.strip()
            }
        
        simple_match = re.match(r'@\w+, #(\d+): (.+)$', message)
        if simple_match:
            quote_id, text = simple_match.groups()
            return {
                "id": quote_id,
                "text": text.strip(),
                "author": "Unknown"
            }
        
        return None