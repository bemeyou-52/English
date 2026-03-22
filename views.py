from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from datetime import date
from django.http import JsonResponse
import json
import random

from .models import (
    UserProfile, DailyActivity,
    Course, Lesson, LessonProgress,
    TestQuestion,
    Achievement, UserAchievement,
)

LEVEL_ORDER = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']

def get_next_level(current_level):
    try:
        idx = LEVEL_ORDER.index(current_level)
        return LEVEL_ORDER[idx + 1] if idx + 1 < len(LEVEL_ORDER) else None
    except ValueError:
        return None
# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────

def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def record_activity(user, minutes=5):
    """Record that user was active today (creates or updates DailyActivity)."""
    today = date.today()
    activity, created = DailyActivity.objects.get_or_create(user=user, day=today)
    if not created:
        activity.minutes += minutes
    else:
        activity.minutes = minutes
    activity.save()
    return activity


def check_and_award_achievements(user, profile):
    streak = profile.get_streak()
    all_achievements = Achievement.objects.all()
    for ach in all_achievements:
        if UserAchievement.objects.filter(user=user, achievement=ach).exists():
            continue
        earned = False
        if ach.condition_type == 'streak' and streak >= ach.condition_value:
            earned = True
        elif ach.condition_type == 'lessons' and profile.lessons_completed >= ach.condition_value:
            earned = True
        elif ach.condition_type == 'xp' and profile.xp >= ach.condition_value:
            earned = True
        elif ach.condition_type == 'words' and profile.words_learned >= ach.condition_value:
            earned = True
        if earned:
            UserAchievement.objects.create(user=user, achievement=ach)


# ──────────────────────────────────────────────
#  MAIN PAGES
# ──────────────────────────────────────────────

def index_view(request):
    courses = Course.objects.filter(is_active=True)[:7]
    return render(request, 'main/index.html', {'courses': courses})


def about_view(request):
    return render(request, 'main/about.html')


# ──────────────────────────────────────────────
#  AUTH
# ──────────────────────────────────────────────

def login_view(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user:
            login(request, user)
            next_url = request.POST.get('next', '/level-check/')
            return redirect(next_url)
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    next_url = request.GET.get('next', '/level-check/')
    return render(request, 'main/login.html', {'next': next_url})


def register_view(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            messages.error(request, 'Пароли не совпадают')
            return render(request, 'main/register.html')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь с таким именем уже существует')
            return render(request, 'main/register.html')
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email уже используется')
            return render(request, 'main/register.html')

        user = User.objects.create_user(username=username, email=email, password=password1)
        get_or_create_profile(user)
        login(request, user)
        messages.success(request, 'Регистрация прошла успешно!')
        return redirect('/level-check/')

    return render(request, 'main/register.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из аккаунта')
    return redirect('/')


# ──────────────────────────────────────────────
#  ONBOARDING FLOW
# ──────────────────────────────────────────────

@login_required(login_url='/login/')
def level_check_view(request):
    """Step 1: Goal & does user know their level?"""
    profile = get_or_create_profile(request.user)

    # If already fully set up — redirect to learning
    if profile.level and profile.current_lesson:
        return redirect('/learning/')

    if request.method == "POST":
        goal = request.POST.get('goal', '')
        knows_level = request.POST.get('knows_level', '')
        if goal:
            profile.goal = goal
            profile.save()
        if knows_level == 'yes':
            return redirect('/level-select/')
        elif knows_level == 'no':
            return redirect('/test/')

    return render(request, 'main/level_check.html')


@login_required(login_url='/login/')
def level_select_view(request):
    """Manual level selection."""
    if request.method == "POST":
        level = request.POST.get('level')
        if level:
            profile = get_or_create_profile(request.user)
            profile.level = level
            profile.save()
            return redirect('/learning/')
    return render(request, 'main/level_select.html')


LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
QUESTIONS_PER_BLOCK = 4
MAX_QUESTIONS = 25


def _init_test_session(request):
    request.session['adaptive_test'] = {
        'current_level': 'A1',
        'level_index': 0,
        'block_correct': 0,
        'block_total': 0,
        'is_retry': False,
        'total_asked': 0,
        'used_question_ids': [],
        'current_block_questions': [], 
        'done': False,
        'final_level': None,
    }


def _get_next_question(state):
    if not state['current_block_questions']:

        qs = list(
            TestQuestion.objects.filter(
                is_active=True,
                level=state['current_level']
            ).exclude(
                id__in=state['used_question_ids']
            )
        )

        if not qs:
            return None

        random.shuffle(qs)

        block = qs[:QUESTIONS_PER_BLOCK]
        state['current_block_questions'] = [q.id for q in block]

    # Берём следующий вопрос из блока
    question_id = state['current_block_questions'].pop(0)

    return TestQuestion.objects.get(id=question_id)


@login_required(login_url='/login/')
def test_view(request):
    """Точка входа — инициализирует сессию и открывает шаблон."""
    _init_test_session(request)

    if not TestQuestion.objects.filter(is_active=True).exists():
        return render(request, 'main/test.html', {'no_questions': True})

    return render(request, 'main/test.html', {
        'max_questions': MAX_QUESTIONS,
        'levels': LEVELS,
    })


@login_required(login_url='/login/')
def test_next_question_view(request):
    """AJAX GET — возвращает следующий вопрос или сигнал завершения."""
    state = request.session.get('adaptive_test')
    if not state:
        return JsonResponse({'error': 'no_session'}, status=400)

    # Уже завершён
    if state['done']:
        return JsonResponse({'done': True, 'final_level': state['final_level']})

    # Достигнут лимит вопросов
    if state['total_asked'] >= MAX_QUESTIONS:
        state['done'] = True
        state['final_level'] = state['current_level']
        request.session.modified = True
        return JsonResponse({'done': True, 'final_level': state['final_level']})

    q = _get_next_question(state)

    # Нет вопросов для текущего уровня — завершаем
    if not q:
        state['done'] = True
        state['final_level'] = state['current_level']
        request.session.modified = True
        return JsonResponse({'done': True, 'final_level': state['final_level']})

    return JsonResponse({
        'done': False,
        'question': {
            'id': q.id,
            'text': q.question_text,
            'option_a': q.option_a,
            'option_b': q.option_b,
            'option_c': q.option_c,
            'option_d': q.option_d,
        },
        'current_level': state['current_level'],
        'total_asked': state['total_asked'] + 1,
        'max_questions': MAX_QUESTIONS,
        'block_question': state['block_total'] + 1,
    })


@login_required(login_url='/login/')
def test_answer_view(request):
    """AJAX POST — принимает ответ, обновляет состояние, возвращает результат."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)

    state = request.session.get('adaptive_test')
    if not state:
        return JsonResponse({'error': 'no_session'}, status=400)

    question_id = data.get('question_id')
    answer = data.get('answer', '').lower()

    try:
        q = TestQuestion.objects.get(id=question_id, is_active=True)
    except TestQuestion.DoesNotExist:
        return JsonResponse({'error': 'question not found'}, status=404)

    is_correct = (answer == q.correct_option)

    # Обновляем счётчики
    state['used_question_ids'].append(q.id)
    state['total_asked'] += 1
    state['block_total'] += 1
    if is_correct:
        state['block_correct'] += 1

    block_done = state['block_total'] >= QUESTIONS_PER_BLOCK
    transition = None
    next_level = state['current_level']

    if block_done:
        correct = state['block_correct']
        wrong = QUESTIONS_PER_BLOCK - correct
        level_index = state['level_index']
        is_retry = state['is_retry']

        # ── 3 или 4 правильных → повышаем уровень ──────────────────────────
        if correct >= 3:
            state['is_retry'] = False
            if level_index + 1 >= len(LEVELS):
                # Уже максимальный уровень
                state['done'] = True
                state['final_level'] = LEVELS[level_index]
                transition = 'finish'
            else:
                level_index += 1
                state['level_index'] = level_index
                state['current_level'] = LEVELS[level_index]
                next_level = state['current_level']
                transition = 'advance'

        # ── 0 или 1 правильный → провал ────────────────────────────────────
        elif wrong >= 3:
            if is_retry:
                # Второй провал подряд — понижаем уровень
                state['is_retry'] = False
                if level_index - 1 >= 0:
                    level_index -= 1
                    state['level_index'] = level_index
                    state['current_level'] = LEVELS[level_index]
                    next_level = state['current_level']
                    transition = 'demote'
                else:
                    # Уже A1, ниже некуда — фиксируем A1
                    state['done'] = True
                    state['final_level'] = LEVELS[level_index]
                    transition = 'finish'
            else:
                # Первый провал — даём ещё один блок на том же уровне
                state['is_retry'] = True
                transition = 'retry'

        # ── 2 правильных → средний результат ───────────────────────────────
        else:
            if is_retry:
                # Второй блок тоже средний — считаем что уровень освоен, идём выше
                state['is_retry'] = False
                if level_index + 1 < len(LEVELS):
                    level_index += 1
                    state['level_index'] = level_index
                    state['current_level'] = LEVELS[level_index]
                    next_level = state['current_level']
                transition = 'advance'
            else:
                # Первый средний результат — retry на том же уровне
                state['is_retry'] = True
                transition = 'retry'

        # Сбрасываем счётчики блока
        state['block_correct'] = 0
        state['block_total'] = 0
        state['current_block_questions'] = []

    # Проверяем лимит вопросов
    if state['total_asked'] >= MAX_QUESTIONS and not state['done']:
        state['done'] = True
        state['final_level'] = state['current_level']

    request.session.modified = True

    # Если тест завершён — сохраняем уровень в профиль
    if state['done']:
        profile = get_or_create_profile(request.user)
        profile.level = state['final_level']
        profile.save()

    return JsonResponse({
        'is_correct': is_correct,
        'correct_answer': q.correct_option,
        'explanation': q.explanation,
        'block_done': block_done,
        'transition': transition,
        'next_level': next_level,
        'done': state['done'],
        'final_level': state.get('final_level'),
    })
# ──────────────────────────────────────────────
#  LEARNING
# ──────────────────────────────────────────────

LEVEL_ORDER = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
LEVEL_NAMES = {
    'A1': 'Начальный', 'A2': 'Элементарный',
    'B1': 'Средний',   'B2': 'Продвинутый',
    'C1': 'Продвинутый+', 'C2': 'Профессиональный',
}

def get_next_level(current_level):
    try:
        idx = LEVEL_ORDER.index(current_level)
        return LEVEL_ORDER[idx + 1] if idx + 1 < len(LEVEL_ORDER) else None
    except ValueError:
        return None


@login_required(login_url='/login/')
def learning_view(request):
    profile = get_or_create_profile(request.user)
    if not profile.level:
        return redirect('/level-check/')

    courses = Course.objects.filter(level=profile.level, is_active=True)
    lessons = list(Lesson.objects.filter(course__in=courses, is_active=True).select_related('course'))

    progress_map = {
        lp.lesson_id: lp
        for lp in LessonProgress.objects.filter(user=request.user, lesson__in=lessons)
    }

    lesson_list = []
    prev_passed = True  # первый урок всегда открыт

    for lesson in lessons:
        lp = progress_map.get(lesson.id)
        is_completed = lp.completed if lp else False
        lesson_score = lp.score if lp else 0
        is_locked = not prev_passed

        lesson_list.append({
            'id': lesson.id,
            'title': lesson.title,
            'icon': lesson.icon,
            'completed': is_completed,
            'locked': is_locked,
            'xp_reward': lesson.xp_reward,
            'score': lesson_score,
        })

        # Следующий урок открывается только если score >= 35
        if is_completed and lesson_score >= 35:
            prev_passed = True
        elif not is_locked:
            prev_passed = False

    # Проверяем: все уроки пройдены с score >= 35 → повышаем уровень
    all_passed = (
        len(lesson_list) > 0
        and all(l['completed'] and l['score'] >= 35 for l in lesson_list)
    )
    if all_passed:
        next_level = get_next_level(profile.level)
        if next_level:
            next_courses = Course.objects.filter(level=next_level, is_active=True)
            if Lesson.objects.filter(course__in=next_courses, is_active=True).exists():
                old_level = profile.level
                profile.level = next_level
                profile.save()
                # Редиректим с параметром чтобы показать сообщение после перезагрузки
                return redirect(f'/learning/?levelup={old_level}')

    # Читаем сообщение об уровне из GET-параметра (после редиректа)
    level_up_message = None
    levelup_param = request.GET.get('levelup')
    if levelup_param and levelup_param in LEVEL_NAMES:
        next_lv = get_next_level(levelup_param)
        next_lv_name = LEVEL_NAMES.get(next_lv, next_lv) if next_lv else ''
        level_up_message = (
            f'Вы успешно завершили курс уровня {levelup_param} '
            f'«{LEVEL_NAMES.get(levelup_param, levelup_param)}»! '
            f'Теперь вы переходите на уровень {next_lv} «{next_lv_name}».'
        )

    streak = profile.get_streak()
    context = {
        'profile': profile,
        'user_level': profile.level,
        'lessons': lesson_list,
        'streak': streak,
        'level_up_message': level_up_message,
    }
    return render(request, 'main/learning.html', context)


@login_required(login_url='/login/')
def complete_lesson_view(request, lesson_id):
    if request.method != "POST":
        return redirect('/learning/')

    lesson = get_object_or_404(Lesson, id=lesson_id, is_active=True)
    profile = get_or_create_profile(request.user)

    with transaction.atomic():
        progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
        if not progress.completed:
            progress.completed = True
            progress.completed_at = timezone.now()
            # Базовый score 50 — достаточно чтобы пройти порог 35
            progress.score = 50
            progress.save()

            profile.lessons_completed += 1
            profile.xp += lesson.xp_reward
            profile.total_minutes += lesson.estimated_minutes
            profile.current_lesson = lesson
            profile.save()

            record_activity(request.user, lesson.estimated_minutes)
            check_and_award_achievements(request.user, profile)

    return redirect('/learning/')


# ──────────────────────────────────────────────
#  PROFILE
# ──────────────────────────────────────────────

@login_required(login_url='/login/')
def profile_view(request):
    profile = get_or_create_profile(request.user)

    if request.method == 'POST':
        # Смена имени
        if 'change_username' in request.POST:
            new_username = request.POST.get('username', '').strip()
            if new_username and new_username != request.user.username:
                if not User.objects.filter(username=new_username).exists():
                    request.user.username = new_username
                    request.user.save()
                    messages.success(request, 'Имя пользователя изменено!')
                else:
                    messages.error(request, 'Это имя уже занято.')
            return redirect('/profile/')

        # Смена аватара
        if 'change_avatar' in request.POST:
            new_avatar = request.POST.get('avatar', '👤').strip()
            profile.avatar = new_avatar
            profile.save()
            messages.success(request, 'Аватар обновлён!')
            return redirect('/profile/')

    streak = profile.get_streak()
    all_achievements = Achievement.objects.all()
    earned_ids = set(
        UserAchievement.objects.filter(user=request.user).values_list('achievement_id', flat=True)
    )
    achievements_display = [
        {'achievement': ach, 'earned': ach.id in earned_ids}
        for ach in all_achievements
    ]
    recent_lessons = LessonProgress.objects.filter(
        user=request.user, completed=True
    ).select_related('lesson').order_by('-completed_at')[:5]

    context = {
        'profile': profile,
        'streak': streak,
        'achievements': achievements_display,
        'recent_lessons': recent_lessons,
        'today_minutes': profile.today_minutes(),
        'week_minutes': profile.week_minutes(),
        'avatar_choices': [
            '👤','🧑','👩','🧒','👦','👧','🧑‍💻','👨‍🎓','👩‍🎓',
            '🦊','🐼','🦁','🐯','🐸','🤖','👾','🧸','🦄',
        ],
    }
    return render(request, 'main/profile.html', context)


# ──────────────────────────────────────────────
#  CTA redirect
# ──────────────────────────────────────────────

def try_now_view(request):
    """CTA 'попробовать прямо сейчас' logic."""
    if not request.user.is_authenticated:
        return redirect('/register/')

    profile = get_or_create_profile(request.user)
    if profile.level and profile.current_lesson:
        return redirect('/learning/')
    return redirect('/level-check/')


# ──────────────────────────────────────────────
#  LESSON DETAIL
# ──────────────────────────────────────────────

from .models import (
    GrammarSection, ReadingSection, AudioSection, VideoSection,
    FlashcardDeck, Flashcard, FlashcardProgress,
    Exercise, ExerciseOption, ExerciseResult,
)


@login_required(login_url='/login/')
def lesson_detail_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, is_active=True)
    profile = get_or_create_profile(request.user)

    progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)

    # Mark content as read when user visits the lesson page
    if not progress.content_read:
        progress.content_read = True
        progress.save()

    context = {
        'lesson': lesson,
        'profile': profile,
        'progress': progress,
        'grammar_sections': lesson.grammar_sections.all(),
        'reading_sections': lesson.reading_sections.all(),
        'audio_sections': lesson.audio_sections.all(),
        'video_sections': lesson.video_sections.all(),
        'has_flashcards': lesson.flashcard_decks.exists(),
        'has_exercises': lesson.exercises.exists(),
    }
    return render(request, 'main/lesson_detail.html', context)


# ──────────────────────────────────────────────
#  FLASHCARDS
# ──────────────────────────────────────────────

@login_required(login_url='/login/')
def flashcards_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, is_active=True)
    decks = lesson.flashcard_decks.prefetch_related('cards').all()

    all_cards = []
    for deck in decks:
        for card in deck.cards.all():
            known = FlashcardProgress.objects.filter(
                user=request.user, flashcard=card, known=True
            ).exists()
            all_cards.append({'card': card, 'known': known})

    # Count known
    known_count = sum(1 for c in all_cards if c['known'])

    context = {
        'lesson': lesson,
        'all_cards': all_cards,
        'known_count': known_count,
        'total_count': len(all_cards),
    }
    return render(request, 'main/flashcards.html', context)


@login_required(login_url='/login/')
def flashcard_mark_view(request, card_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)

    card = get_object_or_404(Flashcard, id=card_id)
    known = data.get('known', False)
    fp, _ = FlashcardProgress.objects.get_or_create(user=request.user, flashcard=card)
    fp.known = known
    fp.save()

    # Check if all cards in deck are known — mark flashcards_done
    deck = card.deck
    lesson = deck.lesson
    total_cards = Flashcard.objects.filter(deck__lesson=lesson).count()
    known_cards = FlashcardProgress.objects.filter(
        user=request.user,
        flashcard__deck__lesson=lesson,
        known=True
    ).count()

    if known_cards >= total_cards:
        progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
        progress.flashcards_done = True
        progress.save()

    return JsonResponse({'success': True, 'known': known})


# ──────────────────────────────────────────────
#  EXERCISES
# ──────────────────────────────────────────────

@login_required(login_url='/login/')
def exercises_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, is_active=True)
    exercises = lesson.exercises.prefetch_related('options').all()

    context = {
        'lesson': lesson,
        'exercises': exercises,
    }
    return render(request, 'main/exercises.html', context)


@login_required(login_url='/login/')
def exercises_submit_view(request, lesson_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)

    lesson = get_object_or_404(Lesson, id=lesson_id, is_active=True)
    answers = data.get('answers', {})

    exercises = lesson.exercises.prefetch_related('options').all()
    total = exercises.count()
    score_count = 0  # количество правильных ответов
    results = {}

    for ex in exercises:
        chosen_id = answers.get(str(ex.id))
        correct_option = ex.options.filter(is_correct=True).first()
        correct_id = correct_option.id if correct_option else None
        is_correct = str(chosen_id) == str(correct_id) if chosen_id else False
        if is_correct:
            score_count += 1
        results[ex.id] = {
            'is_correct': is_correct,
            'correct_id': correct_id,
            'explanation': ex.explanation,
        }

    # Процент правильных ответов
    percentage = (score_count / total * 100) if total > 0 else 0

    # XP за эту попытку
    if percentage >= 80:
        attempt_xp = lesson.xp_reward       # полный XP (обычно 50)
    elif percentage >= 50:
        attempt_xp = lesson.xp_reward // 2  # половина
    else:
        attempt_xp = -10                     # штраф

    # Сохраняем попытку
    ExerciseResult.objects.create(
        user=request.user,
        lesson=lesson,
        score=score_count,
        total=total,
    )

    profile = get_or_create_profile(request.user)

    with transaction.atomic():
        progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)

        # XP суммируется между попытками, не уходит ниже 0
        old_score = progress.score
        new_score = max(0, old_score + attempt_xp)
        if progress.completed:
            new_score = max(35, new_score)
        xp_delta = new_score - old_score  # реальное изменение XP профиля

        progress.score = new_score
        progress.exercises_done = True
        progress.content_read = True

        # Урок считается завершённым при score >= 35
        if new_score >= 35 and not progress.completed:
            progress.completed = True
            progress.completed_at = timezone.now()
            profile.lessons_completed += 1

        progress.save()

        # Обновляем XP профиля
        profile.xp = max(0, profile.xp + xp_delta)
        profile.total_minutes += lesson.estimated_minutes
        profile.current_lesson = lesson
        profile.save()

        record_activity(request.user, lesson.estimated_minutes)
        check_and_award_achievements(request.user, profile)

    return JsonResponse({
        'score': score_count,
        'total': total,
        'percentage': round(percentage),
        'attempt_xp': attempt_xp,
        'total_score': new_score,
        'passed': new_score >= 35,
        'results': results,
        'lesson_completed': progress.completed,
    })