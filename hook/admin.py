from django.contrib import admin

from .models import Conversation, WhiteList

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'context', 'token_count', 'last_token_used',
                    'image_count','last_image_used', 'is_subscribed')
    search_fields = ('phone_number', 'context')
    readonly_fields = ('updated_at',)
    ordering = ('-updated_at','token_count')

@admin.register(WhiteList)
class WhiteListAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'updated_at')
    search_fields = ('phone_number',)
    readonly_fields = ('updated_at',)
    ordering = ('-updated_at',)