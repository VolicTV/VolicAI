import asyncio
from twitchio.ext import commands
import re
import twitchio
from motor.motor_asyncio import AsyncIOMotorClient
import config
import logging
from pymongo.errors import DuplicateKeyError
from bson.int64 import Int64
import backoff
from utils.logger import command_logger
import random
from typing import Optional
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)

class QuoteManager:
    def __init__(self, db: AsyncIOMotorClient):
        """Initialize QuoteManager with database connection"""
        self.db = db
        # Access the correct database and collection
        self.quotes_collection = self.db.twitch_bot_db.quotes  # Changed from db.quotes.quotes

    async def add_quote(self, quote_id: str, text: str, author: str):
        new_quote = {"_id": quote_id, "text": text, "author": author, "channel": self.channel_name}
        # Update local cache first
        self.quote_cache[quote_id] = new_quote
        # Then update the database
        try:
            await self.quotes_collection.insert_one(new_quote)
            return True
        except DuplicateKeyError:
            # If insert fails, remove from local cache
            del self.quote_cache[quote_id]
            return False

    async def get_random_quote(self):
        """Get a random quote from the database"""
        try:
            # Get total count of quotes for the channel
            count = await self.quotes_collection.count_documents({"channel": config.TWITCH_CHANNEL})
            if count == 0:
                return None

            # Get a random quote
            random_index = random.randint(0, count - 1)
            quote = await self.quotes_collection.find_one(
                {"channel": config.TWITCH_CHANNEL},
                skip=random_index
            )
            return quote

        except Exception as e:
            command_logger.error(f"Error getting random quote: {str(e)}")
            return None

    async def get_quote_by_id(self, quote_id: str):
        return await self.quotes_collection.find_one({"_id": quote_id, "channel": self.channel_name})

    async def search_quotes(self, search_term: str):
        cursor = self.quotes_collection.find({
            "channel": self.channel_name,
            "$or": [
                {"text": {"$regex": search_term, "$options": "i"}},
                {"author": {"$regex": search_term, "$options": "i"}}
            ]
        })
        return await cursor.to_list(length=None)

    async def fetch_new_quotes(self, bot, max_checks=200):
        print("Checking for new quotes...")
        last_id = await self.get_last_quote_number()
        print(f"Last quote in database: ID {last_id}")

        quotes_added = 0
        for i in range(last_id + 1, last_id + max_checks + 1):
            quote_id = str(i)
            existing_quote = await self.quotes_collection.find_one({"_id": quote_id, "channel": self.channel_name})
            if existing_quote:
                print(f"Quote {quote_id} already exists in database. Skipping.")
                continue

            try:
                print(f"Fetching quote {quote_id}...")
                await bot.send_message(self.channel_name, f"!quote {quote_id}")
                
                # Wait for the quote to be received and processed
                try:
                    await asyncio.wait_for(self.quote_received.wait(), timeout=10)
                except asyncio.TimeoutError:
                    print(f"Timeout waiting for quote {quote_id}. Moving to next quote.")
                    continue
                
                if self.current_quote:
                    success = await self.add_quote(self.current_quote['id'], self.current_quote['text'], self.current_quote['author'])
                    if success:
                        quotes_added += 1
                        print(f"Added quote {quote_id} to database.")
                        await self.update_user_quote(quote_id, self.current_quote['author'])
                    else:
                        print(f"Failed to add quote {quote_id} to database.")
                else:
                    print(f"No quote received for ID {quote_id}. Stopping fetch process.")
                    break

                # Reset for next iteration
                self.quote_received.clear()
                self.current_quote = None

            except Exception as e:
                print(f"Error fetching quote {quote_id}: {str(e)}")
                break

        print(f"Finished checking for new quotes. Added {quotes_added} new quotes.")

    async def parse_quote_response(self, message: str) -> Optional[dict]:
        """Parse a quote from a StreamElements message"""
        try:
            # Example format: "Quote #123: This is the quote - @Author"
            match = re.match(r'Quote #(\d+): (.*) - @(.+)', message)
            if match:
                quote_id, text, author = match.groups()
                return {
                    "_id": int(quote_id),
                    "text": text.strip(),
                    "author": author.strip(),
                    "timestamp": datetime.utcnow()
                }
            return None
        except Exception as e:
            command_logger.error(f"Error parsing quote: {str(e)}")
            return None

    async def process_message(self, message):
        """Process a message for potential quotes"""
        try:
            if message.author and message.author.name.lower() == 'streamelements':
                quote = await self.parse_quote_response(message.content)
                if quote:
                    await self.save_quote(quote)
                    command_logger.info(f"Saved quote: {quote}")
                else:
                    command_logger.info(f"Failed to parse quote from message: {message.content}")
        except Exception as e:
            command_logger.error(f"Error processing message for quotes: {str(e)}")

    async def update_user_quote(self, quote_id: str, author: str, session=None):
        user_collection = self.db['users']
        await user_collection.update_one(
            {"username": author.lstrip('@').lower()},
            {"$addToSet": {"quotes": quote_id}},
            upsert=True,
            session=session
        )
        # Also update the user's document in the users collection
        await self.bot.user_data_manager.users_collection.update_one(
            {"username": author.lstrip('@').lower()},
            {"$addToSet": {"quotes": quote_id}},
            upsert=True
        )

    async def count_quotes_by_author(self, author: str):
        count = await self.quotes_collection.count_documents({
            "channel": self.channel_name,
            "author": author.lower()
        })
        return count

    async def get_last_quote(self):
        last_quote = await self.quotes_collection.find_one(
            {"channel": self.channel_name},
            sort=[("_id", -1)]
        )
        if last_quote:
            return f"Last quote in database: ID {last_quote['_id']}, Text: '{last_quote['text'][:30]}...'"
        else:
            return "No quotes found in the database."

    async def get_last_quote_number(self):
        pipeline = [
            {"$match": {"channel": self.channel_name}},
            {"$addFields": {"numeric_id": {"$toInt": "$_id"}}},
            {"$sort": {"numeric_id": -1}},
            {"$limit": 1}
        ]
        
        async for doc in self.quotes_collection.aggregate(pipeline):
            last_id = int(doc['_id'])
            print(f"Debug: Last quote found - ID: {last_id}, Text: {doc['text'][:30]}...")
            return last_id
        
        print("Debug: No quotes found in the database.")
        return 0

    async def print_all_quote_ids(self):
        """Print all quote IDs for debugging"""
        try:
            print("Checking database connection...")
            # Add channel filter if quotes are channel-specific
            count = await self.quotes_collection.count_documents({"channel": config.TWITCH_CHANNEL})
            print(f"Found {count} total quotes for channel {config.TWITCH_CHANNEL}")
            
            # Print first few quotes for verification
            async for quote in self.quotes_collection.find(
                {"channel": config.TWITCH_CHANNEL}
            ).limit(5):
                print(f"Quote #{quote.get('_id')}: {quote.get('text', 'No text')} - {quote.get('author', 'Unknown')}")
                
        except Exception as e:
            error_msg = f"Error accessing quotes: {str(e)}"
            command_logger.error(error_msg)
            print(error_msg)

    async def get_quote_statistics(self):
        total_quotes = await self.quotes_collection.count_documents({"channel": self.channel_name})
        unique_authors = await self.quotes_collection.distinct("author", {"channel": self.channel_name})
        avg_quotes = total_quotes / len(unique_authors) if unique_authors else 0
        return total_quotes, avg_quotes

    async def save_quote(self, quote: dict):
        """Save a quote to the database"""
        try:
            await self.quotes_collection.insert_one(quote)
            command_logger.info(f"Saved quote: {quote}")
        except Exception as e:
            command_logger.error(f"Error saving quote: {str(e)}")




