from django.contrib import admin, messages
from .models import Shoe, FootImage

@admin.register(Shoe)
class ShoeAdmin(admin.ModelAdmin):

    list_display = ('company', 'model', 'gender', 'us_size', 'width_category', 'function', 'price_usd', 'is_active')
    
    list_filter = ('company', 'gender', 'width_category', 'function', 'is_active')
    
    search_fields = ('company', 'model', 'function')
    
    list_editable = ('is_active',)



@admin.register(FootImage)
class FootImageAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user_display', 'status', 
        'length_inches', 'width_inches', 'perimeter_inches', 'area_sq_inches',
        'uploaded_at'
    )
    list_filter = ('status', 'uploaded_at')
    readonly_fields = (
        'uploaded_at', 'user', 'image',
        'status', 'length_inches', 'width_inches', 
        'perimeter_inches', 'area_sq_inches', 'error_message'
    )
    search_fields = ('id', 'user__username', 'user__email')
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.username} ({obj.user.id})"
        return "No User"
    user_display.short_description = "User"
    user_display.admin_order_field = 'user__username'
    
    actions = ['process_as_insole_measurement']
    
    def process_as_insole_measurement(self, request, queryset):
        """Process selected FootImages as insole measurements"""
        
        if queryset.count() != 1:
            self.message_user(request, 
                "Please select exactly one image to process", 
                level=messages.ERROR)
            return
        
        foot_image = queryset.first()
        
        if not foot_image.image:
            self.message_user(request, 
                "No image file found", 
                level=messages.ERROR)
            return
        
        try:
            from .views import process_insole_image_with_enhanced_measurements
            
            length, width, perimeter, area, error_msg = process_insole_image_with_enhanced_measurements(foot_image.image.path)
            
            if error_msg:
                self.message_user(request, 
                    f"Processing failed: {error_msg}", 
                    level=messages.ERROR)
            else:
                foot_image.length_inches = length
                foot_image.width_inches = width
                foot_image.perimeter_inches = perimeter
                foot_image.area_sq_inches = area
                foot_image.status = 'complete'
                foot_image.save()
                
                self.message_user(request, 
                    f"Measurements updated: Length={length}\", Width={width}\", Perimeter={perimeter}\", Area={area} sq in", 
                    level=messages.SUCCESS)
                
        except Exception as e:
            self.message_user(request, 
                f"Error: {str(e)}", 
                level=messages.ERROR)

    process_as_insole_measurement.short_description = "🦶 Process as insole measurement"
    list_display = ('id', 'status', 'length_inches', 'width_inches', 'uploaded_at')
    list_filter = ('status',)
    readonly_fields = ('uploaded_at', 'status', 'length_inches', 'width_inches')
    search_fields = ('id',)
    
    actions = ['process_as_insole_measurement']
    
    def process_as_insole_measurement(self, request, queryset):
        """Process selected FootImages as insole measurements"""
        
        if queryset.count() != 1:
            self.message_user(request, 
                "Please select exactly one image to process", 
                level=messages.ERROR)
            return
        
        foot_image = queryset.first()
        
        if not foot_image.image:
            self.message_user(request, 
                "No image file found", 
                level=messages.ERROR)
            return
        
        try:

            from .views import process_insole_image_with_enhanced_measurements
            
            length, width, perimeter, area, error_msg = process_insole_image_with_enhanced_measurements(foot_image.image.path)
            
            if error_msg:
                self.message_user(request, 
                    f"Processing failed: {error_msg}", 
                    level=messages.ERROR)
            else:
                self.message_user(request, 
                    f"Insole measurements: Length={length}\", Width={width}\", Perimeter={perimeter}\", Area={area} sq in", 
                    level=messages.SUCCESS)
                
        except Exception as e:
            self.message_user(request, 
                f"Error: {str(e)}", 
                level=messages.ERROR)
        except Exception as e:
            self.message_user(request, 
                f"Error: {str(e)}", 
                level=messages.ERROR)

    process_as_insole_measurement.short_description = "Process as insole measurement"