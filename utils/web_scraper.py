import requests
from bs4 import BeautifulSoup

def scrape_web_data(url, table_id=None, tag=None):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    if tag == 'h3':
        # Extract text from all h3 tags
        data = [h3.get_text(strip=True) for h3 in soup.find_all('h3')]
    else:
        # Find the table with the specified id, or default to "tablepress-426"
        table = soup.find('table', id=table_id) if table_id else soup.find('table', id='tablepress-426')
        
        # Extract text from all list items within the table
        if table:
            data = [li.get_text(strip=True) for li in table.find_all('li')]
        else:
            data = []
    
    return data
