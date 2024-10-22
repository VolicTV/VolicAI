import asyncio
from twitchio.ext import commands
import re
import twitchio
from motor.motor_asyncio import AsyncIOMotorClient
import config
import logging
from pymongo.errors import DuplicateKeyError
from bson.int64 import Int64

# Set up logging
logging.basicConfig(level=logging.INFO)

class QuoteManager:
    def __init__(self, channel_name: str):
        self.channel_name = channel_name
        self.client = AsyncIOMotorClient(config.MONGO_URI)
        self.db = self.client['twitch_bot_db']
        self.quotes_collection = self.db['quotes']
        self.quote_received = asyncio.Event()
        self.current_quote = None

    async def add_quote(self, quote_id: str, text: str, author: str):
        new_quote = {"_id": quote_id, "text": text, "author": author, "channel": self.channel_name}
        try:
            # Start a session for the transaction
            async with await self.client.start_session() as session:
                async with session.start_transaction():
                    # Insert the new quote
                    await self.quotes_collection.insert_one(new_quote, session=session)
                    
                    # Update the user's quotes
                    await self.update_user_quote(quote_id, author, session=session)
                    
            logging.info(f"Successfully added quote {quote_id} and updated user {author}")
            return True
        except DuplicateKeyError:
            logging.warning(f"Quote with ID {quote_id} already exists. Skipping insertion.")
            return False
        except Exception as e:
            logging.error(f"Error adding quote {quote_id}: {str(e)}")
            return False

    async def get_random_quote(self):
        cursor = self.quotes_collection.aggregate([
            {"$match": {"channel": self.channel_name}},
            {"$sample": {"size": 1}}
        ])
        async for doc in cursor:
            return doc
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

    async def parse_quote_response(self, message):
        pattern = r'@\w+, #(\d+): @(\w+): "(.*)"'
        match = re.match(pattern, message)
        if match:
            quote_id, author, text = match.groups()
            return {"text": text, "author": author, "id": quote_id}
        return None

    async def process_message(self, message: twitchio.Message):
        if message.author and message.author.name.lower() == 'streamelements':
            quote = await self.parse_quote_response(message.content)
            if quote:
                self.current_quote = quote
                self.quote_received.set()
            else:
                print(f"Failed to parse quote from message: {message.content}")
                self.quote_received.set()  # Set the event even if parsing fails

    async def update_user_quote(self, quote_id: str, author: str, session=None):
        user_collection = self.db['users']
        await user_collection.update_one(
            {"username": author.lstrip('@').lower()},
            {"$addToSet": {"quotes": quote_id}},
            upsert=True,
            session=session
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
        pipeline = [
            {"$match": {"channel": self.channel_name}},
            {"$addFields": {"numeric_id": {"$toInt": "$_id"}}},
            {"$sort": {"numeric_id": 1}}
        ]
        
        print(f"All quote IDs for channel {self.channel_name}:")
        async for doc in self.quotes_collection.aggregate(pipeline):
            print(f"Quote ID: {doc['_id']}")

    async def get_quote_statistics(self):
        total_quotes = await self.quotes_collection.count_documents({"channel": self.channel_name})
        unique_authors = await self.quotes_collection.distinct("author", {"channel": self.channel_name})
        avg_quotes = total_quotes / len(unique_authors) if unique_authors else 0
        return total_quotes, avg_quotes
