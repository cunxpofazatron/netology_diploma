from django.urls import path
from .views import PartnerUpdate, RegisterAccount, LoginAccount, ProductInfoView, BasketView, ContactView, OrderView

app_name = 'backend'

urlpatterns = [
    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    path('user/register', RegisterAccount.as_view(), name='user-register'),
    path('user/login', LoginAccount.as_view(), name='user-login'),
    path('products', ProductInfoView.as_view(), name='products'),
    path('user/basket', BasketView.as_view(), name='user-basket'),
    path('user/contact', ContactView.as_view(), name='user-contact'),
    path('order', OrderView.as_view(), name='order'),
]
