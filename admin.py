from django.contrib import admin
from .models import (
    UserProfile, DailyActivity,
    Course, Lesson, LessonProgress,
    GrammarSection, ReadingSection, AudioSection, VideoSection,
    FlashcardDeck, Flashcard, FlashcardProgress,
    Exercise, ExerciseOption, ExerciseResult,
    TestQuestion,
    Achievement, UserAchievement,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'level', 'goal', 'xp', 'lessons_completed', 'created_at']
    list_filter = ['level', 'goal']
    search_fields = ['user__username', 'user__email']


@admin.register(DailyActivity)
class DailyActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'day', 'minutes', 'lessons_done']
    list_filter = ['day']
    search_fields = ['user__username']


# ── Lesson content inlines ──────────────────────────────────────────────

class GrammarSectionInline(admin.StackedInline):
    model = GrammarSection
    extra = 1
    fields = ['title', 'content', 'order']

class ReadingSectionInline(admin.StackedInline):
    model = ReadingSection
    extra = 0
    fields = ['title', 'content', 'translation', 'order']

class AudioSectionInline(admin.StackedInline):
    model = AudioSection
    extra = 0
    fields = ['title', 'description', 'audio_file', 'order']

class VideoSectionInline(admin.StackedInline):
    model = VideoSection
    extra = 0
    fields = ['title', 'description', 'video_url', 'order']

class FlashcardDeckInline(admin.TabularInline):
    model = FlashcardDeck
    extra = 0
    fields = ['title', 'description']
    show_change_link = True

class ExerciseInline(admin.TabularInline):
    model = Exercise
    extra = 0
    fields = ['exercise_type', 'question', 'order']
    show_change_link = True

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ['title', 'icon', 'order', 'xp_reward', 'estimated_minutes', 'is_active']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'level', 'order', 'is_active']
    list_filter = ['level', 'is_active']
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'xp_reward', 'is_active']
    list_filter = ['course__level', 'course', 'is_active']
    inlines = [
        GrammarSectionInline,
        ReadingSectionInline,
        AudioSectionInline,
        VideoSectionInline,
        FlashcardDeckInline,
        ExerciseInline,
    ]


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'completed', 'flashcards_done', 'exercises_done', 'completed_at', 'score']
    list_filter = ['completed']


# ── Flashcards ──────────────────────────────────────────────

class FlashcardInline(admin.TabularInline):
    model = Flashcard
    extra = 2
    fields = ['front_text', 'back_text', 'example_sentence', 'order']


@admin.register(FlashcardDeck)
class FlashcardDeckAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson']
    list_filter = ['lesson__course__level']
    inlines = [FlashcardInline]


@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ['front_text', 'back_text', 'deck']
    search_fields = ['front_text', 'back_text']


# ── Exercises ──────────────────────────────────────────────

class ExerciseOptionInline(admin.TabularInline):
    model = ExerciseOption
    extra = 4
    fields = ['text', 'is_correct', 'order']


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['question_short', 'exercise_type', 'lesson']
    list_filter = ['exercise_type', 'lesson__course__level']
    inlines = [ExerciseOptionInline]

    def question_short(self, obj):
        return obj.question[:70]
    question_short.short_description = 'Вопрос'


@admin.register(ExerciseResult)
class ExerciseResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'score', 'total', 'completed_at']


# ── Test ──────────────────────────────────────────────

@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text_short', 'level', 'order', 'correct_option', 'is_active']
    list_filter = ['level', 'is_active']
    ordering = ['level', 'order']
    fields = [
        'question_text', 'level', 'order',
        'option_a', 'option_b', 'option_c', 'option_d',
        'correct_option', 'explanation', 'is_active'
    ]

    def question_text_short(self, obj):
        return obj.question_text[:70]
    question_text_short.short_description = 'Вопрос'


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['title', 'icon', 'condition_type', 'condition_value']


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'earned_at']
