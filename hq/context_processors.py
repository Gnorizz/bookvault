from django.conf import settings
from .models import Agent, Message

def agency(request):
    ctx = {"AGENCY_NAME": settings.AGENCY_NAME, "AGENCY_SHORT": settings.AGENCY_SHORT}
    agent_id = request.session.get("agent_id")
    if agent_id:
        agent = Agent.objects.filter(pk=agent_id, is_active=True).first()
        if agent:
            ctx["nav_agent"] = agent
            ctx["unread_count"] = Message.objects.filter(
                recipient=agent, read_at__isnull=True).count()
            ctx["session_seconds"] = request.session.get_expiry_age()
    return ctx