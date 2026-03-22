from django.db import migrations


def create_sample_lesson(apps, schema_editor):
    Course = apps.get_model('main', 'Course')
    Lesson = apps.get_model('main', 'Lesson')
    GrammarSection = apps.get_model('main', 'GrammarSection')
    ReadingSection = apps.get_model('main', 'ReadingSection')
    FlashcardDeck = apps.get_model('main', 'FlashcardDeck')
    Flashcard = apps.get_model('main', 'Flashcard')
    Exercise = apps.get_model('main', 'Exercise')
    ExerciseOption = apps.get_model('main', 'ExerciseOption')

    # Create course if it doesn't exist
    course, _ = Course.objects.get_or_create(
        title='Основы английского',
        defaults={
            'level': 'A1',
            'description': 'Базовый курс для начинающих',
            'icon': '🌱',
            'order': 1,
            'is_active': True,
        }
    )

    # Create lesson
    lesson, created = Lesson.objects.get_or_create(
        course=course,
        title='Present Simple — настоящее время',
        defaults={
            'description': 'Учимся описывать привычки, факты и регулярные действия',
            'icon': '⏰',
            'order': 1,
            'xp_reward': 50,
            'estimated_minutes': 15,
            'is_active': True,
        }
    )

    if not created:
        return  # Don't duplicate data

    # Grammar
    GrammarSection.objects.create(
        lesson=lesson,
        title='Что такое Present Simple?',
        content='''<div class="highlight">
<strong>Present Simple</strong> — это простое настоящее время. Мы используем его для описания:
<ul style="margin: 12px 0 0 20px; line-height: 2;">
  <li>привычных и регулярных действий: <em>I drink coffee every morning.</em></li>
  <li>фактов и общих истин: <em>The sun rises in the east.</em></li>
  <li>расписаний: <em>The train leaves at 8.</em></li>
</ul>
</div>

<h3 style="margin: 24px 0 12px; font-size: 18px;">📋 Образование</h3>

<table>
  <tr><th>Лицо</th><th>Местоимение</th><th>Глагол</th><th>Пример</th></tr>
  <tr><td>1-е ед.</td><td>I</td><td>work</td><td>I <strong>work</strong> here.</td></tr>
  <tr><td>2-е</td><td>You</td><td>work</td><td>You <strong>work</strong> here.</td></tr>
  <tr><td>3-е ед.</td><td>He / She / It</td><td>works</td><td>She <strong>works</strong> here.</td></tr>
  <tr><td>1-е мн.</td><td>We</td><td>work</td><td>We <strong>work</strong> here.</td></tr>
  <tr><td>3-е мн.</td><td>They</td><td>work</td><td>They <strong>work</strong> here.</td></tr>
</table>

<div class="highlight" style="margin-top: 20px;">
⚠️ <strong>Важно!</strong> В 3-м лице единственного числа (he, she, it) к глаголу добавляется <strong>-s</strong> или <strong>-es</strong>.
</div>

<h3 style="margin: 24px 0 12px; font-size: 18px;">❓ Отрицание и вопрос</h3>

<div class="example">
  ✅ <strong>+</strong> She <strong>likes</strong> coffee.<br>
  ❌ <strong>–</strong> She <strong>does not (doesn't) like</strong> coffee.<br>
  ❓ <strong>?</strong> <strong>Does</strong> she <strong>like</strong> coffee?
</div>

<div class="example">
  ✅ <strong>+</strong> They <strong>play</strong> football.<br>
  ❌ <strong>–</strong> They <strong>do not (don't) play</strong> football.<br>
  ❓ <strong>?</strong> <strong>Do</strong> they <strong>play</strong> football?
</div>

<h3 style="margin: 24px 0 12px; font-size: 18px;">📅 Слова-маркеры</h3>
<p>Эти слова часто сигнализируют о Present Simple:</p>
<p style="margin-top: 8px;"><strong>always, usually, often, sometimes, rarely, never, every day/week/month, on Mondays</strong></p>''',
        order=1
    )

    # Reading
    ReadingSection.objects.create(
        lesson=lesson,
        title='Meet Anna',
        content='''My name is Anna. I am 25 years old. I live in London with my cat, Max.

Every morning, I wake up at 7 o'clock. I drink a cup of tea and eat toast for breakfast. I don't eat eggs because I don't like them.

I work in a hospital. I am a nurse. I start work at 9 and finish at 5. My colleagues are very friendly.

After work, I usually go to the gym. Sometimes I cook dinner at home. I often make pasta — it's easy and delicious!

At weekends, I visit my parents. They live in a small town near London. My mum bakes cakes. My dad reads books.

I love my life!''',
        translation='''Меня зовут Анна. Мне 25 лет. Я живу в Лондоне с моей кошкой Максом.

Каждое утро я просыпаюсь в 7 часов. Я пью чашку чая и ем тост на завтрак. Я не ем яйца, потому что я их не люблю.

Я работаю в больнице. Я медсестра. Я начинаю работу в 9 и заканчиваю в 5. Мои коллеги очень дружелюбные.

После работы я обычно хожу в спортзал. Иногда я готовлю ужин дома. Я часто делаю пасту — это легко и вкусно!

По выходным я навещаю своих родителей. Они живут в маленьком городке недалеко от Лондона. Моя мама печёт торты. Мой папа читает книги.

Я люблю свою жизнь!''',
        order=1
    )

    # Flashcards
    deck = FlashcardDeck.objects.create(
        lesson=lesson,
        title='Ключевые слова урока',
        description='10 главных слов из текста и грамматики'
    )

    flashcard_data = [
        ('wake up', 'просыпаться', 'I wake up at 7 every day.'),
        ('work', 'работать', 'She works in a hospital.'),
        ('live', 'жить', 'They live in London.'),
        ('usually', 'обычно', 'I usually drink tea in the morning.'),
        ('always', 'всегда', 'He always reads books at night.'),
        ('never', 'никогда', 'She never eats fast food.'),
        ('sometimes', 'иногда', 'We sometimes go to the cinema.'),
        ('every day', 'каждый день', 'I go to school every day.'),
        ('like', 'любить / нравиться', 'Do you like coffee?'),
        ('finish', 'заканчивать', 'He finishes work at 5 pm.'),
    ]

    for i, (front, back, example) in enumerate(flashcard_data):
        Flashcard.objects.create(
            deck=deck,
            front_text=front,
            back_text=back,
            example_sentence=example,
            order=i
        )

    # Exercises
    exercises_data = [
        {
            'question': 'She ___ (work) in a school.',
            'options': [('works', True), ('work', False), ('is working', False), ('worked', False)],
            'explanation': 'В 3-м лице единственного числа (she) к глаголу добавляется -s: works.'
        },
        {
            'question': 'I ___ (not / like) coffee. I prefer tea.',
            'options': [("don't like", True), ("doesn't like", False), ("not like", False), ("am not like", False)],
            'explanation': 'Для отрицания с I/You/We/They используем do not (don\'t) + инфинитив.'
        },
        {
            'question': '___ he ___ (play) tennis on weekends?',
            'options': [('Does / play', True), ('Do / plays', False), ('Is / play', False), ('Does / plays', False)],
            'explanation': 'В вопросе с he/she/it используем Does + инфинитив (без -s).'
        },
        {
            'question': 'They ___ (visit) their grandparents every Sunday.',
            'options': [('visit', True), ('visits', False), ('are visiting', False), ('visited', False)],
            'explanation': 'С местоимением They глагол не меняется — нет окончания -s.'
        },
        {
            'question': 'Какое слово-маркер НЕ относится к Present Simple?',
            'options': [('yesterday', True), ('always', False), ('every day', False), ('usually', False)],
            'explanation': 'Yesterday (вчера) — маркер Past Simple. Always, every day, usually — маркеры Present Simple.'
        },
    ]

    for i, ex_data in enumerate(exercises_data):
        ex = Exercise.objects.create(
            lesson=lesson,
            exercise_type='multiple_choice',
            question=ex_data['question'],
            explanation=ex_data['explanation'],
            order=i
        )
        for j, (text, is_correct) in enumerate(ex_data['options']):
            ExerciseOption.objects.create(
                exercise=ex,
                text=text,
                is_correct=is_correct,
                order=j
            )


def remove_sample_lesson(apps, schema_editor):
    Course = apps.get_model('main', 'Course')
    Course.objects.filter(title='Основы английского', level='A1').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_lesson_content_flashcards_exercises'),
    ]

    operations = [
        migrations.RunPython(create_sample_lesson, remove_sample_lesson),
    ]
