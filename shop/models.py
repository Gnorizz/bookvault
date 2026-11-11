from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)
    cover = models.CharField(max_length=100, blank=True,
                             help_text="Filename inside static/shop/covers/ (optional)")

    def __str__(self):
        return self.title


class Order(models.Model):
    STATUS = [("PENDING", "Pending"), ("PAID", "Paid"), ("FAILED", "Failed")]
    reference = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    address = models.TextField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS, default="PENDING")
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.reference


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    title = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)