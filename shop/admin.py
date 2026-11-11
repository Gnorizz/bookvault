from django.contrib import admin
from .models import Book, Order, OrderItem

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "price")
    search_fields = ("title", "author")

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("reference", "name", "total", "status", "created")
    list_filter = ("status",)
    inlines = [OrderItemInline]