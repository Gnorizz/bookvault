from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
import datetime

class Agent(models.Model):
    service_number = models.CharField(max_length=20, unique=True)
    codename = models.CharField(max_length=30, unique=True)
    full_name = models.CharField(max_length=100)
    clearance_level = models.PositiveSmallIntegerField(default=1)
    unit = models.CharField(max_length=100, blank=True)
    posting = models.CharField(max_length=100, blank=True)
    photo = models.CharField(max_length=100, default="agent.jpg",
                             help_text="Filename inside static/hq/images/")
    password = models.CharField(max_length=128, blank=True)
    is_active = models.BooleanField(default=True)

    def set_password(self, raw):
        self.password = make_password(raw)

    def check_password(self, raw):
        return bool(self.password) and check_password(raw, self.password)

    def __str__(self):
        return f"{self.service_number} ({self.codename})"


class Case(models.Model):
    STATUS = [("ACTIVE", "Active"), ("PENDING", "Pending review"), ("CLOSED", "Closed")]
    PRIORITY = [("ROUTINE", "Routine"), ("PRIORITY", "Priority"), ("URGENT", "Urgent")]

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="cases")
    case_number = models.CharField(max_length=30)
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=STATUS, default="ACTIVE")
    priority = models.CharField(max_length=10, choices=PRIORITY, default="ROUTINE")
    summary = models.TextField(blank=True)
    required_level = models.PositiveSmallIntegerField(default=1)
    opened = models.DateField(default=timezone.now)

    def __str__(self):
        return self.case_number


class Memo(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="memos")
    sender = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    sent_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.subject


class AccessLog(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="logs")
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    success = models.BooleanField(default=True)

    class Meta:
        ordering = ["-timestamp"]

class Message(models.Model):
    PRIORITY = [("ROUTINE", "Routine"), ("PRIORITY", "Priority")]
    sender = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="received_messages")
    body = models.TextField(max_length=1000)
    priority = models.CharField(max_length=10, choices=PRIORITY, default="ROUTINE")
    sent_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)


class BannedTerm(models.Model):
    term = models.CharField(max_length=100, unique=True)
    whole_word = models.BooleanField(
        default=False, help_text="Match only as a standalone word (use this for short words).")

    def __str__(self):
        return self.term


class MessageViolation(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="violations")
    recipient = models.ForeignKey(Agent, null=True, blank=True,
                                  on_delete=models.SET_NULL, related_name="+")
    text = models.TextField()
    reason = models.CharField(max_length=20)
    attempted_at = models.DateTimeField(auto_now_add=True)        

class Equipment(models.Model):
    STATUS = [("ISSUED", "Issued"), ("RETURNED", "Returned"), ("REPORTED", "Reported lost")]
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="equipment")
    item = models.CharField(max_length=120)
    category = models.CharField(max_length=60, blank=True)
    serial_number = models.CharField(max_length=60)
    issued_on = models.DateField(default=datetime.date.today)
    status = models.CharField(max_length=10, choices=STATUS, default="ISSUED")
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name_plural = "equipment"

    def __str__(self):
        return f"{self.item} ({self.serial_number})"


class Training(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="trainings")
    course = models.CharField(max_length=150)
    provider = models.CharField(max_length=100, blank=True)
    completed_on = models.DateField()
    expires_on = models.DateField(null=True, blank=True, help_text="Leave blank if it doesn't expire")
    certificate_no = models.CharField(max_length=40, blank=True)

    @property
    def status(self):
        if not self.expires_on:
            return "NO EXPIRY"
        today = datetime.date.today()
        if self.expires_on < today:
            return "EXPIRED"
        if (self.expires_on - today).days <= 60:
            return "EXPIRING SOON"
        return "VALID"

    @property
    def status_class(self):
        return {"NO EXPIRY": "none", "EXPIRED": "expired",
                "EXPIRING SOON": "soon", "VALID": "valid"}[self.status]

    def __str__(self):
        return self.course