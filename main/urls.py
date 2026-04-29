"""
URL маршруты для main приложения.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('theory/', views.theory_view, name='theory'),
    path('chat/', views.chat_view, name='chat'),
    path('chat/api/threads/', views.chat_threads_api_view, name='chat_api_threads'),
    path('chat/thread/create/', views.chat_thread_create_view, name='chat_thread_create'),
    path('chat/thread/<int:thread_id>/reply/', views.chat_reply_create_view, name='chat_reply'),
    path('phishing/', views.phishing_view, name='phishing'),
    path('phishing/check/', views.phishing_check_view, name='phishing_check'),
    path('password/', views.password_view, name='password'),
    path('password/check/', views.password_check_view, name='password_check'),
    path('links/', views.links_view, name='links'),
    path('spam/', views.spam_view, name='spam'),
    path('quiz/', views.quiz_view, name='quiz'),
    path('api/quiz/progress/', views.quiz_progress_view, name='quiz_progress'),
    path('learn/', views.learn_view, name='learn'),
    path('saved-tasks/', views.saved_tasks_view, name='saved_tasks'),
    path('api/saved-tasks/toggle/', views.saved_tasks_toggle_view, name='saved_tasks_toggle'),
    path('ai-detect/', views.ai_detect_view, name='ai_detect'),
    path('ai-detect/check/', views.ai_detect_check_view, name='ai_detect_check'),
    path('qr-simulator/', views.qr_simulator_view, name='qr_simulator'),
    path('sms-drag/', views.sms_drag_view, name='sms_drag'),
    path('stats/', views.stats_view, name='stats'),
    path('settings/', views.settings_view, name='settings'),
]
