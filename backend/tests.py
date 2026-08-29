from django.test import TestCase
from .models import Category, Shop

class ModelsTestCase(TestCase):
    def test_category_creation(self):
        """Проверка создания категории товаров"""
        category = Category.objects.create(name='Электроника')
        self.assertEqual(category.name, 'Электроника')

    def test_shop_creation(self):
        """Проверка создания магазина"""
        shop = Shop.objects.create(name='Связной', state=True)
        self.assertEqual(shop.name, 'Связной')
        self.assertTrue(shop.state)
