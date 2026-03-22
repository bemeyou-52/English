from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_new_models'),
    ]

    operations = [
        # GrammarSection
        migrations.CreateModel(
            name='GrammarSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Заголовок')),
                ('content', models.TextField(verbose_name='Содержание (поддерживает HTML)')),
                ('order', models.IntegerField(default=0)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grammar_sections', to='main.lesson')),
            ],
            options={'ordering': ['order'], 'verbose_name': 'Блок грамматики', 'verbose_name_plural': 'Блоки грамматики'},
        ),
        # ReadingSection
        migrations.CreateModel(
            name='ReadingSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Заголовок текста')),
                ('content', models.TextField(verbose_name='Текст для чтения')),
                ('translation', models.TextField(blank=True, verbose_name='Перевод (необязательно)')),
                ('order', models.IntegerField(default=0)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reading_sections', to='main.lesson')),
            ],
            options={'ordering': ['order'], 'verbose_name': 'Текст для чтения', 'verbose_name_plural': 'Тексты для чтения'},
        ),
        # AudioSection
        migrations.CreateModel(
            name='AudioSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Заголовок аудио')),
                ('description', models.TextField(blank=True, verbose_name='Описание / транскрипт')),
                ('audio_file', models.FileField(upload_to='lessons/audio/', verbose_name='Аудиофайл (mp3/wav)')),
                ('order', models.IntegerField(default=0)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audio_sections', to='main.lesson')),
            ],
            options={'ordering': ['order'], 'verbose_name': 'Аудио', 'verbose_name_plural': 'Аудиофайлы'},
        ),
        # VideoSection
        migrations.CreateModel(
            name='VideoSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Заголовок видео')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('video_url', models.URLField(verbose_name='Ссылка на YouTube / Vimeo')),
                ('order', models.IntegerField(default=0)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='video_sections', to='main.lesson')),
            ],
            options={'ordering': ['order'], 'verbose_name': 'Видео', 'verbose_name_plural': 'Видеофайлы'},
        ),
        # FlashcardDeck
        migrations.CreateModel(
            name='FlashcardDeck',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Название набора')),
                ('description', models.TextField(blank=True)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='flashcard_decks', to='main.lesson')),
            ],
            options={'verbose_name': 'Набор флеш-карт', 'verbose_name_plural': 'Наборы флеш-карт'},
        ),
        # Flashcard
        migrations.CreateModel(
            name='Flashcard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('front_text', models.CharField(max_length=300, verbose_name='Лицевая сторона (англ.)')),
                ('back_text', models.CharField(max_length=300, verbose_name='Обратная сторона (рус.)')),
                ('example_sentence', models.TextField(blank=True, verbose_name='Пример предложения')),
                ('order', models.IntegerField(default=0)),
                ('deck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cards', to='main.flashcarddeck')),
            ],
            options={'ordering': ['order'], 'verbose_name': 'Флеш-карта', 'verbose_name_plural': 'Флеш-карты'},
        ),
        # FlashcardProgress
        migrations.CreateModel(
            name='FlashcardProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('known', models.BooleanField(default=False)),
                ('reviewed_at', models.DateTimeField(auto_now=True)),
                ('flashcard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.flashcard')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='flashcard_progress', to='auth.user')),
            ],
            options={'unique_together': {('user', 'flashcard')}},
        ),
        # Exercise
        migrations.CreateModel(
            name='Exercise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exercise_type', models.CharField(choices=[('multiple_choice', 'Выбор ответа'), ('fill_blank', 'Заполнить пропуск'), ('true_false', 'Верно / Неверно')], default='multiple_choice', max_length=20, verbose_name='Тип задания')),
                ('question', models.TextField(verbose_name='Вопрос / Задание')),
                ('explanation', models.TextField(blank=True, verbose_name='Объяснение правильного ответа')),
                ('order', models.IntegerField(default=0)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exercises', to='main.lesson')),
            ],
            options={'ordering': ['order'], 'verbose_name': 'Задание', 'verbose_name_plural': 'Задания'},
        ),
        # ExerciseOption
        migrations.CreateModel(
            name='ExerciseOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=300, verbose_name='Текст варианта')),
                ('is_correct', models.BooleanField(default=False, verbose_name='Правильный ответ')),
                ('order', models.IntegerField(default=0)),
                ('exercise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='main.exercise')),
            ],
            options={'ordering': ['order'], 'verbose_name': 'Вариант ответа', 'verbose_name_plural': 'Варианты ответа'},
        ),
        # ExerciseResult
        migrations.CreateModel(
            name='ExerciseResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField(default=0)),
                ('total', models.IntegerField(default=0)),
                ('completed_at', models.DateTimeField(auto_now_add=True)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.lesson')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exercise_results', to='auth.user')),
            ],
            options={'ordering': ['-completed_at'], 'verbose_name': 'Результат заданий', 'verbose_name_plural': 'Результаты заданий'},
        ),
        # Add new fields to LessonProgress
        migrations.AddField(
            model_name='lessonprogress',
            name='content_read',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='lessonprogress',
            name='flashcards_done',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='lessonprogress',
            name='exercises_done',
            field=models.BooleanField(default=False),
        ),
    ]
