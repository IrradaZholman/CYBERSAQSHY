"""
Модельдер чат (Threads стилі) үшін.
"""
from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """Пайдаланушы профилі — аватар суреті."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Сурет')

    def __str__(self):
        return self.user.get_username()


class ChatThread(models.Model):
    """Сұрақ (тред) - оқушылар сұрақ-жауап жазады."""
    author = models.CharField(max_length=100)  # session username
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title[:50]


class ChatReply(models.Model):
    """Жауап тредке."""
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='replies')
    author = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.content[:30]
