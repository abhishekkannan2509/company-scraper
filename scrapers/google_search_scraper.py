from typing import Dict, List, Optional
import json
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus
import time
import random

class GoogleSearchScraper:
    def __init__(self):
        self.base_url = "https://www.google.com/search"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        self.default_domains = [
            "khaleejtimes.com",
            "gulfnews.com",
            "thenationalnews.com",
            "arabianbusiness.com",
            "zawya.com"
        ]
    
    def _random_delay(self):
        """Add a random delay between requests to avoid rate limiting."""
        time.sleep(random.uniform(2, 5))
    
    def search_news(self, company_name: str, domains: Optional[List[str]] = None) -> List[Dict]:
        """
        Search for news articles about a company from specific domains using Google Search.
        
        Args:
            company_name (str): Name of the company to search for
            domains (List[str], optional): List of domains to search in. Defaults to UAE news sites.
            
        Returns:
            List[Dict]: List of news articles
        """
        try:
            
            search_domains = domains or self.default_domains
            
            
            
            domain_query = ' OR '.join(f'site:{domain}' for domain in search_domains)
            query = f'"{company_name}" ({domain_query})'
            
            
            encoded_query = quote_plus(query)
            
            
            url = f"{self.base_url}?q={encoded_query}&tbm=nws&hl=en"
            print(url)
            
            self._random_delay()
            
            
            response = self.session.get(url)
            response.raise_for_status()
            
            
            if "Our systems have detected unusual traffic" in response.text:
                print("Warning: Google Search detected automated traffic. Results may be limited.")
                return []
            
            
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = []
            
            
            for result in soup.find_all('div', class_='g'):
                try:
                    
                    title_elem = result.find('h3')
                    link_elem = result.find('a')
                    snippet_elem = result.find('div', class_='VwiC3b')
                    source_elem = result.find('div', class_='UPmit')
                    date_elem = result.find(text=re.compile(r'\d+ \w+ ago|\d+/\d+/\d+|\d+ hours ago|\d+ days ago'))
                    
                    if title_elem and link_elem:
                        article = {
                            'title': title_elem.get_text(),
                            'url': link_elem['href'],
                            'description': snippet_elem.get_text() if snippet_elem else '',
                            'source': {
                                'name': source_elem.get_text() if source_elem else self._extract_domain(link_elem['href'])
                            },
                            'publishedAt': date_elem if date_elem else ''
                        }
                        articles.append(article)
                except Exception as e:
                    print(f"Error parsing article: {str(e)}")
                    continue
            
            return articles
            
        except requests.exceptions.RequestException as e:
            print(f"Error making request to Google Search: {str(e)}")
            return []
        except Exception as e:
            print(f"Error searching news: {str(e)}")
            return []
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL."""
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        return match.group(1) if match else ''
    
    def save_to_json(self, data: List[Dict], filename: Optional[str] = None) -> Optional[str]:
        """
        Save the scraped news data to a JSON file.
        
        Args:
            data (List[Dict]): List of news articles to save
            filename (str, optional): Custom filename. Defaults to timestamp-based name.
            
        Returns:
            str: Path to the saved file
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"google_search_data_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            return filename
        except Exception as e:
            print(f"Error saving data to JSON: {str(e)}")
            return None 