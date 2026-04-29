"""
Function-based views для Кибер-Сақшы приложения.
"""
import json
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from .models import ChatThread, ChatReply, UserProfile
from .phishing_scenarios import PHISHING_DM_SCENARIOS
from .progress import build_module_progress

# Тапсырма слагы → атауы мен url name
LEARN_TASKS_META = [
    {'slug': 'phishing', 'title': 'Фишинг симуляторы', 'url_name': 'phishing'},
    {'slug': 'password', 'title': 'Құпия сөз тексергіш', 'url_name': 'password'},
    {'slug': 'links', 'title': 'Сенімді сілтемелер', 'url_name': 'links'},
    {'slug': 'spam', 'title': 'Спам және фишинг', 'url_name': 'spam'},
    {'slug': 'quiz', 'title': 'Интерактивті тест', 'url_name': 'quiz'},
    {'slug': 'ai_detect', 'title': 'ЖИ мен шынды ажырату', 'url_name': 'ai_detect'},
    {'slug': 'qr_simulator', 'title': 'QR код симуляторы', 'url_name': 'qr_simulator'},
    {'slug': 'sms_drag', 'title': 'SMS сүйреу симуляторы', 'url_name': 'sms_drag'},
    {'slug': 'learn', 'title': 'Білім базасы', 'url_name': 'learn'},
    {'slug': 'theory', 'title': 'Теория', 'url_name': 'theory'},
]


def home_view(request):
    """Негізгі бет — кірусіз ашылатын басты көрініс."""
    return render(request, 'home.html')


def register_view(request):
    """Тіркелу - жаңа пайдаланушы жасау."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        avatar_file = request.FILES.get('avatar')
        if not username:
            messages.error(request, 'Пайдаланушы атын енгізіңіз.')
            return render(request, 'register.html')
        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'Бұл пайдаланушы аты бұрыннан бар.')
            return render(request, 'register.html')
        if password != password_confirm:
            messages.error(request, 'Құпия сөздер сәйкес келмейді.')
            return render(request, 'register.html')
        try:
            validate_password(password, user=User(username=username))
        except ValidationError as e:
            for msg in e.messages:
                messages.error(request, msg)
            return render(request, 'register.html')
        user = User.objects.create_user(username=username, password=password)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if avatar_file:
            profile.avatar = avatar_file
            profile.save()
        auth_login(request, user)
        messages.success(request, 'Тіркелу сәтті аяқталды.')
        return redirect('dashboard')
    return render(request, 'register.html')


def login_view(request):
    """Кіру беті — GET форма, POST тексеру."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('dashboard')
            messages.error(request, 'Қате логин немесе құпия сөз.')
        else:
            messages.error(request, 'Логин мен құпия сөзді енгізіңіз.')
    return render(request, 'login.html')


def dashboard_view(request):
    """Личный кабинет - дашборд с модулями."""
    if not request.user.is_authenticated:
        return redirect('login')
    username = request.user.get_username()
    return render(request, 'dashboard.html', {
        'username': username,
        'mod': build_module_progress(request),
    })


def phishing_view(request):
    """Фишинг симулятор - определение подозрительных сообщений."""
    return render(request, 'phishing.html', {
        'phishing_scenarios': PHISHING_DM_SCENARIOS,
    })


def phishing_check_view(request):
    """
    API: фишинг симуляторы. POST JSON: scenario_id (int), is_trap (bool).
    is_trap=True — пайдаланушы «фишинг/тұзақ» деп белгіледі.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    data = {}
    if request.content_type == 'application/json' and request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            pass
    scenario_id = data.get('scenario_id')
    is_trap = bool(data.get('is_trap', False))

    scenario = next((s for s in PHISHING_DM_SCENARIOS if s['id'] == scenario_id), None)
    if scenario is None:
        return JsonResponse({'error': 'Жоқ сценарий'}, status=400)

    is_phishing = scenario['is_phishing']
    is_correct = is_trap == is_phishing
    if is_correct:
        msg = 'Дұрыс!'
    elif is_phishing:
        msg = 'Қате! Бұл фишинг тұзағы — «Бұл тұзақ» деген дұрыс болар еді.'
    else:
        msg = 'Қате! Бұл ресми немесе бейбіт хабар — «Бұл сенімді» деген дұрыс.'

    session_key = 'phishing_results'
    if session_key not in request.session:
        request.session[session_key] = []
    request.session[session_key].append({
        'is_correct': is_correct,
        'user_choice': 'trap' if is_trap else 'trusted',
        'scenario_id': scenario_id,
    })
    request.session.modified = True

    return JsonResponse({'is_correct': is_correct, 'message': msg})


def password_view(request):
    """Проверка надёжности пароля."""
    return render(request, 'password.html')


def password_check_view(request):
    """
    API: проверка силы пароля на сервере.
    POST: { "password": "..." }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    import re
    password = request.POST.get('password', '')
    if not password and request.content_type == 'application/json' and request.body:
        try:
            data = json.loads(request.body)
            password = data.get('password', '')
        except json.JSONDecodeError:
            pass

    # Простая логика оценки пароля
    score = 0
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if re.search(r'[a-z]', password) and re.search(r'[A-Z]', password):
        score += 1
    if re.search(r'\d', password):
        score += 1
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1

    # Оценка: 0-1 слабый, 2 средний, 3-4 хороший, 5 отличный
    if score <= 1:
        strength = 'weak'
        strength_text = 'ӨТЕ ӘЛСІЗ'
        breaking_time = '2 СЕКУНД'
    elif score == 2:
        strength = 'medium'
        strength_text = 'ӘЛСІЗ'
        breaking_time = '1 САҒАТ'
    elif score == 3:
        strength = 'good'
        strength_text = 'ОРТАША'
        breaking_time = '1 ЖЫЛ'
    elif score == 4:
        strength = 'strong'
        strength_text = 'КҮШТІ'
        breaking_time = '100 ЖЫЛ'
    else:
        strength = 'very_strong'
        strength_text = 'ӨТЕ КҮШТІ'
        breaking_time = 'МҮМКІН ЕМЕС'

    return JsonResponse({
        'strength': strength,
        'strength_text': strength_text,
        'breaking_time': breaking_time,
        'score': score,
    })


def links_view(request):
    """Проверка надёжных ссылок."""
    return render(request, 'links.html')


def spam_view(request):
    """Спам и фишинг - определение подозрительных писем."""
    return render(request, 'spam.html')


def quiz_view(request):
    """Интерактивный тест."""
    return render(request, 'quiz.html')


def learn_view(request):
    """База знаний."""
    saved = request.session.get('saved_tasks', [])
    return render(request, 'learn.html', {'saved_task_slugs': saved})


def saved_tasks_view(request):
    """Сақталған тапсырмалар тізімі."""
    if not request.user.is_authenticated:
        return redirect('login')
    saved_slugs = request.session.get('saved_tasks', [])
    tasks = []
    for meta in LEARN_TASKS_META:
        if meta['slug'] in saved_slugs:
            tasks.append({
                'slug': meta['slug'],
                'title': meta['title'],
                'url': reverse(meta['url_name']),
            })
    return render(request, 'saved_tasks.html', {
        'username': request.user.get_username(),
        'saved_tasks': tasks,
    })


def saved_tasks_toggle_view(request):
    """API: тапсырманы сақтау / алып тастау. POST JSON: { slug: 'phishing' }"""
    if request.method != 'POST' or not request.user.is_authenticated:
        return JsonResponse({'error': 'Рұқсат жоқ'}, status=405)
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}
    slug = (data.get('slug') or '').strip()
    valid = {m['slug'] for m in LEARN_TASKS_META}
    if slug not in valid:
        return JsonResponse({'error': 'Жоқ тапсырма'}, status=400)
    saved = list(request.session.get('saved_tasks', []))
    if slug in saved:
        saved.remove(slug)
        saved_flag = False
    else:
        saved.append(slug)
        saved_flag = True
    request.session['saved_tasks'] = saved
    request.session.modified = True
    return JsonResponse({'saved': saved_flag, 'slug': slug})


def stats_view(request):
    """Статистика пользователя."""
    if not request.user.is_authenticated:
        return redirect('login')
    username = request.user.get_username()
    phishing_results = request.session.get('phishing_results', [])
    correct_count = sum(1 for r in phishing_results if r.get('is_correct'))
    total_count = len(phishing_results)
    mod = build_module_progress(request)
    quiz_prog = request.session.get('quiz_progress') or {}
    quiz_score = int(quiz_prog.get('score', 0) or 0)
    points = correct_count * 15 + quiz_score * 10
    level = 1 + min(9, points // 200) if points else 1
    modules_finished = sum(1 for k in ('phishing', 'quiz', 'ai_detect') if mod[k]['pct'] >= 100)
    return render(request, 'stats.html', {
        'username': username,
        'phishing_correct': correct_count,
        'phishing_total': total_count,
        'mod': mod,
        'stats_points': points,
        'stats_level': level,
        'stats_modules_done': modules_finished,
    })


def settings_view(request):
    """Баптаулар — профиль суретін жүктеу."""
    if not request.user.is_authenticated:
        return redirect('login')
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST' and request.FILES.get('avatar'):
        profile.avatar = request.FILES['avatar']
        profile.save()
        messages.success(request, 'Профиль суреті сақталды.')
        return redirect('settings')
    return render(request, 'settings.html', {
        'username': request.user.get_username(),
        'profile': profile,
    })


def logout_view(request):
    """Выход из системы."""
    auth_logout(request)
    return redirect('home')


# === Теория (algorithm.42web.io стилі) ===
def theory_view(request):
    """Теория бөлімі - тақырыптар бойынша оқу материалдары."""
    topic = request.GET.get('topic', 'intro')
    return render(request, 'theory.html', {'topic': topic})


# === Чат (Threads стилі - сұрақ-жауап) ===
def chat_view(request):
    """Оқушылар арасындағы чат - тредтар (сұрақ-жауап)."""
    if not request.user.is_authenticated:
        return redirect('login')
    threads = ChatThread.objects.all()[:50]
    return render(request, 'chat.html', {'threads': threads})


def chat_thread_create_view(request):
    """Жаңа сұрақ (тред) жасау."""
    if not request.user.is_authenticated or request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = json.loads(request.body) if request.body else {}
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    if not title and not content:
        return JsonResponse({'error': 'Тақырып пен мәтінді енгізіңіз'}, status=400)
    if not title:
        title = content[:50] + ('...' if len(content) > 50 else '')
    thread = ChatThread.objects.create(
        author=request.user.get_username(),
        title=title,
        content=content
    )
    return JsonResponse({
        'id': thread.id,
        'title': thread.title,
        'content': thread.content,
        'author': thread.author,
        'created_at': thread.created_at.isoformat(),
    })


def chat_reply_create_view(request, thread_id):
    """Тредке жауап жазу."""
    if not request.user.is_authenticated or request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    thread = get_object_or_404(ChatThread, id=thread_id)
    data = json.loads(request.body) if request.body else {}
    content = data.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Жауапты енгізіңіз'}, status=400)
    reply = ChatReply.objects.create(
        thread=thread,
        author=request.user.get_username(),
        content=content
    )
    return JsonResponse({
        'id': reply.id,
        'content': reply.content,
        'author': reply.author,
        'created_at': reply.created_at.isoformat(),
    })


def chat_threads_api_view(request):
    """API: барлық тредтар мен жауаптар."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Кіру керек'}, status=401)
    threads = ChatThread.objects.prefetch_related('replies').all()[:30]
    data = []
    for t in threads:
        data.append({
            'id': t.id,
            'title': t.title,
            'content': t.content,
            'author': t.author,
            'created_at': t.created_at.isoformat(),
            'replies': [{'id': r.id, 'author': r.author, 'content': r.content, 'created_at': r.created_at.isoformat()} for r in t.replies.all()]
        })
    return JsonResponse({'threads': data})


# === "ЖИ мен шынды ажырата білу" тапсырмасы ===
def ai_detect_view(request):
    """ЖИ (AI) мен адам жазыған мәтінді ажырату тапсырмасы."""
    return render(request, 'ai_detect.html')


def ai_detect_check_view(request):
    """API: ЖИ/адам жауабын тексеру."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = json.loads(request.body) if request.body else {}
    sample_id = data.get('sample_id')
    user_choice = data.get('choice')  # 'ai' or 'human'
    answers = {
        1: 'human', 2: 'ai', 3: 'human', 4: 'ai', 5: 'human',
        6: 'ai', 7: 'human', 8: 'human', 9: 'ai', 10: 'human',
    }
    expected = answers.get(sample_id)
    correct = expected == user_choice
    if correct:
        msg = 'Дұрыс!'
    else:
        msg = 'Қате! Дұрыс жауап: ' + ('адам жазыған' if expected == 'human' else 'ЖИ жазыған')
    if sample_id is not None:
        try:
            sid = int(sample_id)
        except (TypeError, ValueError):
            sid = None
        if sid is not None and sid in answers:
            ans_list = list(request.session.get('ai_detect_answered', []))
            if sid not in ans_list:
                ans_list.append(sid)
                request.session['ai_detect_answered'] = ans_list
                request.session.modified = True
    return JsonResponse({'is_correct': correct, 'message': msg})


def quiz_progress_view(request):
    """Тест прогрессін сессияға жазу (дашборд үшін)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        data = {}
    from .progress import QUIZ_TOTAL
    total = int(data.get('total') or QUIZ_TOTAL)
    if total <= 0:
        total = QUIZ_TOTAL
    try:
        answered = max(0, int(data.get('answered', 0)))
    except (TypeError, ValueError):
        answered = 0
    answered = min(answered, total)
    prev = request.session.get('quiz_progress') or {}
    prev_a = int(prev.get('answered', 0) or 0)
    payload = {'answered': max(prev_a, answered), 'total': total}
    if data.get('score') is not None:
        try:
            sc = int(data['score'])
            prev_s = int(prev.get('score', 0) or 0)
            payload['score'] = max(prev_s, sc)
        except (TypeError, ValueError):
            pass
    request.session['quiz_progress'] = payload
    request.session.modified = True
    return JsonResponse({'ok': True})


# === QR код симуляторы ===
def qr_simulator_view(request):
    """QR код скандау симуляторы - фишинг қауіпін көрсету."""
    return render(request, 'qr_simulator.html')


# === SMS сүйреу симуляторы (drag-and-drop) ===
def sms_drag_view(request):
    """SMS хабарын талдау — жауаптарды сүйреп немесе басып орналастыру."""
    return render(request, 'sms_drag.html')
