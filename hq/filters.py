import re
import unicodedata
from datetime import timedelta
from django.utils import timezone
from .models import BannedTerm, MessageViolation

LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t",
                      "@": "a", "$": "s", "!": "i"})

LINK_RE = re.compile(
    r"(https?:|www\.|\b[a-z0-9-]+\.(com|net|org|ng|io|co|me|gov|edu|info|app|link|ly|xyz|biz|tv)\b"
    r"|\b(t|wa)\.me\b|\bd[o0]t\s*(com|ng|net|org)\b)"
)
EMAIL_RE = re.compile(r"[\w.+-]+\s*(@|\[at\]|\(at\))\s*[\w-]+")
PHONE_RE = re.compile(r"(?:\+?\d[\s\-.()]*){9,}")

def _normalize(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.lower().translate(LEET)

def _letters(text):
    return re.sub(r"[^a-z]", "", text)

def check_message(text):
    """Returns a reason string if the message must be blocked, otherwise None."""
    low = text.lower()
    if LINK_RE.search(low) or EMAIL_RE.search(low):
        return "link"
    if PHONE_RE.search(text):
        return "contact"

    norm = _normalize(text)
    squashed = _letters(norm)
    for t in BannedTerm.objects.all():
        n = _normalize(t.term)
        if t.whole_word:
            if re.search(rf"(?<![a-z]){re.escape(n)}(?![a-z])", norm):
                return "term"
        else:
            s = _letters(n)
            if s and s in squashed:
                return "term"
    return None

def is_locked(agent, strikes=3, minutes=10):
    since = timezone.now() - timedelta(minutes=minutes)
    return MessageViolation.objects.filter(agent=agent, attempted_at__gte=since).count() >= strikes