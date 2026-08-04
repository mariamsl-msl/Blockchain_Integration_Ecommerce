from django.contrib import admin
from .models import Product, Order, OrderItem

# Register the Product model
class ProductAdmin(admin.ModelAdmin):
    exclude = ('seller',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.seller = request.user
        super().save_model(request, obj, form, change)

admin.site.register(Product, ProductAdmin)

# Inline to show order items inside the order admin
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

# Customize the admin interface for Order model
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'email', 'timestamp', 'payment_status', 'delivery_status')
    list_filter = ('payment_status', 'delivery_status')
    search_fields = ('id', 'full_name', 'email')
    inlines = [OrderItemInline]  # Display associated items

admin.site.register(Order, OrderAdmin)
