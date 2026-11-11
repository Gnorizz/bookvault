from django import forms
from django.contrib import admin
from .models import Agent, Case, Memo, AccessLog, Message, BannedTerm, MessageViolation

class AgentAdminForm(forms.ModelForm):
    new_password = forms.CharField(
        required=False, widget=forms.PasswordInput,
        help_text="Type a password to set or change it. Leave blank to keep the current one.")

    class Meta:
        model = Agent
        fields = ["service_number", "codename", "full_name", "clearance_level",
                  "unit", "posting", "photo", "is_active"]

    def save(self, commit=True):
        agent = super().save(commit=False)
        pw = self.cleaned_data.get("new_password")
        if pw:
            agent.set_password(pw)
        if commit:
            agent.save()
        return agent

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    form = AgentAdminForm
    fields = ["service_number", "codename", "full_name", "clearance_level",
              "unit", "posting", "photo", "is_active", "new_password"]
    list_display = ("service_number", "codename", "clearance_level", "is_active")

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("case_number", "title", "agent", "status", "priority", "required_level")

@admin.register(Memo)
class MemoAdmin(admin.ModelAdmin):
    list_display = ("subject", "agent", "sender", "sent_at", "is_read")

@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ("agent", "timestamp", "ip_address", "success")

@admin.register(BannedTerm)
class BannedTermAdmin(admin.ModelAdmin):
    list_display = ("term", "whole_word")

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "recipient", "priority", "sent_at", "read_at")

@admin.register(MessageViolation)
class MessageViolationAdmin(admin.ModelAdmin):
    list_display = ("agent", "recipient", "reason", "attempted_at")