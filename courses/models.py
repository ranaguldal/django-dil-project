from django.db import models


class Language(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    flag = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name


class Level(models.Model):
    name = models.CharField(max_length=20)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.language.name} - {self.name}"


class Course(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    imageUrl = models.CharField(max_length=200, blank=True)
    isActive = models.BooleanField(default=True)
    

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons'
    )

    title = models.CharField(max_length=100)

    description = models.TextField(blank=True)

    content = models.TextField()

    order = models.PositiveIntegerField(default=1)

    isActive = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.course.title} - {self.title}"    

class Activity(models.Model):

    ACTIVITY_TYPES = [
        ('multiple_choice', 'Çoktan Seçmeli'),
        ('fill_blank', 'Boşluk Doldurma'),
        ('true_false', 'Doğru / Yanlış'),
        ('sentence_order', 'Cümle Oluşturma'),
    ]

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='activities'
    )

    title = models.CharField(max_length=100)

    activity_type = models.CharField(
        max_length=30,
        choices=ACTIVITY_TYPES
    )

    order = models.PositiveIntegerField(default=1)

    isActive = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"    

class Question(models.Model):

    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name='questions'
    )

    question_text = models.TextField()

    correct_answer = models.CharField(
        max_length=255,
        blank=True
    )

    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.question_text

class Choice(models.Model):

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices'
    )

    text = models.CharField(max_length=255)

    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class QuizResult(models.Model):

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE
    )

    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE
    )

    score = models.IntegerField()


    def __str__(self):
        return f"{self.user.username} - {self.activity.title} - {self.score}"

class LessonProgress(models.Model):

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE
    )

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE
    )

    completed = models.BooleanField(default=False)

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}"


class QuestionResult(models.Model):

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )

    is_correct = models.BooleanField()

    answered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        durum = "Doğru" if self.is_correct else "Yanlış"
        return f"{self.user.username} - {self.question.question_text} - {durum}"