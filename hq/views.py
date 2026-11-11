from functools import wraps
from django.contrib.auth import logout
from django.http import Http404
from django.shortcuts import render, redirect
from .models import Agent, AccessLog

def client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")

def agent_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        agent_id = request.session.get("agent_id")
        if not agent_id:
            return redirect("hq:login")
        try:
            request.agent = Agent.objects.get(pk=agent_id, is_active=True)
        except Agent.DoesNotExist:
            request.session.pop("agent_id", None)
            return redirect("hq:login")
        return view(request, *args, **kwargs)
    return wrapper

def login_view(request):
    if not request.session.get("hq_gate") and not request.session.get("agent_id"):
        raise Http404()

    error = None
    if request.method == "POST":
        sn = request.POST.get("service_number", "").strip().upper()
        pw = request.POST.get("password", "")
        agent = Agent.objects.filter(service_number__iexact=sn, is_active=True).first()
        if agent and agent.check_password(pw):
            AccessLog.objects.create(agent=agent, ip_address=client_ip(request), success=True)
            logout(request)                         # make sure no shop login survives
            request.session["agent_id"] = agent.id
            return redirect("hq:dashboard")
        if agent:
            AccessLog.objects.create(agent=agent, ip_address=client_ip(request), success=False)
        error = "Authentication failed. This attempt has been logged."
    return render(request, "hq/login.html", {"error": error})

@agent_required
def dashboard(request):
    agent = request.agent
    successes = list(agent.logs.filter(success=True)[:2])
    last_login = successes[1] if len(successes) > 1 else None
    context = {
        "agent": agent,
        "cases": agent.cases.order_by("-opened"),
        "memos": agent.memos.order_by("-sent_at")[:6],
        "logs": agent.logs.all()[:6],
        "last_login": last_login,
        "levels": [1, 2, 3, 4, 5],
    }
    return render(request, "hq/dashboard.html", context)

def logout_view(request):
    request.session.flush()
    return redirect("shop:home")