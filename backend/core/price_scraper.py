#!/usr/bin/env python3
"""
Django-integrated Price Scraper for Shoe-Shopper
Automatically discovers and saves selectors to database like brand filters
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import logging
from urllib.parse import urlparse
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from django.utils import timezone
from .models import PriceSelector, Shoe

logger = logging.getLogger(__name__)

@dataclass
class PriceScrapingResult:
    """Result of price scraping attempt"""
    url: str
    price: Optional[float] = None
    currency: str = "USD"
    success: bool = False
    error: Optional[str] = None
    response_time: float = 0.0
    method_used: str = ""
    confidence_score: float = 0.0
    selector_used: Optional[str] = None

class DjangoPriceScraper:
    """Django-integrated price scraper with automatic selector learning"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        })
        
        # Security constraints
        self.max_response_size = 10 * 1024 * 1024  # 10MB max response size
        self.timeout = 15  # 15 second timeout
        self.max_redirects = 5
        
        # Price validation patterns
        self.price_patterns = [
            r'\$(\d+\.?\d*)',
            r'USD\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*USD',
            r'"price":\s*"?(\d+\.?\d*)"?',
            r'"amount":\s*"?(\d+\.?\d*)"?',
        ]
        
        # Keywords for discovering price elements
        self.price_keywords = [
            'price', 'cost', 'amount', 'total', 'pay', 'sale', 'regular', 
            'current', 'retail', 'msrp', 'buy', 'purchase', 'checkout'
        ]
    
    def get_domain(self, url: str) -> str:
        """Extract clean domain from URL"""
        try:
            domain = urlparse(url).netloc.lower()
            return domain.replace('www.', '')
        except:
            return ""
    
    def validate_url(self, url: str) -> bool:
        """Validate URL to prevent SSRF attacks"""
        try:
            parsed = urlparse(url)
            
            # Must be HTTP/HTTPS
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Must have a domain
            if not parsed.netloc:
                return False
            
            # Prevent localhost and internal IPs
            domain = parsed.netloc.lower()
            if any(blocked in domain for blocked in ['localhost', '127.0.0.1', '::1', '169.254', '10.', '192.168.', '172.']):
                return False
            
            # Must be reasonable length
            if len(url) > 2000:
                return False
                
            return True
        except:
            return False
    
    def extract_price_from_text(self, text: str, expected_price: Optional[float] = None) -> Optional[float]:
        """Extract price from text with validation"""
        prices_found = []
        
        for pattern in self.price_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    price = float(match)
                    if 10 <= price <= 2000:  # Reasonable shoe price range
                        prices_found.append(price)
                except ValueError:
                    continue
        
        if not prices_found:
            return None
        
        # If we have expected price, prefer closest match
        if expected_price and expected_price > 0:
            closest = min(prices_found, key=lambda x: abs(x - expected_price))
            if abs(closest - expected_price) / expected_price < 0.5:  # Within 50%
                return closest
        
        # Otherwise return highest reasonable price
        return max(prices_found)
    
    def discover_new_selectors(self, soup: BeautifulSoup, domain: str, expected_price: Optional[float] = None) -> List[str]:
        """Discover new price selectors on the page"""
        discovered = []
        
        # Find elements with price-related attributes
        price_elements = set()
        
        # Search by class/id attributes
        for attr in ['class', 'id', 'data-testid', 'data-track', 'data-price']:
            elements = soup.find_all(attrs={attr: re.compile(r'price|cost|amount|sale|regular|current', re.I)})
            price_elements.update(elements)
        
        # Find elements containing dollar signs
        dollar_texts = soup.find_all(text=re.compile(r'\$\d+'))
        for text in dollar_texts:
            if text.parent:
                price_elements.add(text.parent)
        
        # Generate selectors for promising elements
        for element in price_elements:
            selector = self._generate_selector(element)
            if selector:
                text = element.get_text(strip=True)
                price = self.extract_price_from_text(text, expected_price)
                
                if price:
                    # Validate against expected price if available
                    if not expected_price or abs(price - expected_price) / expected_price < 0.4:
                        discovered.append(selector)
                        logger.info(f"Discovered selector for {domain}: {selector} -> ${price}")
        
        return discovered[:5]  # Limit to top 5 discoveries
    
    def _generate_selector(self, element) -> str:
        """Generate CSS selector for an element"""
        try:
            parts = []
            current = element
            depth = 0
            
            while current and current.name and depth < 3:
                part = current.name
                
                # Add class (prefer price-related classes)
                classes = current.get('class', [])
                if classes:
                    price_classes = [c for c in classes if any(kw in c.lower() for kw in self.price_keywords)]
                    if price_classes:
                        part += '.' + '.'.join(price_classes[:2])
                    elif len(classes) <= 3:
                        part += '.' + '.'.join(classes[:2])
                
                # Add ID if present and reasonable length
                elem_id = current.get('id')
                if elem_id and len(elem_id) < 30 and any(kw in elem_id.lower() for kw in self.price_keywords):
                    part += f"#{elem_id}"
                
                # Add data attributes
                for attr in ['data-testid', 'data-track', 'data-price']:
                    value = current.get(attr)
                    if value and any(kw in value.lower() for kw in self.price_keywords):
                        part += f'[{attr}="{value}"]'
                        break
                
                parts.append(part)
                current = current.parent
                depth += 1
                
                if not current or current.name in ['body', 'html']:
                    break
            
            return ' '.join(reversed(parts)) if parts else ""
        except:
            return ""
    
    def scrape_with_db_selectors(self, soup: BeautifulSoup, domain: str, expected_price: Optional[float] = None) -> tuple[Optional[float], Optional[str]]:
        """Try database-stored selectors first"""
        selectors = PriceSelector.get_selectors_for_domain(domain)
        
        for selector_obj in selectors:
            try:
                elements = soup.select(selector_obj.selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    price = self.extract_price_from_text(text, expected_price)
                    
                    if price:
                        # Record successful attempt
                        selector_obj.record_attempt(success=True)
                        logger.info(f"Found price ${price} using DB selector: {selector_obj.selector}")
                        return price, selector_obj.selector
                
                # Record failed attempt
                selector_obj.record_attempt(success=False)
                
            except Exception as e:
                # Record failed attempt
                selector_obj.record_attempt(success=False)
                logger.debug(f"DB selector failed: {selector_obj.selector} - {e}")
        
        return None, None
    
    def save_discovered_selectors(self, domain: str, selectors: List[str]):
        """Save newly discovered selectors to database"""
        for selector in selectors:
            try:
                # Create or get existing selector
                selector_obj, created = PriceSelector.objects.get_or_create(
                    domain=domain,
                    selector=selector,
                    defaults={'is_active': True}
                )
                
                if created:
                    logger.info(f"Saved new selector for {domain}: {selector}")
                else:
                    logger.debug(f"Selector already exists for {domain}: {selector}")
                    
            except Exception as e:
                logger.error(f"Failed to save selector {selector} for {domain}: {e}")
    
    def scrape_price(self, url: str, expected_price: Optional[float] = None) -> PriceScrapingResult:
        """Main price scraping method"""
        start_time = time.time()
        result = PriceScrapingResult(url=url)
        
        # Validate URL first
        if not self.validate_url(url):
            result.error = "Invalid or unsafe URL"
            result.response_time = time.time() - start_time
            return result
        
        domain = self.get_domain(url)
        
        try:
            logger.info(f"Scraping {domain}: {url}" + (f" (expected: ${expected_price})" if expected_price else ""))
            
            # Make request with security constraints
            response = self.session.get(
                url, 
                timeout=self.timeout,
                allow_redirects=True,
                stream=True  # Stream to check content length
            )
            
            # Check content length
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_response_size:
                result.error = "Response too large"
                result.response_time = time.time() - start_time
                return result
            
            # Read content with size limit
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > self.max_response_size:
                    result.error = "Response too large"
                    result.response_time = time.time() - start_time
                    return result
            
            response._content = content
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            result.response_time = time.time() - start_time
            
            # Try database selectors first
            price, selector_used = self.scrape_with_db_selectors(soup, domain, expected_price)
            
            if price:
                result.price = price
                result.success = True
                result.method_used = "database_selector"
                result.selector_used = selector_used
                
                # Calculate confidence
                if expected_price:
                    diff_ratio = abs(price - expected_price) / expected_price
                    result.confidence_score = max(0, 1 - diff_ratio * 2)
                else:
                    result.confidence_score = 0.8
                
                return result
            
            # If no DB selectors worked, try discovery
            logger.info(f"No database selectors worked for {domain}, attempting discovery...")
            discovered_selectors = self.discover_new_selectors(soup, domain, expected_price)
            
            if discovered_selectors:
                # Try the discovered selectors
                for selector in discovered_selectors:
                    try:
                        elements = soup.select(selector)
                        for element in elements:
                            text = element.get_text(strip=True)
                            price = self.extract_price_from_text(text, expected_price)
                            
                            if price:
                                result.price = price
                                result.success = True
                                result.method_used = "discovered_selector"
                                result.selector_used = selector
                                result.confidence_score = 0.6
                                
                                # Save the working selector
                                self.save_discovered_selectors(domain, [selector])
                                
                                return result
                    except Exception as e:
                        logger.debug(f"Discovered selector failed: {selector} - {e}")
                
                # Save all discovered selectors even if they didn't work this time
                self.save_discovered_selectors(domain, discovered_selectors)
            
            # Final fallback: regex on full HTML
            price = self.extract_price_from_text(response.text, expected_price)
            if price:
                result.price = price
                result.success = True
                result.method_used = "regex_fallback"
                result.confidence_score = 0.3
                return result
            
            result.error = "No price found with any method"
            
        except requests.RequestException as e:
            result.error = f"Request failed: {str(e)}"
        except Exception as e:
            result.error = f"Unexpected error: {str(e)}"
            logger.exception(f"Scraping error for {url}")
        
        result.response_time = time.time() - start_time
        return result
    
    def update_shoe_prices(self, limit: Optional[int] = None):
        """Update prices for shoes in database"""
        shoes = Shoe.objects.filter(is_active=True, product_url__isnull=False).exclude(product_url='')
        
        if limit:
            shoes = shoes[:limit]
        
        results = []
        updated_count = 0
        
        for shoe in shoes:
            logger.info(f"Updating price for {shoe.company} {shoe.model}")
            
            result = self.scrape_price(shoe.product_url, float(shoe.price_usd))
            results.append(result)
            
            if result.success and result.confidence_score > 0.5:
                old_price = shoe.price_usd
                shoe.price_usd = result.price
                shoe.save()
                updated_count += 1
                logger.info(f"Updated {shoe}: ${old_price} -> ${result.price}")
            
            time.sleep(1)  # Be respectful
        
        logger.info(f"Price update complete: {updated_count}/{len(results)} shoes updated")
        return results


def populate_initial_selectors():
    """Populate database with initial known selectors"""
    initial_selectors = {
        'amazon.com': ['.a-price-whole', '.a-price .a-offscreen'],
        'allbirds.com': ['[data-testid="pdp-price"]', '.price__current'],
        'newbalance.com': ['.pdp-product-price', '.price-sales'],
        'nordstromrack.com': ['[data-testid="price-current"]', '.price-current'],
        'muji.us': ['.price', '.product-price'],
        'converse.com': ['.product-price', '.price-current'],
        'drmartens.com': ['.product-price', '.pdp-price'],
        'adidas.com': ['.gl-price', '.product-price'],
    }
    
    for domain, selectors in initial_selectors.items():
        for selector in selectors:
            PriceSelector.objects.get_or_create(
                domain=domain,
                selector=selector,
                defaults={'is_active': True}
            )
    
    logger.info("Initial selectors populated")