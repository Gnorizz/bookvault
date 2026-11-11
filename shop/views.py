import secrets
import uuid
import requests
from django.conf import settings
from django.contrib.auth import logout
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from .cart import Cart
from .models import Book, Order, OrderItem

PAYSTACK_API = "https://api.paystack.co"

def _headers():
    return {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}

def home(request):
    q = request.GET.get("q", "").strip()

    # Secret trigger
    if q and secrets.compare_digest(q.encode(), settings.SECRET_SEARCH_CODE.encode()):
        logout(request)
        request.session["hq_gate"] = True
        return redirect("hq:login")

    books = Book.objects.all().order_by("title")
    if q:
        books = books.filter(Q(title__icontains=q) | Q(author__icontains=q))
    return render(request, "shop/home.html", {"books": books, "q": q})

def book_detail(request, pk):
    return render(request, "shop/book.html", {"book": get_object_or_404(Book, pk=pk)})

def cart_view(request):
    cart = Cart(request)
    return render(request, "shop/cart.html", {"items": cart.items(), "total": cart.total()})

@require_POST
def cart_add(request, pk):
    book = get_object_or_404(Book, pk=pk)
    Cart(request).add(book.pk)
    return redirect("shop:cart")

@require_POST
def cart_update(request, pk):
    try:
        qty = int(request.POST.get("quantity", 1))
    except ValueError:
        qty = 1
    Cart(request).set(pk, qty)
    return redirect("shop:cart")

def checkout(request):
    cart = Cart(request)
    items = cart.items()
    if not items:
        return redirect("shop:cart")

    error = None
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()

        if not (name and email and phone and address):
            error = "Please fill in all delivery details."
        else:
            order = Order.objects.create(
                reference="PB-" + uuid.uuid4().hex[:12].upper(),
                name=name, email=email, phone=phone, address=address,
                total=cart.total(),
            )
            for row in items:
                OrderItem.objects.create(order=order, title=row["book"].title,
                                         price=row["book"].price, quantity=row["quantity"])
            try:
                resp = requests.post(
                    f"{PAYSTACK_API}/transaction/initialize",
                    headers=_headers(),
                    json={
                        "email": email,
                        "amount": int(order.total * 100),       # Paystack uses kobo
                        "reference": order.reference,
                        "callback_url": request.build_absolute_uri(reverse("shop:payment_callback")),
                    },
                    timeout=20,
                )
                data = resp.json()
            except (requests.RequestException, ValueError):
                data = {}
            if data.get("status"):
                return redirect(data["data"]["authorization_url"])
            order.status = "FAILED"
            order.save()
            error = "We couldn't start the payment. Please try again."

    return render(request, "shop/checkout.html",
                  {"items": items, "total": cart.total(), "error": error, "form": request.POST})

def payment_callback(request):
    reference = request.GET.get("reference") or request.GET.get("trxref")
    order = get_object_or_404(Order, reference=reference)
    if order.status != "PAID":
        try:
            resp = requests.get(f"{PAYSTACK_API}/transaction/verify/{reference}",
                                headers=_headers(), timeout=20)
            data = resp.json()
        except (requests.RequestException, ValueError):
            data = {}
        ok = bool(
            data.get("status")
            and data.get("data", {}).get("status") == "success"
            and data["data"].get("amount") == int(order.total * 100)
        )
        order.status = "PAID" if ok else "FAILED"
        order.save()
        if ok:
            Cart(request).clear()
    return redirect("shop:order_done", reference=order.reference)

def order_done(request, reference):
    order = get_object_or_404(Order, reference=reference)
    return render(request, "shop/order_done.html", {"order": order})