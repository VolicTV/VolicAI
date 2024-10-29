import aiohttp
from bs4 import BeautifulSoup
from typing import List
from utils.logger import command_logger

async def scrape_web_data(url: str, tag: str = 'h3') -> List[str]:
    """Scrape text content from specified HTML tags on a webpage"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    elements = soup.find_all(tag)
                    return [element.text.strip() for element in elements if element.text.strip()]
                else:
                    command_logger.error(f"Failed to fetch URL {url}. Status: {response.status}")
                    return []
    except Exception as e:
        command_logger.error(f"Error scraping {url}: {str(e)}")
        return []
