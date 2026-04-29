from django.contrib import admin
from .models import ChatThread, ChatReply, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'avatar')
    search_fields = ('user__username',)


@admin.register(ChatThread)
class ChatThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')


@admin.register(ChatReply)
class ChatReplyAdmin(admin.ModelAdmin):
    list_display = ('thread', 'author', 'content', 'created_at')
