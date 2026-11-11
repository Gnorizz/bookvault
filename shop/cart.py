from decimal import Decimal
from .models import Book

class Cart:
    def __init__(self, request):
        self.session = request.session
        self.data = dict(self.session.get("cart", {}))

    def _save(self):
        self.session["cart"] = self.data

    def add(self, book_id):
        key = str(book_id)
        self.data[key] = min(self.data.get(key, 0) + 1, 20)
        self._save()

    def set(self, book_id, qty):
        key = str(book_id)
        if qty <= 0:
            self.data.pop(key, None)
        else:
            self.data[key] = min(qty, 20)
        self._save()

    def clear(self):
        self.data = {}
        self._save()

    def items(self):
        books = Book.objects.in_bulk([int(k) for k in self.data])
        rows = []
        for key, qty in self.data.items():
            book = books.get(int(key))
            if book:
                rows.append({"book": book, "quantity": qty, "subtotal": book.price * qty})
        return rows

    def total(self):
        return sum((r["subtotal"] for r in self.items()), Decimal("0"))

    def count(self):
        return sum(self.data.values())