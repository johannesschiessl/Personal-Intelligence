import requests
from bs4 import BeautifulSoup
from typing import Optional

class Url:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def process(self, url: str) -> Optional[str]:
        """Fetch and parse content from a URL.
        
        Args:
            url: The URL to fetch
            
        Returns:
            str: The parsed content or None if the request fails
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for script in soup(["script", "style"]):
                script.decompose()
                
            text = soup.get_text()
            
            lines = (line.strip() for line in text.splitlines())
            
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:10000]
            
        except Exception as e:
            return f"Error fetching URL: {str(e)}"