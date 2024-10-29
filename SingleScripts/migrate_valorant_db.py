import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def migrate_valorant_data():
    """Migrate data from valorant database to twitch_bot_db"""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(config.MONGO_URI)
        
        # Source and destination databases
        valorant_db = client.valorant
        twitch_bot_db = client.twitch_bot_db
        
        # Collections to migrate
        collections = ['riot_ids', 'player_stats', 'match_history']
        
        for collection_name in collections:
            logger.info(f"Migrating {collection_name}...")
            
            # Get source collection
            source_collection = valorant_db[collection_name]
            # Get destination collection
            dest_collection = twitch_bot_db[collection_name]
            
            # Count documents before migration
            doc_count = await source_collection.count_documents({})
            logger.info(f"Found {doc_count} documents in {collection_name}")
            
            if doc_count > 0:
                # Get all documents
                documents = await source_collection.find({}).to_list(None)
                
                # Add migration metadata
                for doc in documents:
                    doc['migrated_at'] = datetime.utcnow()
                    doc['migrated_from'] = 'valorant_db'
                
                try:
                    # Insert into new database
                    result = await dest_collection.insert_many(documents)
                    logger.info(f"Successfully migrated {len(result.inserted_ids)} documents to {collection_name}")
                except Exception as e:
                    logger.error(f"Error inserting documents into {collection_name}: {str(e)}")
                    continue
            else:
                logger.info(f"No documents found in {collection_name} to migrate")
        
        # Create indexes in new location
        logger.info("Creating indexes...")
        await twitch_bot_db.riot_ids.create_index("twitch_username", unique=True)
        await twitch_bot_db.player_stats.create_index("puuid", unique=True)
        await twitch_bot_db.player_stats.create_index("last_updated")
        await twitch_bot_db.match_history.create_index("puuid")
        await twitch_bot_db.match_history.create_index("match_id", unique=True)
        
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
    finally:
        client.close()

async def verify_migration():
    """Verify the migration was successful"""
    try:
        client = AsyncIOMotorClient(config.MONGO_URI)
        valorant_db = client.valorant
        twitch_bot_db = client.twitch_bot_db
        collections = ['riot_ids', 'player_stats', 'match_history']
        
        for collection_name in collections:
            source_count = await valorant_db[collection_name].count_documents({})
            dest_count = await twitch_bot_db[collection_name].count_documents({})
            
            logger.info(f"{collection_name}:")
            logger.info(f"  Source (valorant_db): {source_count} documents")
            logger.info(f"  Destination (twitch_bot_db): {dest_count} documents")
            
            if source_count == dest_count:
                logger.info("  ✅ Migration verified")
            else:
                logger.warning("  ⚠️ Document count mismatch!")
                
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    logger.info("Starting Valorant database migration...")
    
    # Run migration
    asyncio.run(migrate_valorant_data())
    
    # Verify migration
    logger.info("\nVerifying migration...")
    asyncio.run(verify_migration()) 