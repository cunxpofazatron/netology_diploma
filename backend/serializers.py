from rest_framework import serializers
from .models import User, Category, Shop, ProductInfo, Product, ProductParameter, Contact
from rest_framework import serializers
from .models import User, Category, Shop, ProductInfo, Product, ProductParameter, Order, OrderItem

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'company', 'position', 'type')
        read_only_fields = ('id',)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name',)
        read_only_fields = ('id',)

class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('id', 'name', 'state',)
        read_only_fields = ('id',)

class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value',)

class ProductInfoSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField()
    shop = serializers.StringRelatedField()
    product_parameters = ProductParameterSerializer(many=True, read_only=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'product', 'shop', 'model', 'quantity', 'price', 'price_rrc', 'product_parameters',)
        read_only_fields = ('id',)

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('id', 'product_info', 'quantity', 'order',)
        read_only_fields = ('id',)
        extra_kwargs = {'order': {'write_only': True}}

class OrderSerializer(serializers.ModelSerializer):
    ordered_items = OrderItemSerializer(read_only=True, many=True)

    class Meta:
        model = Order
        fields = ('id', 'ordered_items', 'state', 'dt',)
        read_only_fields = ('id',)

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'phone')
        read_only_fields = ('id',)
        extra_kwargs = {'user': {'write_only': True}}
