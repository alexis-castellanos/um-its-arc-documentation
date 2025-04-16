#!/usr/bin/env python
"""
University of Michigan Advanced Research Computing Documentation Scraper

This script crawls the University of Michigan ARC documentation site and
extracts all pages, storing them in a structured format.

Base URL: https://documentation.its.umich.edu/advanced-research-computing
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import re
import json
from urllib.parse import urljoin, urlparse
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("arc_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://documentation.its.umich.edu/advanced-research-computing"
OUTPUT_DIR = "umich_arc_docs"
DELAY = 1  # Delay between requests in seconds
MAX_PAGES = 1000  # Safety limit

# Make sure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


class ARCDocScraper:
    """Scraper for University of Michigan ARC Documentation."""
    
    def __init__(self, base_url=BASE_URL, output_dir=OUTPUT_DIR, delay=DELAY):
        self.base_url = base_url
        self.output_dir = output_dir
        self.delay = delay
        self.session = requests.Session()
        # Add headers to mimic a browser request
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        })
        self.visited_urls = set()
        self.pages = {}
        self.link_map = {}
        
    def get_soup(self, url):
        """Fetch the URL and return a BeautifulSoup object."""
        try:
            logger.info(f"Fetching {url}")
            response = self.session.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def is_valid_url(self, url):
        """Check if URL is valid and within the documentation site."""
        parsed_url = urlparse(url)
        # Only process documentation.its.umich.edu URLs
        if 'documentation.its.umich.edu' not in parsed_url.netloc:
            return False
        # Avoid non-HTML resources
        if any(url.endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.jpg', '.png', '.gif']):
            return False
        return True
    
    def extract_page_info(self, soup, url):
        """Extract relevant information from a page."""
        page_info = {
            'url': url,
            'title': soup.title.text.strip() if soup.title else "No Title",
            'content': "",
            'links': [],
        }
        
        # Extract main content
        main_content = soup.find('div', class_='region-content')
        if main_content:
            # Extract text content
            page_info['content'] = main_content.get_text(separator='\n', strip=True)
            
            # Extract links to other documentation pages
            for link in main_content.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                
                if self.is_valid_url(full_url):
                    link_text = link.get_text(strip=True)
                    page_info['links'].append({
                        'url': full_url,
                        'text': link_text or "No Link Text"
                    })
                    
        return page_info
    
    def save_page(self, page_info):
        """Save page information to a file."""
        # Create a safe filename from the URL
        parsed_url = urlparse(page_info['url'])
        filename = parsed_url.path.replace('/', '_')
        if not filename:
            filename = 'index'
        filename = re.sub(r'[^\w\-.]', '_', filename)
        
        # Add query parameters to filename if they exist
        if parsed_url.query:
            filename += '_' + re.sub(r'[^\w\-.]', '_', parsed_url.query)
            
        filepath = os.path.join(self.output_dir, filename + '.json')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(page_info, f, indent=2)
            
        logger.info(f"Saved {page_info['url']} to {filepath}")
        return filepath
    
    def crawl(self, start_url=None):
        """Crawl the documentation site starting from the given URL."""
        if start_url is None:
            start_url = self.base_url
            
        urls_to_visit = [start_url]
        page_counter = 0
        
        while urls_to_visit and page_counter < MAX_PAGES:
            url = urls_to_visit.pop(0)
            
            # Skip if already visited
            if url in self.visited_urls:
                continue
                
            # Mark as visited
            self.visited_urls.add(url)
            page_counter += 1
            
            # Get the page content
            soup = self.get_soup(url)
            if not soup:
                continue
                
            # Extract page information
            page_info = self.extract_page_info(soup, url)
            self.pages[url] = page_info
            
            # Save the page
            self.save_page(page_info)
            
            # Add links to visit queue if they're in the documentation site
            for link in page_info['links']:
                link_url = link['url']
                if link_url not in self.visited_urls and link_url not in urls_to_visit:
                    # Check if the link is within the documentation site
                    if 'documentation.its.umich.edu' in link_url:
                        urls_to_visit.append(link_url)
                        
                # Add to link map
                if url not in self.link_map:
                    self.link_map[url] = []
                self.link_map[url].append(link_url)
            
            # Save progress periodically
            if page_counter % 10 == 0:
                self.save_progress()
                
            # Be nice to the server
            time.sleep(self.delay)
            
        # Save final progress
        self.save_progress()
        logger.info(f"Crawl completed. Visited {len(self.visited_urls)} pages.")
        
    def save_progress(self):
        """Save the current progress."""
        with open(os.path.join(self.output_dir, 'link_map.json'), 'w', encoding='utf-8') as f:
            json.dump(self.link_map, f, indent=2)
            
        with open(os.path.join(self.output_dir, 'visited_urls.json'), 'w', encoding='utf-8') as f:
            json.dump(list(self.visited_urls), f, indent=2)
            
        logger.info(f"Progress saved. Visited {len(self.visited_urls)} pages so far.")
        
    def create_index(self):
        """Create an index of all scraped pages."""
        index = {
            'total_pages': len(self.pages),
            'pages': []
        }
        
        for url, page_info in self.pages.items():
            index['pages'].append({
                'url': url,
                'title': page_info['title'],
                'outgoing_links': len(page_info['links'])
            })
            
        with open(os.path.join(self.output_dir, 'index.json'), 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
            
        logger.info(f"Index created with {len(self.pages)} pages.")
        
    def run(self, start_url=None):
        """Run the full scraping process."""
        try:
            logger.info("Starting the scraping process")
            self.crawl(start_url)
            self.create_index()
            logger.info("Scraping completed successfully")
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            raise
            

if __name__ == "__main__":
    # Handle pagination by starting with both the base page and page 1
    scraper = ARCDocScraper()
    
    # First crawl the base pages
    logger.info("Starting with the base page")
    scraper.crawl(BASE_URL)
    
    # Then crawl page 1 and beyond
    logger.info("Starting with page 1")
    scraper.crawl(f"{BASE_URL}?page=1")
    
    # Create the index
    scraper.create_index()
    
    logger.info("Scraping process completed")