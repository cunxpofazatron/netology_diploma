from django.contrib import admin
from .models import User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem, Contact, ConfirmEmailToken

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'company', 'position', 'type', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'state')
    list_filter = ('state',)
    search_fields = ('name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ('product', 'shop', 'model', 'quantity', 'price', 'price_rrc')
    list_filter = ('shop',)
    search_fields = ('product__name', 'model')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'state', 'dt')
    list_filter = ('state', 'dt')
    search_fields = ('user__email',)

# Простые регистрации для остальных моделей
admin.site.register(Parameter)
admin.site.register(ProductParameter)
admin.site.register(OrderItem)
admin.site.register(Contact)
admin.site.register(ConfirmEmailToken)
