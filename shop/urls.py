from django.urls import path
from . import views

app_name = "shop"
urlpatterns = [
    path("", views.home, name="home"),
    path("book/<int:pk>/", views.book_detail, name="book"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:pk>/", views.cart_add, name="cart_add"),
    path("cart/update/<int:pk>/", views.cart_update, name="cart_update"),
    path("checkout/", views.checkout, name="checkout"),
    path("payment/callback/", views.payment_callback, name="payment_callback"),
    path("order/<str:reference>/", views.order_done, name="order_done"),
]