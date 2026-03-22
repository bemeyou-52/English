from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('level-check/', views.level_check_view, name='level_check'),
    path('level-select/', views.level_select_view, name='level_select'),
    path('test/', views.test_view, name='test'),
    path('test/next-question/', views.test_next_question_view, name='test_next_question'),
    path('test/answer/', views.test_answer_view, name='test_answer'),
    path('learning/', views.learning_view, name='learning'),
    path('lesson/<int:lesson_id>/', views.lesson_detail_view, name='lesson_detail'),
    path('lesson/<int:lesson_id>/complete/', views.complete_lesson_view, name='complete_lesson'),
    path('lesson/<int:lesson_id>/flashcards/', views.flashcards_view, name='flashcards'),
    path('lesson/<int:lesson_id>/exercises/', views.exercises_view, name='exercises'),
    path('lesson/<int:lesson_id>/exercises/submit/', views.exercises_submit_view, name='exercises_submit'),
    path('flashcard/<int:card_id>/mark/', views.flashcard_mark_view, name='flashcard_mark'),
    path('profile/', views.profile_view, name='profile'),
    path('try/', views.try_now_view, name='try_now'),
]
