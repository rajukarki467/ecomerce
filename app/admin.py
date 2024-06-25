from django.contrib import admin
from .models import (
    Customer,
    LatestProduct,
    Product,
    Cart,
    OrderPlaced,
    Rating,
    Seller
)

# Register your models here.

@admin.register(Customer)
class CustomerModelAdmin(admin.ModelAdmin):
    list_display = ['id','user','name','locality','city','state']

@admin.register(Product)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ['id','title','selling_price','discounted_price','description','brand','category','product_image','created_at']

@admin.register(Cart)
class CartModelAdmin(admin.ModelAdmin):
    list_display = ['id','user','product','quantity']

class OrderPlacedAdmin(admin.ModelAdmin):
    # Specify the fields to display in the admin list view
    list_display = ('id', 'user', 'product', 'quantity', 'total', 'status', 'ordered_date', 'payment_method', 'payment_completed')
    # Add a search bar for specific fields
    search_fields = ('user__username', 'product__name', 'status')
    # Add filters for specific fields
    list_filter = ('status', 'payment_method', 'ordered_date')

    # Customize the fields displayed in the add/edit form
    fields = ('user', 'product', 'address', 'mobile', 'email', 'quantity', 'total', 'status', 'payment_method', 'payment_completed')

    # Read-only fields
    readonly_fields = ('total', 'ordered_date')

admin.site.register(OrderPlaced, OrderPlacedAdmin)

@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ('id', 'firstname', 'lastname', 'username', 'email', 'phone', 'address')
    search_fields = ('firstname', 'lastname', 'username', 'email', 'phone')


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating')  # Display these fields in the admin list view
    list_filter = ('product', 'rating')  # Add filters for these fields
    search_fields = ('user__username',)  # Add a search bar for user's username
    def get_queryset(self, request):
        # Override queryset to prefetch related fields for efficiency
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'product')

admin.site.register(LatestProduct)
