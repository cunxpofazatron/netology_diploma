from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import JsonResponse
from rest_framework.views import APIView
from requests import get
from yaml import load as load_yaml, Loader
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer, ProductInfoSerializer, OrderSerializer, ContactSerializer
from rest_framework.response import Response
from .models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem, ConfirmEmailToken
from .models import Contact
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

class RegisterAccount(APIView):
    """
    Для регистрации покупателей
    """
    def post(self, request, *args, **kwargs):
        # Проверяем обязательные аргументы
        if {'first_name', 'last_name', 'email', 'password', 'company', 'position', 'type'}.issubset(request.data):

            # Проверяем пароль на сложность
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                return JsonResponse({'Status': False, 'Errors': {'password': list(password_error.messages)}})

            # Проверяем, не занят ли email
            user_serializer = UserSerializer(data=request.data)
            if user_serializer.is_valid():
                user = user_serializer.save()
                user.set_password(request.data['password'])
                # В задании почта используется как логин, поэтому копируем email в username
                user.username = request.data['email']
                user.is_active = False
                user.save()
                token, _ = ConfirmEmailToken.objects.get_or_create(user=user)
                print(f"\n---> ТОКЕН ПОДТВЕРЖДЕНИЯ ДЛЯ {user.email}: {token.key} <---\n")
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': user_serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class LoginAccount(APIView):
    """
    Класс для авторизации пользователей
    """
    def post(self, request, *args, **kwargs):
        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])

            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)
                    return JsonResponse({'Status': True, 'Token': token.key})

            return JsonResponse({'Status': False, 'Errors': 'Не удалось авторизовать'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """
    @extend_schema(
            request=inline_serializer(
                name="PartnerUpdate",
                fields={"url": serializers.URLField()}
            )
        )
    def post(self, request, *args, **kwargs):
        # Проверки на авторизацию (включим на следующем этапе)
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)})
            else:
                stream = get(url).content

                data = load_yaml(stream, Loader=Loader)

                shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
                for category in data['categories']:
                    category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                    category_object.shops.add(shop.id)
                    category_object.save()
                ProductInfo.objects.filter(shop_id=shop.id).delete()
                for item in data['goods']:
                    product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

                    product_info = ProductInfo.objects.create(product_id=product.id,
                                                              external_id=item['id'],
                                                              model=item['model'],
                                                              price=item['price'],
                                                              price_rrc=item['price_rrc'],
                                                              quantity=item['quantity'],
                                                              shop_id=shop.id)
                    for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_object.id,
                                                        value=value)

                return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

class ProductInfoView(APIView):
    """
    Класс для получения списка товаров
    """
    def get(self, request, *args, **kwargs):
        # Берем только товары из активных магазинов
        query = ProductInfo.objects.filter(shop__state=True)

        # Получаем параметры для фильтрации из URL
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')

        # Применяем фильтры, если они переданы
        if shop_id:
            query = query.filter(shop_id=shop_id)
        if category_id:
            query = query.filter(product__category_id=category_id)

        # Оптимизируем запросы к БД, чтобы не было дублей (select_related и prefetch_related)
        query = query.select_related('shop', 'product__category').prefetch_related('product_parameters__parameter')

        serializer = ProductInfoSerializer(query, many=True)
        return Response(serializer.data)

class BasketView(APIView):
    """
    Класс для работы с корзиной пользователя
    """
    @extend_schema(
        request=inline_serializer(
            name="BasketRequest",
            fields={
                "items": inline_serializer(
                    name="BasketItem",
                    fields={
                        "product_info": serializers.IntegerField(),
                        "quantity": serializers.IntegerField()
                    },
                    many=True
                )
            }
        )
    )
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется авторизация'}, status=403)

        # Ищем открытую корзину пользователя
        basket = Order.objects.filter(user=request.user, state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter'
        ).distinct()

        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется авторизация'}, status=403)

        items_dict = request.data.get('items')
        if items_dict:
            # Находим открытую корзину или создаем новую
            basket, _ = Order.objects.get_or_create(user=request.user, state='basket')

            # Добавляем или обновляем товары в корзине
            for order_item in items_dict:
                product_info_id = order_item.get('product_info')
                quantity = order_item.get('quantity')
                if product_info_id and quantity:
                    OrderItem.objects.update_or_create(
                        order=basket,
                        product_info_id=product_info_id,
                        defaults={'quantity': quantity}
                    )
            return JsonResponse({'Status': True})
        return JsonResponse({'Status': False, 'Errors': 'Не переданы товары'})

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется авторизация'}, status=403)

        items = request.data.get('items') # Ожидаем список ID удаляемых позиций
        if items:
            query = Order.objects.filter(user=request.user, state='basket').first()
            if query:
                OrderItem.objects.filter(order=query, product_info_id__in=items).delete()
                return JsonResponse({'Status': True})
        return JsonResponse({'Status': False, 'Errors': 'Не переданы ID товаров'})

class ContactView(APIView):
    """
    Класс для работы с контактами покупателей
    """
    @extend_schema(
        request=inline_serializer(
            name="ContactRequest",
            fields={
                "city": serializers.CharField(),
                "street": serializers.CharField(),
                "phone": serializers.CharField()
            }
        )
    )
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется авторизация'}, status=403)
        contact = Contact.objects.filter(user=request.user)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется авторизация'}, status=403)

        if {'city', 'street', 'phone'}.issubset(request.data):
            # Создаем изменяемую копию данных, чтобы добавить ID пользователя
            data = request.data.copy()
            data['user'] = request.user.id
            serializer = ContactSerializer(data=data)

            if serializer.is_valid():
                serializer.save(user=request.user)
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы (city, street, phone)'})

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется авторизация'}, status=403)

        items = request.data.get('items')
        if items:
            Contact.objects.filter(id__in=items, user=request.user).delete()
            return JsonResponse({'Status': True})
        return JsonResponse({'Status': False, 'Errors': 'Не переданы ID контактов'})


class OrderView(APIView):
    """
    Класс для подтверждения заказа и получения истории заказов
    """
    @extend_schema(
        request=inline_serializer(
            name="OrderRequest",
            fields={
                "id": serializers.IntegerField(),
                "contact": serializers.IntegerField()
            }
        )
    )
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется авторизация'}, status=403)

        # Получаем все заказы, кроме тех, что еще в статусе корзины
        order = Order.objects.filter(
            user=request.user).exclude(state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').distinct()

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется авторизация'}, status=403)

        if {'id', 'contact'}.issubset(request.data):
            try:
                is_updated = Order.objects.filter(
                    user=request.user, id=request.data['id']).update(
                    contact_id=request.data['contact'],
                    state='new')
            except Exception as e:
                return JsonResponse({'Status': False, 'Errors': str(e)})

            if is_updated:
                # Генерируем и отправляем письмо
                msg = EmailMultiAlternatives(
                    # Заголовок письма
                    f"Обновление статуса заказа",
                    # Тело письма
                    f"Заказ №{request.data['id']} успешно сформирован и переведен в статус 'Новый'.",
                    # От кого (берем из settings.py)
                    settings.DEFAULT_FROM_EMAIL,
                    # Кому (email текущего пользователя)
                    [request.user.email]
                )
                msg.send()

                return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы (id заказа и ID контакта)'})

class ConfirmAccount(APIView):
    """
    Класс для подтверждения электронной почты
    """
    @extend_schema(
        request=inline_serializer(
            name="ConfirmAccountRequest",
            fields={
                "email": serializers.EmailField(),
                "token": serializers.CharField()
            }
        )
    )
    def post(self, request, *args, **kwargs):
        if {'email', 'token'}.issubset(request.data):
            token = ConfirmEmailToken.objects.filter(
                user__email=request.data['email'],
                key=request.data['token']
            ).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': 'Неправильно указан токен или email'})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})
