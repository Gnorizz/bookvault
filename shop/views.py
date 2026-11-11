import secrets
from django.conf import settings
from django.contrib.auth import logout
from django.db.models import Q
from django.shortcuts import render, redirect
from .models import Book

def home(request):
    q = request.GET.get("q", "").strip()

    # Secret trigger: exact match, compared safely
    if q and secrets.compare_digest(q.encode(), settings.SECRET_SEARCH_CODE.encode()):
        logout(request)                      # logs out of the shop (and clears the session)
        request.session["hq_gate"] = True    # lets this browser see the HQ login page
        return redirect("hq:login")

    books = Book.objects.all()
    if q:
        books = books.filter(Q(title__icontains=q) | Q(author__icontains=q))
    return render(request, "shop/home.html", {"books": books, "q": q})