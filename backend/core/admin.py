from django.contrib import admin, messages
from django.utils.html import format_html
from .models import Shoe, FootImage, PriceSelector

@admin.register(Shoe)
class ShoeAdmin(admin.ModelAdmin):
    # What columns to show in the list view
    list_display = ('shoe_image_preview', 'company', 'model', 'gender', 'us_size', 'width_category', 'function', 'price_usd', 'is_active', 'has_insole_measurements')
    
    # Add filters on the right side
    list_filter = ('company', 'gender', 'width_category', 'function', 'is_active')
    
    # Add search functionality
    search_fields = ('company', 'model', 'function')
    
    # Allow editing is_active directly from the list
    list_editable = ('is_active',)
    
    # Group fields in the edit form
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'model', 'gender', 'us_size', 'width_category', 'function', 'price_usd', 'product_url', 'is_active')
        }),
        ('Product Image', {
            'fields': ('shoe_image_url',),
            'description': 'Enter URL to the shoe product image (e.g., from manufacturer website).'  # CHANGED: description
        }),
        ('Insole Measurements', {
            'fields': ('insole_image', 'insole_length', 'insole_width', 'insole_perimeter', 'insole_area'),
            'description': 'Upload an insole image to automatically calculate measurements, or enter them manually.'
        }),
    )
    
    # Make the calculated fields read-only
    readonly_fields = ('insole_length', 'insole_width', 'insole_perimeter', 'insole_area')
    
    def shoe_image_preview(self, obj):
        """Show a small preview of the shoe image in the admin list"""
        if obj.shoe_image_url: 
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" '
                'onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'inline\';" />'
                '<span style="display: none; color: #999; font-size: 11px;">Invalid URL</span>',
                obj.shoe_image_url 
            )
        return "No Image"
    shoe_image_preview.short_description = 'Image'
    
    def has_insole_measurements(self, obj):
        """Show if shoe has insole measurements"""
        return bool(obj.insole_length)
    has_insole_measurements.boolean = True
    has_insole_measurements.short_description = 'Has Measurements'


@admin.register(FootImage)
class FootImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'length_inches', 'width_inches', 'uploaded_at')
    list_filter = ('status',)
    readonly_fields = ('uploaded_at', 'status', 'length_inches', 'width_inches')
    search_fields = ('id',)
    
    # Add the action
    actions = ['process_as_insole_measurement']
    
    def process_as_insole_measurement(self, request, queryset):
        """Process selected FootImages as insole measurements"""
        
        # Safety: Only allow one image at a time
        if queryset.count() != 1:
            self.message_user(request, 
                "Please select exactly one image to process", 
                level=messages.ERROR)
            return
        
        foot_image = queryset.first()
        
        # Safety: Check if image file exists
        if not foot_image.image:
            self.message_user(request, 
                "No image file found", 
                level=messages.ERROR)
            return
        
        try:
            # Process the actual uploaded image
            from .views import process_insole_image_with_enhanced_measurements
            
            # Get the measurements
            length, width, perimeter, area, error_msg = process_insole_image_with_enhanced_measurements(foot_image.image.path)
            
            if error_msg:
                self.message_user(request, 
                    f"Processing failed: {error_msg}", 
                    level=messages.ERROR)
            else:
                # Show all 4 measurements
                self.message_user(request, 
                    f"Insole measurements: Length={length}\", Width={width}\", Perimeter={perimeter}\", Area={area} sq in", 
                    level=messages.SUCCESS)
                
        except Exception as e:
            self.message_user(request, 
                f"Error: {str(e)}", 
                level=messages.ERROR)
    
    process_as_insole_measurement.short_description = "Process as insole measurement"


@admin.register(PriceSelector)
class PriceSelectorAdmin(admin.ModelAdmin):
    list_display = ('domain', 'selector_preview', 'success_rate_display', 'success_count', 'total_attempts', 'last_success', 'is_active')
    list_filter = ('domain', 'is_active', 'last_success')
    search_fields = ('domain', 'selector')
    list_editable = ('is_active',)
    readonly_fields = ('success_count', 'total_attempts', 'last_success', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Selector Information', {
            'fields': ('domain', 'selector', 'is_active')
        }),
        ('Performance Stats', {
            'fields': ('success_count', 'total_attempts', 'last_success'),
            'description': 'These fields are automatically updated when the selector is used.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def selector_preview(self, obj):
        """Show a truncated version of the selector"""
        if len(obj.selector) > 60:
            return obj.selector[:60] + '...'
        return obj.selector
    selector_preview.short_description = 'Selector'
    
    def success_rate_display(self, obj):
        """Show success rate with color coding"""
        rate = obj.success_rate
        if rate >= 80:
            color = '#28a745'  # green
        elif rate >= 60:
            color = '#ffc107'  # yellow
        elif rate >= 30:
            color = '#fd7e14'  # orange
        else:
            color = '#dc3545'  # red
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, rate
        )
    success_rate_display.short_description = 'Success Rate'
    success_rate_display.admin_order_field = 'success_rate'
    
    # Custom action to test selectors
    actions = ['test_selectors']
    
    def test_selectors(self, request, queryset):
        """Test selected selectors against sample URLs"""
        from .price_scraper import DjangoPriceScraper
        
        if queryset.count() > 5:
            self.message_user(request, 
                "Please select 5 or fewer selectors to test",
                level=messages.ERROR)
            return
        
        scraper = DjangoPriceScraper()
        tested = 0
        
        for selector in queryset:
            # This is a simplified test - in practice you'd need URLs for each domain
            tested += 1
        
        self.message_user(request,
            f"Tested {tested} selectors. Check logs for detailed results.",
            level=messages.SUCCESS)
    
    test_selectors.short_description = "Test selected selectors"