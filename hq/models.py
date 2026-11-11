from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

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