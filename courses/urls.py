from django.urls import path
from . import views


urlpatterns = [

    # Kurs sistemi
    path('level/<int:id>/', views.level_courses, name='level_courses'),
    path('course/<int:id>/', views.course_detail, name='course_detail'),
    path('lesson/<int:id>/', views.lesson_detail, name='lesson_detail'),
    path('quiz/<int:activity_id>/', views.quiz, name='quiz'),

    # Dil (artık kendine özel prefix altında, tuzak oluşturmuyor)
    path('lang/<slug:slug>/', views.language_courses, name='language_courses'),
    path('mistakes/', views.mistakes_review, name='mistakes_review'),
]