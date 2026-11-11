from django.conf import settings

def agency(request):
    return {
        "AGENCY_NAME": settings.AGENCY_NAME,
        "AGENCY_SHORT": settings.AGENCY_SHORT,
    }