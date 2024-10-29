import sys
import os
import aiohttp
import asyncio
import json

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from utils.logger import command_logger

async def test_riot_api_key():
    """Test if the Riot API key is valid and working"""
    print(f"\nTesting Riot API key: {config.RIOT_API_KEY[:8]}...")
    
    headers = {
        'X-Riot-Token': config.RIOT_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        # Step 1: Get content first to get the current Act ID
        print("\nStep 1: Getting current Act ID...")
        content_url = 'https://na.api.riotgames.com/val/content/v1/contents'
        async with session.get(content_url, headers=headers) as response:
            if response.status == 200:
                content = await response.json()
                # Get the most recent competitive act
                acts = [act for act in content.get('acts', []) if act.get('type') == 'act']
                if acts:
                    current_act = acts[-1]  # Most recent act
                    print(f"Found current Act: {current_act['name']} (ID: {current_act['id']})")
                    act_id = current_act['id']
                else:
                    print("❌ Could not find current Act")
                    return
            else:
                print(f"❌ Failed to get content: {response.status}")
                return

        # Step 2: Test Account API with your Riot ID
        print("\nStep 2: Testing Account API...")
        riot_id = "EF Volic"  # Your Riot ID
        tag = "Volic"         # Your tag
        account_url = f'https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{riot_id}/{tag}'
        
        async with session.get(account_url, headers=headers) as response:
            print(f"Account API Status: {response.status}")
            if response.status == 200:
                account_data = await response.json()
                puuid = account_data.get('puuid')
                print(f"Found PUUID: {puuid}")
            else:
                print("❌ Could not get PUUID")
                body = await response.text()
                print(f"Error: {body}")
                return

        # Step 3: Test various endpoints with real values
        test_endpoints = {
            'VAL Content': content_url,
            'VAL Status': 'https://na.api.riotgames.com/val/status/v1/platform-data',
            'VAL Match History': f'https://na.api.riotgames.com/val/match/v1/matchlists/by-puuid/{puuid}',
            'VAL Ranked': f'https://na.api.riotgames.com/val/ranked/v1/leaderboards/by-act/{act_id}?size=10&startIndex=0'
        }

        for name, url in test_endpoints.items():
            try:
                print(f"\nTesting {name}...")
                print(f"URL: {url}")
                
                async with session.get(url, headers=headers) as response:
                    print(f"Status: {response.status}")
                    body = await response.text()
                    
                    if response.status == 200:
                        print("✅ Success!")
                        if name == 'VAL Ranked':
                            data = json.loads(body)
                            if 'players' in data and data['players']:
                                print(f"Top player: {data['players'][0]['gameName']}#{data['players'][0]['tagLine']}")
                    else:
                        print(f"Response: {body}")

                    print("\nHeaders:")
                    for header, value in response.headers.items():
                        if header.lower().startswith(('x-riot', 'x-rate')):
                            print(f"{header}: {value}")
                        
            except Exception as e:
                print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("Starting Riot API key test...")
    asyncio.run(test_riot_api_key())