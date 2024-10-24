import csv
from pymongo import MongoClient
import config

client = MongoClient(config.MONGO_URI)
db = client['twitch_bot_db']
quotes_collection = db['quotes']

def migrate_quotes():
    with open(f"{config.TWITCH_CHANNEL}_quotes.csv", 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            quote = {
                "_id": row['id'],
                "text": row['text'],
                "author": row['author'],
                "channel": config.TWITCH_CHANNEL
            }
            quotes_collection.insert_one(quote)
            
    print("Migration complete!")

if __name__ == "__main__":
    migrate_quotes()
