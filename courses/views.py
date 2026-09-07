from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db.models import Max

from .models import (
    Language,
    Level,
    Course,
    Lesson,
    Activity,
    Question,
    Choice,
    QuizResult,
    LessonProgress,
    QuestionResult
)


def language_courses(request, slug):
    language = get_object_or_404(Language, slug=slug)
    levels = language.level_set.all()

    context = {
        'language': language,
        'levels': levels
    }
    return render(request, 'courses/language_courses.html', context)


def level_courses(request, id):
    level = get_object_or_404(Level, id=id)
    courses = Course.objects.filter(level=level, isActive=True).prefetch_related('lessons')

    total_lessons = 0
    completed_lessons = 0

    if request.user.is_authenticated:
        for course in courses:
            lessons = course.lessons.filter(isActive=True)
            total_lessons += lessons.count()
            completed_lessons += LessonProgress.objects.filter(
                user=request.user,
                lesson__in=lessons,
                completed=True
            ).count()
    else:
        for course in courses:
            total_lessons += course.lessons.filter(isActive=True).count()

    if total_lessons > 0:
        progress_percentage = int((completed_lessons / total_lessons) * 100)
    else:
        progress_percentage = 0

    context = {
        'level': level,
        'courses': courses,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'progress_percentage': progress_percentage
    }
    return render(request, 'courses/level_courses.html', context)


def course_detail(request, id):
    course = get_object_or_404(Course, id=id, isActive=True)
    lessons = course.lessons.filter(isActive=True).order_by('order')

    completed_lessons = []

    if request.user.is_authenticated:
        completed_lessons = LessonProgress.objects.filter(
            user=request.user,
            lesson__in=lessons,
            completed=True
        ).values_list('lesson_id', flat=True)

    completed_lessons = set(completed_lessons)

    total_lessons = lessons.count()
    completed_count = len(completed_lessons)

    if total_lessons > 0:
        progress_percentage = int((completed_count / total_lessons) * 100)
    else:
        progress_percentage = 0

    context = {
        'course': course,
        'lessons': lessons,
        'completed_lessons': completed_lessons,
        'total_lessons': total_lessons,
        'completed_count': completed_count,
        'progress_percentage': progress_percentage
    }
    return render(request, 'courses/course_detail.html', context)


def lesson_detail(request, id):
    lesson = get_object_or_404(Lesson, id=id, isActive=True)
    activities = lesson.activities.filter(isActive=True).order_by('order')

    progress = None

    if request.user.is_authenticated:
        progress, created = LessonProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson
        )

    # Ders içeriğini "İngilizce = Türkçe" satırlarına ayır
    vocab_list = []
    for line in lesson.content.splitlines():
        line = line.strip()
        if not line:
            continue
        if '=' in line:
            english, turkish = line.split('=', 1)
            vocab_list.append({
                'english': english.strip(),
                'turkish': turkish.strip(),
            })
        else:
            vocab_list.append({
                'english': line,
                'turkish': '',
            })



    speech_lang_map = {
    'ingilizce': 'en-US',
    'almanca': 'de-DE',
    'ispanyolca': 'es-ES',
    }

    speech_lang = speech_lang_map.get(
        lesson.course.level.language.slug,
        'en-US'
    )

    context = {
        'lesson': lesson,
        'activities': activities,
        'progress': progress,
        'vocab_list': vocab_list,
        'speech_lang': speech_lang,
    }
    return render(request, 'courses/lesson_detail.html', context)


def quiz(request, activity_id):
    activity = get_object_or_404(
        Activity,
        id=activity_id,
        isActive=True,
        lesson__isActive=True,
        lesson__course__isActive=True
    )

    speech_lang_map = {
    'ingilizce': 'en-US',
    'almanca': 'de-DE',
    'ispanyolca': 'es-ES',
    }
    speech_lang = speech_lang_map.get(
        activity.lesson.course.level.language.slug,
        'en-US'
    )
    questions = activity.questions.all().order_by('order')

    if request.method == 'POST':
        score = 0
        results = []

        if activity.activity_type == 'sentence_order':
            for question in questions:
                user_answer = request.POST.get(f'question_{question.id}', '').strip()
                correct_answer = (question.correct_answer or '').strip()

                user_answer_clean = user_answer.rstrip(".,!?")
                correct_answer_clean = correct_answer.rstrip(".,!?")

                is_correct = user_answer_clean.lower() == correct_answer_clean.lower()

                if is_correct:
                    score += 1

                results.append({
                    'question_text': question.question_text,
                    'user_answer': user_answer if user_answer else 'Cevaplanmadı',
                    'correct_answer': correct_answer,
                    'is_correct': is_correct,
                })

                if request.user.is_authenticated:
                    QuestionResult.objects.create(
                        user=request.user,
                        question=question,
                        is_correct=is_correct,
                    )

        elif activity.activity_type == 'fill_blank':
            for question in questions:
                user_answer = request.POST.get(f'question_{question.id}', '').strip()
                correct_answer = (question.correct_answer or '').strip()

                is_correct = user_answer.lower() == correct_answer.lower()

                if is_correct:
                    score += 1

                results.append({
                    'question_text': question.question_text,
                    'user_answer': user_answer if user_answer else 'Cevaplanmadı',
                    'correct_answer': correct_answer,
                    'is_correct': is_correct,
                })

                if request.user.is_authenticated:
                    QuestionResult.objects.create(
                        user=request.user,
                        question=question,
                        is_correct=is_correct,
                    )

        elif activity.activity_type in ('multiple_choice', 'true_false'):
            for question in questions:
                selected_id = request.POST.get(f'question_{question.id}')
                correct_choice = question.choices.filter(is_correct=True).first()

                selected_choice = None
                if selected_id:
                    selected_choice = question.choices.filter(id=selected_id).first()

                is_correct = bool(
                    correct_choice and selected_choice and selected_choice.id == correct_choice.id
                )

                if is_correct:
                    score += 1

                results.append({
                    'question_text': question.question_text,
                    'user_answer': selected_choice.text if selected_choice else 'Cevaplanmadı',
                    'correct_answer': correct_choice.text if correct_choice else '',
                    'is_correct': is_correct,
                })

                if request.user.is_authenticated:
                    QuestionResult.objects.create(
                        user=request.user,
                        question=question,
                        is_correct=is_correct,
                    )

        total_questions = questions.count()

        if total_questions > 0:
            percentage = int((score / total_questions) * 100)
        else:
            percentage = 0

        if request.user.is_authenticated:
            QuizResult.objects.create(
                user=request.user,
                activity=activity,
                score=score
            )

            lesson = activity.lesson
            lesson_activities = lesson.activities.filter(isActive=True)

            all_activities_completed = True

            for lesson_activity in lesson_activities:
                lesson_results = QuizResult.objects.filter(
                    user=request.user,
                    activity=lesson_activity
                )

                if not lesson_results.exists():
                    all_activities_completed = False
                    break

                activity_question_count = lesson_activity.questions.count()

                if activity_question_count == 0:
                    all_activities_completed = False
                    break

                highest_score = max(result.score for result in lesson_results)
                activity_percentage = (highest_score / activity_question_count) * 100

                if activity_percentage < 80:
                    all_activities_completed = False
                    break

            if all_activities_completed:
                LessonProgress.objects.update_or_create(
                    user=request.user,
                    lesson=lesson,
                    defaults={'completed': True}
                )

        return render(
            request,
            'courses/quiz_result.html',
            {
                'activity': activity,
                'score': score,
                'total': total_questions,
                'percentage': percentage,
                'results': results,
                'speech_lang': speech_lang,
            }
        )

    return render(
        request,
        'courses/quiz.html',
        {
            'activity': activity,
            'questions': questions,
            'speech_lang': speech_lang,
        }
    )

def mistakes_review(request):

    if not request.user.is_authenticated:
        return redirect('login')

    latest_result_ids = (
        QuestionResult.objects
        .filter(user=request.user)
        .values('question')
        .annotate(latest_id=Max('id'))
        .values_list('latest_id', flat=True)
    )

    wrong_results = (
        QuestionResult.objects
        .filter(id__in=latest_result_ids, is_correct=False)
        .select_related('question', 'question__activity', 'question__activity__lesson')
    )

    for result in wrong_results:
        question = result.question

        if question.activity.activity_type in ('multiple_choice', 'true_false'):
            correct_choice = question.choices.filter(is_correct=True).first()
            result.correct_answer_display = correct_choice.text if correct_choice else ''
        else:
            result.correct_answer_display = question.correct_answer

    context = {
        'wrong_results': wrong_results
    }

    return render(request, 'courses/mistakes_review.html', context)