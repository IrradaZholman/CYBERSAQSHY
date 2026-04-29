"""Дашборд/статистика үшін модуль прогресі (сессия деректері)."""
from .phishing_scenarios import PHISHING_DM_SCENARIOS

PHISHING_TOTAL = len(PHISHING_DM_SCENARIOS)
AI_DETECT_TOTAL = 10
# templates/quiz.html ішіндегі questions ұзындығымен сәйкес болуы керек
QUIZ_TOTAL = 18


def _pct(done: int, total: int) -> int:
    if total <= 0:
        return 0
    return min(100, int(round(100 * done / total)))


def build_module_progress(request) -> dict:
    """Әр модуль үшін {'pct': int, 'started': bool, 'label': str}."""
    session = request.session

    results = session.get('phishing_results', [])
    ph_ids = {r['scenario_id'] for r in results if r.get('scenario_id') is not None}
    ph_pct = _pct(len(ph_ids), PHISHING_TOTAL)

    quiz = session.get('quiz_progress') or {}
    q_answered = int(quiz.get('answered', 0) or 0)
    q_total = int(quiz.get('total', QUIZ_TOTAL) or QUIZ_TOTAL)
    if q_total <= 0:
        q_total = QUIZ_TOTAL
    quiz_pct = _pct(q_answered, q_total)

    ai_ids = session.get('ai_detect_answered') or []
    if isinstance(ai_ids, list):
        ai_done = len({int(x) for x in ai_ids if x is not None})
    else:
        ai_done = 0
    ai_pct = _pct(ai_done, AI_DETECT_TOTAL)

    zeros = {'pct': 0, 'started': False}

    out = {
        'phishing': {'pct': ph_pct, 'started': ph_pct > 0},
        'quiz': {'pct': quiz_pct, 'started': quiz_pct > 0},
        'ai_detect': {'pct': ai_pct, 'started': ai_pct > 0},
        'password': zeros.copy(),
        'links': zeros.copy(),
        'spam': zeros.copy(),
        'qr_simulator': zeros.copy(),
        'sms_drag': zeros.copy(),
    }
    for info in out.values():
        info['label'] = progress_label_kk(info)
    return out


def progress_label_kk(info: dict) -> str:
    """Карта астыңғы мәтіні."""
    if info['pct'] > 0:
        return f"{info['pct']}% өтілді"
    return 'Жаңа тапсырма'
