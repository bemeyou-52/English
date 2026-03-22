from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import date, timedelta


# ──────────────────────────────────────────────
#  USER PROFILE & STREAK
# ──────────────────────────────────────────────

class UserProfile(models.Model):
    LEVEL_CHOICES = [
        ('A1', 'A1 — Начальный'),
        ('A2', 'A2 — Элементарный'),
        ('B1', 'B1 — Средний'),
        ('B2', 'B2 — Продвинутый'),
        ('C1', 'C1 — Продвинутый+'),
        ('C2', 'C2 — Профессиональный'),
    ]

    GOAL_CHOICES = [
        ('travel', 'Путешествия'),
        ('work', 'Работа / карьера'),
        ('study', 'Учёба'),
        ('hobby', 'Хобби / саморазвитие'),
        ('exam', 'Подготовка к экзамену'),
        ('kids', 'Для детей'),
        ('other', 'Другое'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES, blank=True, null=True)
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES, blank=True, null=True)
    xp = models.IntegerField(default=0)
    avatar = models.CharField(max_length=10, default='👤')
    lessons_completed = models.IntegerField(default=0)
    words_learned = models.IntegerField(default=0)
    total_minutes = models.IntegerField(default=0)
    current_lesson = models.ForeignKey(
        'Lesson', on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} — {self.level or "уровень не определён"}'

    def get_streak(self):
        today = date.today()
        streak = 0
        check_date = today
        while True:
            if DailyActivity.objects.filter(user=self.user, day=check_date).exists():
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        return streak

    def get_xp_to_next_level(self):
        level_xp = {'A1': 500, 'A2': 1000, 'B1': 2000, 'B2': 3500, 'C1': 5000, 'C2': 0}
        return level_xp.get(self.level, 500)

    def today_minutes(self):
        today = date.today()
        activity = DailyActivity.objects.filter(user=self.user, day=today).first()
        return activity.minutes if activity else 0

    def week_minutes(self):
        week_ago = date.today() - timedelta(days=7)
        activities = DailyActivity.objects.filter(user=self.user, day__gte=week_ago)
        return sum(a.minutes for a in activities)

    def total_hours(self):
        return round(self.total_minutes / 60, 1)

    def avg_daily_minutes(self):
        days = DailyActivity.objects.filter(user=self.user).count()
        if not days:
            return 0
        return round(self.total_minutes / days)


class DailyActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_activities')
    day = models.DateField(default=date.today)
    minutes = models.IntegerField(default=0)
    lessons_done = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'day')
        ordering = ['-day']

    def __str__(self):
        return f'{self.user.username} — {self.day}'


# ──────────────────────────────────────────────
#  COURSES & LESSONS
# ──────────────────────────────────────────────

class Course(models.Model):
    LEVEL_CHOICES = [
        ('A1', 'A1'), ('A2', 'A2'), ('B1', 'B1'),
        ('B2', 'B2'), ('C1', 'C1'), ('C2', 'C2'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, default='📚')
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES, default='A1')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['level', 'order']

    def __str__(self):
        return f'[{self.level}] {self.title}'

def get_default_lesson_order():
    last = Lesson.objects.order_by('-order').first()
    return (last.order + 1) if last else 1

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, default='📖')
    order = models.IntegerField(default=get_default_lesson_order)
    xp_reward = models.IntegerField(default=50)
    estimated_minutes = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.course.title} → {self.title}'
        


# ──────────────────────────────────────────────
#  LESSON CONTENT
# ──────────────────────────────────────────────

class GrammarSection(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='grammar_sections')
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Содержание (поддерживает HTML)')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Блок грамматики'
        verbose_name_plural = 'Блоки грамматики'

    def __str__(self):
        return f'{self.lesson.title} — Грамматика: {self.title}'


class ReadingSection(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='reading_sections')
    title = models.CharField(max_length=200, verbose_name='Заголовок текста')
    content = models.TextField(verbose_name='Текст для чтения')
    translation = models.TextField(blank=True, verbose_name='Перевод (необязательно)')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Текст для чтения'
        verbose_name_plural = 'Тексты для чтения'

    def __str__(self):
        return f'{self.lesson.title} — Чтение: {self.title}'


class AudioSection(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='audio_sections')
    title = models.CharField(max_length=200, verbose_name='Заголовок аудио')
    description = models.TextField(blank=True, verbose_name='Описание / транскрипт')
    audio_file = models.FileField(upload_to='lessons/audio/', verbose_name='Аудиофайл (mp3/wav)')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Аудио'
        verbose_name_plural = 'Аудиофайлы'

    def __str__(self):
        return f'{self.lesson.title} — Аудио: {self.title}'


class VideoSection(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='video_sections')
    title = models.CharField(max_length=200, verbose_name='Заголовок видео')
    description = models.TextField(blank=True, verbose_name='Описание')
    video_url = models.URLField(verbose_name='Ссылка на YouTube / Vimeo')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Видео'
        verbose_name_plural = 'Видеофайлы'

    def __str__(self):
        return f'{self.lesson.title} — Видео: {self.title}'

    def get_embed_url(self):
        import re
        url = self.video_url
        yt_match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]+)', url)
        if yt_match:
            return f'https://www.youtube.com/embed/{yt_match.group(1)}'
        if 'embed' in url:
            return url
        return url


# ──────────────────────────────────────────────
#  FLASHCARDS
# ──────────────────────────────────────────────

class FlashcardDeck(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='flashcard_decks')
    title = models.CharField(max_length=200, verbose_name='Название набора')
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Набор флеш-карт'
        verbose_name_plural = 'Наборы флеш-карт'

    def __str__(self):
        return f'{self.lesson.title} — Карточки: {self.title}'


class Flashcard(models.Model):
    deck = models.ForeignKey(FlashcardDeck, on_delete=models.CASCADE, related_name='cards')
    front_text = models.CharField(max_length=300, verbose_name='Лицевая сторона (англ.)')
    back_text = models.CharField(max_length=300, verbose_name='Обратная сторона (рус.)')
    example_sentence = models.TextField(blank=True, verbose_name='Пример предложения')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Флеш-карта'
        verbose_name_plural = 'Флеш-карты'

    def __str__(self):
        return f'{self.front_text} → {self.back_text}'


class FlashcardProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flashcard_progress')
    flashcard = models.ForeignKey(Flashcard, on_delete=models.CASCADE)
    known = models.BooleanField(default=False)
    reviewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'flashcard')

    def __str__(self):
        return f'{self.user.username} — {self.flashcard.front_text}'


# ──────────────────────────────────────────────
#  EXERCISES
# ──────────────────────────────────────────────

class Exercise(models.Model):
    EXERCISE_TYPES = [
        ('multiple_choice', 'Выбор ответа'),
        ('fill_blank', 'Заполнить пропуск'),
        ('true_false', 'Верно / Неверно'),
    ]

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='exercises')
    exercise_type = models.CharField(max_length=20, choices=EXERCISE_TYPES, default='multiple_choice', verbose_name='Тип задания')
    question = models.TextField(verbose_name='Вопрос / Задание')
    explanation = models.TextField(blank=True, verbose_name='Объяснение правильного ответа')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'

    def __str__(self):
        return f'{self.lesson.title} — {self.get_exercise_type_display()}: {self.question[:60]}'


class ExerciseOption(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=300, verbose_name='Текст варианта')
    is_correct = models.BooleanField(default=False, verbose_name='Правильный ответ')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Вариант ответа'
        verbose_name_plural = 'Варианты ответа'

    def __str__(self):
        return f'{"✓" if self.is_correct else "✗"} {self.text}'


class ExerciseResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercise_results')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']
        verbose_name = 'Результат заданий'
        verbose_name_plural = 'Результаты заданий'

    def __str__(self):
        return f'{self.user.username} — {self.lesson.title}: {self.score}/{self.total}'


# ──────────────────────────────────────────────
#  LESSON PROGRESS
# ──────────────────────────────────────────────

class LessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='user_progress')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0)
    content_read = models.BooleanField(default=False)
    flashcards_done = models.BooleanField(default=False)
    exercises_done = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'lesson')

    def __str__(self):
        return f'{self.user.username} — {self.lesson.title} ({"✓" if self.completed else "…"})'


# ──────────────────────────────────────────────
#  PLACEMENT TEST
# ──────────────────────────────────────────────

class TestQuestion(models.Model):
    LEVEL_CHOICES = [
        ('A1', 'A1'), ('A2', 'A2'), ('B1', 'B1'),
        ('B2', 'B2'), ('C1', 'C1'), ('C2', 'C2'),
    ]

    question_text = models.TextField()
    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300)
    option_d = models.CharField(max_length=300)
    correct_option = models.CharField(
        max_length=1,
        choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')]
    )
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES, default='C2')
    order = models.IntegerField(default=0)
    explanation = models.TextField(max_length=300, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['level', 'order']

    def __str__(self):
        return f'[{self.level}] {self.question_text[:60]}'


# ──────────────────────────────────────────────
#  ACHIEVEMENTS
# ──────────────────────────────────────────────

class Achievement(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=300)
    icon = models.CharField(max_length=10, default='🏆')
    condition_type = models.CharField(
        max_length=30,
        choices=[
            ('streak', 'Дней подряд'),
            ('lessons', 'Уроков пройдено'),
            ('xp', 'Очков опыта'),
            ('words', 'Слов изучено'),
        ]
    )
    condition_value = models.IntegerField(default=1)

    def __str__(self):
        return self.title


class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')

    def __str__(self):
        return f'{self.user.username} — {self.achievement.title}'
