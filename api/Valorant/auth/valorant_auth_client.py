import aiohttp
import urllib3
import re
from typing import Dict, Optional, Tuple
from base64 import b64encode
import json

from utils.logger import command_logger

class ValorantAuthClient:
    def __init__(self):
        self.auth_keys = {}
        self.session = None
        self.region = "na"  # Default region
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    async def initialize(self, username: str, password: str) -> bool:
        """Initialize auth session with Riot credentials"""
        try:
            self.session = aiohttp.ClientSession()
            auth_data = await self._get_authorization(username, password)
            if not auth_data:
                return False
            
            self.auth_keys = {
                'access_token': auth_data['access_token'],
                'entitlements_token': await self._get_entitlements_token(auth_data['access_token']),
                'user_id': auth_data['subject']
            }
            return True
            
        except Exception as e:
            command_logger.error(f"Auth initialization failed: {str(e)}")
            return False

    async def _get_authorization(self, username: str, password: str) -> Optional[Dict]:
        """Get Riot authorization tokens"""
        try:
            # Get cookie and client version
            async with self.session.post(
                'https://auth.riotgames.com/api/v1/authorization',
                json={
                    'client_id': 'play-valorant-web-prod',
                    'nonce': '1',
                    'redirect_uri': 'https://playvalorant.com/opt_in',
                    'response_type': 'token id_token',
                    'scope': 'account openid'
                },
                headers={'User-Agent': 'RiotClient/58.0.0.4640299.4552318 rso-auth (Windows;10;;Professional, x64)'},
            ) as r:
                cookies = r.cookies
                
            # Authenticate
            async with self.session.put(
                'https://auth.riotgames.com/api/v1/authorization',
                json={
                    'type': 'auth',
                    'username': username,
                    'password': password
                },
                headers={'User-Agent': 'RiotClient/58.0.0.4640299.4552318 rso-auth (Windows;10;;Professional, x64)'},
                cookies=cookies
            ) as r:
                data = await r.json()
                if 'error' in data:
                    command_logger.error(f"Auth error: {data['error']}")
                    return None
                
                pattern = re.compile('access_token=((?:[a-zA-Z]|\d|\.|-|_)*).*id_token=((?:[a-zA-Z]|\d|\.|-|_)*).*expires_in=(\d*)')
                if 'response' in data and 'parameters' in data['response']:
                    params = data['response']['parameters']
                    if 'uri' in params:
                        match = pattern.findall(params['uri'])[0]
                        return {
                            'access_token': match[0],
                            'id_token': match[1],
                            'expires_in': match[2],
                            'subject': data['response'].get('subject', '')
                        }
            return None

        except Exception as e:
            command_logger.error(f"Authorization failed: {str(e)}")
            return None

    async def _get_entitlements_token(self, access_token: str) -> Optional[str]:
        """Get entitlements token"""
        try:
            async with self.session.post(
                'https://entitlements.auth.riotgames.com/api/token/v1',
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                },
                json={}
            ) as r:
                data = await r.json()
                return data.get('entitlements_token')
        except Exception as e:
            command_logger.error(f"Getting entitlements token failed: {str(e)}")
            return None

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close() 