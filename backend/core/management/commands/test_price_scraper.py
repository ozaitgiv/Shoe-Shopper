from django.core.management.base import BaseCommand
from django.db import models
from core.price_scraper import DjangoPriceScraper, populate_initial_selectors
from core.models import Shoe, PriceSelector
import json

class Command(BaseCommand):
    help = 'Test the Django-integrated price scraper with automatic selector learning'

    def add_arguments(self, parser):
        parser.add_argument('--populate', action='store_true', help='Populate initial selectors')
        parser.add_argument('--limit', type=int, default=5, help='Number of shoes to test')
        parser.add_argument('--update-prices', action='store_true', help='Update actual shoe prices')

    def handle(self, *args, **options):
        if options['populate']:
            self.stdout.write("Populating initial selectors...")
            populate_initial_selectors()
            self.stdout.write(self.style.SUCCESS("Initial selectors populated"))
            return

        scraper = DjangoPriceScraper()
        
        # Get test shoes from database
        shoes = Shoe.objects.filter(
            is_active=True, 
            product_url__isnull=False
        ).exclude(product_url='')[:options['limit']]
        
        if not shoes:
            self.stdout.write(self.style.ERROR("No shoes with URLs found in database"))
            return
        
        self.stdout.write(f"Testing Django Price Scraper on {len(shoes)} shoes")
        self.stdout.write("=" * 70)
        
        results = []
        successful = 0
        high_confidence = 0
        new_selectors = 0
        
        for i, shoe in enumerate(shoes):
            self.stdout.write(f"\n[{i+1}/{len(shoes)}] {shoe.company} {shoe.model}")
            self.stdout.write(f"Expected: ${shoe.price_usd}")
            self.stdout.write(f"URL: {shoe.product_url}")
            self.stdout.write("-" * 50)
            
            result = scraper.scrape_price(shoe.product_url, float(shoe.price_usd))
            results.append(result)
            
            if result.success:
                successful += 1
                diff = abs(result.price - float(shoe.price_usd))
                diff_percent = (diff / float(shoe.price_usd)) * 100
                
                self.stdout.write(self.style.SUCCESS(f"SUCCESS: Found ${result.price}"))
                self.stdout.write(f"   Method: {result.method_used}")
                self.stdout.write(f"   Confidence: {result.confidence_score:.2f}")
                self.stdout.write(f"   Difference: ${diff:.2f} ({diff_percent:.1f}%)")
                
                if result.selector_used:
                    self.stdout.write(f"   Selector: {result.selector_used}")
                
                if result.method_used == "discovered_selector":
                    new_selectors += 1
                    self.stdout.write(self.style.WARNING("   -> NEW SELECTOR DISCOVERED!"))
                
                if result.confidence_score > 0.7:
                    high_confidence += 1
                
                # Update price if requested and confidence is high
                if options['update_prices'] and result.confidence_score > 0.6:
                    old_price = shoe.price_usd
                    shoe.price_usd = result.price
                    shoe.save()
                    self.stdout.write(self.style.SUCCESS(f"   -> Updated price: ${old_price} -> ${result.price}"))
            
            else:
                self.stdout.write(self.style.ERROR(f"FAILED: {result.error}"))
            
            self.stdout.write(f"   Response time: {result.response_time:.2f}s")
        
        # Summary
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 70)
        self.stdout.write(f"Success Rate: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
        self.stdout.write(f"High Confidence: {high_confidence}/{successful}")
        self.stdout.write(f"New Selectors Discovered: {new_selectors}")
        self.stdout.write(f"Average Response Time: {sum(r.response_time for r in results)/len(results):.2f}s")
        
        # Show selector statistics
        total_selectors = PriceSelector.objects.count()
        domains_covered = PriceSelector.objects.values('domain').distinct().count()
        
        self.stdout.write(f"\nSelector Database:")
        self.stdout.write(f"Total Selectors: {total_selectors}")
        self.stdout.write(f"Domains Covered: {domains_covered}")
        
        # Show top performing selectors
        top_selectors = PriceSelector.objects.filter(
            total_attempts__gt=0
        ).annotate(
            calculated_success_rate=models.F('success_count') * 100.0 / models.F('total_attempts')
        ).order_by('-calculated_success_rate')[:5]
        
        if top_selectors:
            self.stdout.write(f"\nTop Performing Selectors:")
            for selector in top_selectors:
                rate = selector.calculated_success_rate if hasattr(selector, 'calculated_success_rate') else selector.success_rate
                self.stdout.write(f"  {selector.domain}: {rate:.1f}% ({selector.success_count}/{selector.total_attempts})")
        
        self.stdout.write(self.style.SUCCESS("\nPrice scraper test completed!"))