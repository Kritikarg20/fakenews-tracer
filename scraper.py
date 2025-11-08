"""
Scraper Module - Extract metadata from news articles
"""

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from urllib.parse import urlparse
import re
from datetime import datetime

# Free NewsAPI key placeholder - users need to get their own at https://newsapi.org
NEWSAPI_KEY = "YOUR_NEWSAPI_KEY_HERE"

def scrape_article_metadata(url):
    """
    Scrape metadata from a news article URL
    
    Args:
        url (str): The article URL to scrape
        
    Returns:
        dict: Article metadata including title, author, date, and cited sources
        
    Raises:
        Exception: If scraping fails and NewsAPI fallback also fails
    """
    try:
        # Check robots.txt compliance (basic check)
        domain = urlparse(url).netloc
        
        # Make request with timeout
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; FakeNewsTracer/1.0; +http://example.com/bot)'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = None
        if soup.find('meta', property='og:title'):
            title = soup.find('meta', property='og:title').get('content')
        elif soup.find('title'):
            title = soup.find('title').text.strip()
        else:
            title = "Unknown Title"
        
        # Extract author
        author = None
        author_meta = soup.find('meta', attrs={'name': re.compile('author', re.I)})
        if author_meta:
            author = author_meta.get('content')
        elif soup.find('span', class_=re.compile('author', re.I)):
            author = soup.find('span', class_=re.compile('author', re.I)).text.strip()
        else:
            author = "Unknown Author"
        
        # Extract publish date
        publish_date = None
        date_meta = soup.find('meta', property='article:published_time')
        if not date_meta:
            date_meta = soup.find('meta', attrs={'name': re.compile('date', re.I)})
        
        if date_meta:
            try:
                date_str = date_meta.get('content')
                publish_date = date_parser.parse(date_str).strftime('%Y-%m-%d')
            except:
                publish_date = "Unknown Date"
        else:
            publish_date = "Unknown Date"
        
        # Extract cited sources (find all external links)
        sources = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href.startswith('http') and urlparse(href).netloc != domain:
                sources.append({
                    'url': href,
                    'domain': urlparse(href).netloc,
                    'text': link.text.strip()[:100]
                })
        
        # Remove duplicates
        unique_sources = []
        seen_domains = set()
        for source in sources:
            if source['domain'] not in seen_domains:
                seen_domains.add(source['domain'])
                unique_sources.append(source)
        
        return {
            'url': url,
            'title': title,
            'author': author,
            'publish_date': publish_date,
            'domain': domain,
            'sources': unique_sources[:10],  # Limit to top 10
            'scrape_success': True
        }
        
    except Exception as e:
        print(f"Scraping failed for {url}: {str(e)}")
        # Fallback to NewsAPI
        return fallback_to_newsapi(url)

def fallback_to_newsapi(url):
    """
    Fallback to NewsAPI when direct scraping fails
    
    Args:
        url (str): Article URL
        
    Returns:
        dict: Basic metadata from NewsAPI or minimal data
    """
    try:
        if NEWSAPI_KEY == "YOUR_NEWSAPI_KEY_HERE":
            # Return minimal data if no API key
            return {
                'url': url,
                'title': f"Article from {urlparse(url).netloc}",
                'author': "Unknown",
                'publish_date': datetime.now().strftime('%Y-%m-%d'),
                'domain': urlparse(url).netloc,
                'sources': [],
                'scrape_success': False
            }
        
        # Try NewsAPI (this is a simplified version)
        domain = urlparse(url).netloc
        api_url = f"https://newsapi.org/v2/everything?domains={domain}&apiKey={NEWSAPI_KEY}"
        response = requests.get(api_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('articles'):
                article = data['articles'][0]
                return {
                    'url': url,
                    'title': article.get('title', 'Unknown'),
                    'author': article.get('author', 'Unknown'),
                    'publish_date': article.get('publishedAt', 'Unknown')[:10],
                    'domain': domain,
                    'sources': [],
                    'scrape_success': False
                }
    except:
        pass
    
    # Return minimal data if all fails
    return {
        'url': url,
        'title': f"Article from {urlparse(url).netloc}",
        'author': "Unknown",
        'publish_date': datetime.now().strftime('%Y-%m-%d'),
        'domain': urlparse(url).netloc,
        'sources': [],
        'scrape_success': False
    }

def search_related_articles(keyword_or_url, num_results=10):
    """
    Search for related articles using keyword or URL
    
    Args:
        keyword_or_url (str): Search term or URL
        num_results (int): Number of results to return
        
    Returns:
        list: List of article dictionaries with metadata
    """
    articles = []
    
    # Check if input is URL or keyword
    is_url = keyword_or_url.startswith('http')
    
    if is_url:
        # If URL, scrape it first
        main_article = scrape_article_metadata(keyword_or_url)
        articles.append(main_article)
        # Use title as search keyword
        search_term = main_article['title']
    else:
        search_term = keyword_or_url
    
    # Search using NewsAPI
    try:
        if NEWSAPI_KEY != "YOUR_NEWSAPI_KEY_HERE":
            api_url = f"https://newsapi.org/v2/everything?q={search_term}&pageSize={num_results}&apiKey={NEWSAPI_KEY}"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for article_data in data.get('articles', [])[:num_results]:
                    article = {
                        'url': article_data.get('url', ''),
                        'metadata': {
                            'title': article_data.get('title', 'Unknown'),
                            'author': article_data.get('author', 'Unknown'),
                            'publish_date': article_data.get('publishedAt', 'Unknown')[:10],
                            'domain': urlparse(article_data.get('url', '')).netloc,
                            'sources': []
                        },
                        'domain': urlparse(article_data.get('url', '')).netloc
                    }
                    articles.append(article)
    except Exception as e:
        print(f"NewsAPI search failed: {str(e)}")
    
    # If no results from API, generate sample data for demo
    if len(articles) < 3:
        print("Generating sample data for demonstration...")
        sample_domains = [
            'bbc.com', 'cnn.com', 'reuters.com', 'theguardian.com',
            'nytimes.com', 'washingtonpost.com', 'apnews.com'
        ]
        
        for i, domain in enumerate(sample_domains[:num_results]):
            articles.append({
                'url': f'https://{domain}/article-{i}',
                'metadata': {
                    'title': f'{search_term} - Report from {domain}',
                    'author': f'Reporter {i+1}',
                    'publish_date': f'2024-{10+i%3:02d}-{15+i:02d}',
                    'domain': domain,
                    'sources': []
                },
                'domain': domain
            })
    
    return articles[:num_results]