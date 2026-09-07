from django.shortcuts import render, redirect

from courses.models import Language, QuizResult, Course, Lesson,LessonProgress,QuestionResult

from django.contrib.auth import login, logout

from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
    PasswordChangeForm
)

import json
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST


def home(request):

    languages = Language.objects.all().order_by('order')

    context = {
        'languages': languages
    }

    return render(
        request,
        'pages/home.html',
        context
    )


def register(request):

    if request.method == 'POST':

        form = UserCreationForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)

            return redirect('home')

    else:

        form = UserCreationForm()

    return render(
        request,
        'pages/register.html',
        {
            'form': form
        }
    )


def login_view(request):

    if request.method == 'POST':

        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            user = form.get_user()

            login(request, user)

            return redirect('home')

    else:

        form = AuthenticationForm()


    form.fields['username'].widget.attrs.update({
        'class': 'form-control',
        'placeholder': 'Kullanıcı adınızı girin'
    })

    form.fields['password'].widget.attrs.update({
        'class': 'form-control',
        'placeholder': 'Şifrenizi girin'
    })


    return render(
        request,
        'pages/login.html',
        {
            'form': form
        }
    )


def logout_view(request):

    logout(request)

    return redirect('home')


def profile(request):

    if not request.user.is_authenticated:
        return redirect('login')

    all_results = QuizResult.objects.filter(
        user=request.user
    ).select_related(
        'activity',
        'activity__lesson',
        'activity__lesson__course'
    )

    # Her aktivite için sadece en iyi denemeyi tut
    best_per_activity = {}
    for result in all_results:
        current_best = best_per_activity.get(result.activity_id)
        if current_best is None or result.score > current_best.score:
            best_per_activity[result.activity_id] = result

    best_results = list(best_per_activity.values())

    # Yüzdeleri hesapla
    total_percentage = 0
    highest_percentage = 0

    for result in best_results:
        total_questions = result.activity.questions.count()
        raw_percentage = int((result.score / total_questions) * 100) if total_questions > 0 else 0
        percentage = min(raw_percentage, 100)
        result.percentage = percentage  # template'te kullanmak için ekliyoruz

        total_percentage += percentage
        if percentage > highest_percentage:
            highest_percentage = percentage

    completed_quizzes = len(best_results)

    average_percentage = int(total_percentage / completed_quizzes) if completed_quizzes > 0 else 0

    context = {
        'results': best_results,
        'average_percentage': average_percentage,
        'completed_quizzes': completed_quizzes,
        'highest_score': highest_percentage,
    }

    return render(request, 'pages/profile.html', context)

def password_change(request):

    if not request.user.is_authenticated:

        return redirect('login')


    if request.method == 'POST':

        form = PasswordChangeForm(
            request.user,
            request.POST
        )

    else:

        form = PasswordChangeForm(
            request.user
        )


    # Bootstrap görünümü

    for field in form.fields.values():

        field.widget.attrs.update({
            'class': 'form-control'
        })


    if request.method == 'POST' and form.is_valid():

        user = form.save()

        # Şifre değiştikten sonra
        # kullanıcının oturumunu açık tut

        login(
            request,
            user
        )

        return redirect('profile')


    return render(
        request,
        'pages/password_change.html',
        {
            'form': form
        }
    )


def translate_page(request):
    return render(request, 'pages/translate.html')


@require_POST
def translate_api(request):

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'Geçersiz istek.'}, status=400)

    text = data.get('text', '').strip()
    target_lang = data.get('target_lang', 'EN')

    if not text:
        return JsonResponse({'error': 'Çevrilecek metin boş olamaz.'}, status=400)

    response = requests.post(
        'https://api-free.deepl.com/v2/translate',
        headers={
            'Authorization': f'DeepL-Auth-Key {settings.DEEPL_API_KEY}',
        },
        data={
            'text': text,
            'target_lang': target_lang,
        },
        timeout=10,
    )

    if response.status_code != 200:
        return JsonResponse(
            {'error': 'Çeviri servisi şu anda kullanılamıyor.'},
            status=502
        )

    result = response.json()
    translated_text = result['translations'][0]['text']

    return JsonResponse({'translated_text': translated_text})


def search(request):

    query = request.GET.get('q', '').strip()

    courses = Course.objects.none()
    lessons = Lesson.objects.none()

    if query:
        courses = Course.objects.filter(
            title__icontains=query,
            isActive=True
        ).select_related('level', 'level__language')

        lessons = Lesson.objects.filter(
            title__icontains=query,
            isActive=True
        ).select_related('course', 'course__level', 'course__level__language')

    context = {
        'query': query,
        'courses': courses,
        'lessons': lessons,
    }

    return render(request, 'pages/search_results.html', context)


def dashboard(request):

    if not request.user.is_authenticated:
        return redirect('login')

    total_lessons_completed = LessonProgress.objects.filter(
        user=request.user,
        completed=True
    ).count()

    activities_attempted = (
        QuizResult.objects
        .filter(user=request.user)
        .values('activity')
        .distinct()
        .count()
    )

    total_answered = QuestionResult.objects.filter(user=request.user).count()
    total_correct = QuestionResult.objects.filter(user=request.user, is_correct=True).count()

    if total_answered > 0:
        overall_accuracy = int((total_correct / total_answered) * 100)
    else:
        overall_accuracy = 0

    language_progress = []

    for language in Language.objects.all():

        lessons = Lesson.objects.filter(
            course__level__language=language,
            isActive=True
        )

        total = lessons.count()

        if total == 0:
            continue

        completed = LessonProgress.objects.filter(
            user=request.user,
            lesson__in=lessons,
            completed=True
        ).count()

        percentage = int((completed / total) * 100)

        language_progress.append({
            'language': language,
            'completed': completed,
            'total': total,
            'percentage': percentage,
        })

    context = {
        'total_lessons_completed': total_lessons_completed,
        'activities_attempted': activities_attempted,
        'overall_accuracy': overall_accuracy,
        'language_progress': language_progress,
    }

    return render(request, 'pages/dashboard.html', context)