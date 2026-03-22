from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Drop old UserProfile and recreate with new fields
        migrations.DeleteModel(name='UserProfile'),

        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(blank=True, choices=[('A1', 'A1 — Начальный'), ('A2', 'A2 — Элементарный'), ('B1', 'B1 — Средний'), ('B2', 'B2 — Продвинутый'), ('C1', 'C1 — Продвинутый+'), ('C2', 'C2 — Профессиональный')], max_length=2, null=True)),
                ('goal', models.CharField(blank=True, choices=[('travel', 'Путешествия'), ('work', 'Работа / карьера'), ('study', 'Учёба'), ('hobby', 'Хобби / саморазвитие'), ('exam', 'Подготовка к экзамену'), ('kids', 'Для детей'), ('other', 'Другое')], max_length=20, null=True)),
                ('xp', models.IntegerField(default=0)),
                ('lessons_completed', models.IntegerField(default=0)),
                ('words_learned', models.IntegerField(default=0)),
                ('total_minutes', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),

        migrations.CreateModel(
            name='DailyActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.DateField(default=datetime.date.today)),
                ('minutes', models.IntegerField(default=0)),
                ('lessons_done', models.IntegerField(default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_activities', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-day'], 'unique_together': {('user', 'day')}},
        ),

        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('icon', models.CharField(default='📚', max_length=10)),
                ('level', models.CharField(choices=[('A1', 'A1'), ('A2', 'A2'), ('B1', 'B1'), ('B2', 'B2'), ('C1', 'C1'), ('C2', 'C2')], default='A1', max_length=2)),
                ('order', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['level', 'order']},
        ),

        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('icon', models.CharField(default='📖', max_length=10)),
                ('order', models.IntegerField(default=0)),
                ('xp_reward', models.IntegerField(default=50)),
                ('estimated_minutes', models.IntegerField(default=10)),
                ('is_active', models.BooleanField(default=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lessons', to='main.course')),
            ],
            options={'ordering': ['order']},
        ),

        # Add FK from UserProfile to Lesson
        migrations.AddField(
            model_name='userprofile',
            name='current_lesson',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='main.lesson'),
        ),

        migrations.CreateModel(
            name='LessonProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completed', models.BooleanField(default=False)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('score', models.IntegerField(default=0)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_progress', to='main.lesson')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lesson_progress', to=settings.AUTH_USER_MODEL)),
            ],
            options={'unique_together': {('user', 'lesson')}},
        ),

        migrations.CreateModel(
            name='TestQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_text', models.TextField()),
                ('option_a', models.CharField(max_length=300)),
                ('option_b', models.CharField(max_length=300)),
                ('option_c', models.CharField(max_length=300)),
                ('option_d', models.CharField(max_length=300)),
                ('correct_option', models.CharField(choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')], max_length=1)),
                ('level', models.CharField(choices=[('A1', 'A1'), ('A2', 'A2'), ('B1', 'B1'), ('B2', 'B2'), ('C1', 'C1'), ('C2', 'C2')], default='A1', max_length=2)),
                ('order', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['level', 'order']},
        ),

        migrations.CreateModel(
            name='Achievement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=300)),
                ('icon', models.CharField(default='🏆', max_length=10)),
                ('condition_type', models.CharField(choices=[('streak', 'Дней подряд'), ('lessons', 'Уроков пройдено'), ('xp', 'Очков опыта'), ('words', 'Слов изучено')], max_length=30)),
                ('condition_value', models.IntegerField(default=1)),
            ],
        ),

        migrations.CreateModel(
            name='UserAchievement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('earned_at', models.DateTimeField(auto_now_add=True)),
                ('achievement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.achievement')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='achievements', to=settings.AUTH_USER_MODEL)),
            ],
            options={'unique_together': {('user', 'achievement')}},
        ),
    ]
