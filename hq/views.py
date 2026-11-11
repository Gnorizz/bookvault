from functools import wraps
from django.contrib.auth import logout
from django.http import Http404
from django.shortcuts import render, redirect
from datetime import timedelta
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Message, MessageViolation
from .filters import check_message, is_locked
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

RETENTION_HOURS = 72
MAX_LEN = 1000

def purge_old_messages():
    cutoff = timezone.now() - timedelta(hours=RETENTION_HOURS)
    Message.objects.filter(sent_at__lt=cutoff).delete()

@agent_required
def messages_home(request):
    me = request.agent
    purge_old_messages()
    rows = []
    for other in Agent.objects.filter(is_active=True).exclude(pk=me.pk).order_by("codename"):
        unread = Message.objects.filter(sender=other, recipient=me, read_at__isnull=True).count()
        last = Message.objects.filter(
            Q(sender=me, recipient=other) | Q(sender=other, recipient=me)
        ).order_by("-sent_at").first()
        rows.append({"agent": other, "unread": unread, "last": last})
    rows.sort(key=lambda r: r["last"].sent_at.timestamp() if r["last"] else 0, reverse=True)
    return render(request, "hq/messages.html", {"rows": rows})

@agent_required
def thread(request, codename):
    me = request.agent
    other = get_object_or_404(Agent, codename__iexact=codename, is_active=True)
    if other.pk == me.pk:
        raise Http404()
    purge_old_messages()

    error = None
    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        priority = "PRIORITY" if request.POST.get("priority") == "PRIORITY" else "ROUTINE"
        if not body:
            error = "Message cannot be empty."
        elif len(body) > MAX_LEN:
            error = f"Message exceeds {MAX_LEN} characters."
        elif is_locked(me):
            error = "Messaging access suspended pending review. Contact your unit administrator."
        else:
            reason = check_message(body)
            if reason:
                MessageViolation.objects.create(agent=me, recipient=other, text=body, reason=reason)
                error = "Message blocked: restricted content detected. This attempt has been logged."
            else:
                Message.objects.create(sender=me, recipient=other, body=body, priority=priority)
                return redirect("hq:thread", codename=other.codename)

    Message.objects.filter(sender=other, recipient=me, read_at__isnull=True).update(read_at=timezone.now())
    convo = Message.objects.filter(
        Q(sender=me, recipient=other) | Q(sender=other, recipient=me)
    ).select_related("sender").order_by("sent_at")
    return render(request, "hq/thread.html", {"me": me, "other": other, "convo": convo, "error": error})