from django.contrib import admin

from .models import Conversation

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'context', 'updated_at')
    search_fields = ('phone_number', 'context')
    readonly_fields = ('updated_at',)
