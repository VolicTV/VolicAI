import csv
from pymongo import MongoClient
import sys
import os
from tqdm import tqdm

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import config

client = MongoClient(config.MONGO_URI)
db = client['twitch_bot_db']
quotes_collection = db['quotes']

def update_quotes_from_csv():
    csv_file = os.path.join(parent_dir, f"{config.TWITCH_CHANNEL}_quotes.csv")
    
    # Clear existing quotes for this channel
    quotes_collection.delete_many({"channel": config.TWITCH_CHANNEL})
    
    print(f"Updating quotes for channel: {config.TWITCH_CHANNEL}")
    
    with open(csv_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        quotes = list(reader)
        
        for quote in tqdm(quotes, desc="Updating quotes"):
            new_quote = {
                "_id": quote['id'],
                "text": quote['text'],
                "author": quote['author'],
                "channel": config.TWITCH_CHANNEL
            }
            quotes_collection.insert_one(new_quote)
    
    print("Update complete!")
    print(f"Total quotes in database: {quotes_collection.count_documents({'channel': config.TWITCH_CHANNEL})}")

if __name__ == "__main__":
    update_quotes_from_csv()
