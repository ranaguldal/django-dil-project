from django.contrib import admin
import nested_admin

from .models import (
    Language,
    Level,
    Course,
    Lesson,
    Activity,
    Question,
    Choice,
    QuizResult,
    LessonProgress
)


# =========================
# LANGUAGE
# =========================

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'flag')
    search_fields = ('name',)


# =========================
# LEVEL
# =========================

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'language')
    list_filter = ('language',)
    search_fields = ('name', 'language__name')


# =========================
# CHOICE (en alt seviye)
# =========================

class ChoiceInline(nested_admin.NestedTabularInline):
    model = Choice
    extra = 1
    fields = ('text', 'is_correct')


# =========================
# QUESTION (Choice'ları içinde barındırır)
# =========================

class QuestionInline(nested_admin.NestedStackedInline):
    model = Question
    extra = 1
    fields = ('question_text', 'correct_answer', 'order')
    ordering = ('order',)
    inlines = [ChoiceInline]


# =========================
# ACTIVITY (Question'ları içinde barındırır)
# =========================

class ActivityInline(nested_admin.NestedStackedInline):
    model = Activity
    extra = 1
    fields = ('title', 'activity_type', 'order', 'isActive')
    ordering = ('order',)
    inlines = [QuestionInline]


# =========================
# LESSON (Activity'leri içinde barındırır)
# =========================

class LessonInline(nested_admin.NestedStackedInline):
    model = Lesson
    extra = 0
    fields = ('title', 'description', 'content', 'order', 'isActive')
    ordering = ('order',)


# =========================
# COURSE (üst seviye - hepsini tek sayfada gösterir)
# =========================

@admin.register(Course)
class CourseAdmin(nested_admin.NestedModelAdmin):
    list_display = ('title', 'level', 'isActive')
    list_filter = ('isActive', 'level')
    search_fields = ('title', 'description')
    inlines = [LessonInline]


# =========================
# LESSON (tek başına da erişilebilir kalsın)
# =========================

@admin.register(Lesson)
class LessonAdmin(nested_admin.NestedModelAdmin):
    list_display = ('title', 'course', 'order', 'isActive')
    list_filter = ('isActive', 'course')
    search_fields = ('title', 'description')
    ordering = ('course', 'order')
    inlines = [ActivityInline]


# =========================
# ACTIVITY (tek başına da erişilebilir kalsın)
# =========================

@admin.register(Activity)
class ActivityAdmin(nested_admin.NestedModelAdmin):
    list_display = ('title', 'lesson', 'activity_type', 'order', 'isActive')
    list_filter = ('activity_type', 'isActive')
    search_fields = ('title', 'lesson__title')
    ordering = ('lesson', 'order')
    inlines = [QuestionInline]


# =========================
# QUESTION (tek başına da erişilebilir kalsın)
# =========================

@admin.register(Question)
class QuestionAdmin(nested_admin.NestedModelAdmin):
    list_display = ('question_text', 'activity', 'order')
    search_fields = ('question_text', 'activity__title')
    ordering = ('activity', 'order')
    inlines = [ChoiceInline]


# =========================
# CHOICE
# =========================

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('is_correct',)
    search_fields = ('text', 'question__question_text')


# =========================
# QUIZ RESULT
# =========================

@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity', 'score')
    list_filter = ('activity',)
    search_fields = ('user__username', 'activity__title')


# =========================
# LESSON PROGRESS
# =========================

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'completed', 'completed_at')
    list_filter = ('completed',)
    search_fields = ('user__username', 'lesson__title')