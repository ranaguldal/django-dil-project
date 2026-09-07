import random

from django.core.management.base import BaseCommand
from django.db import transaction

from courses.models import Lesson, Activity, Question, Choice


class Command(BaseCommand):

    help = "Ders içeriğindeki kelime listesinden soru üretir."

    def add_arguments(self, parser):
        parser.add_argument("--questions-per-lesson", type=int, default=8)

    def handle(self, *args, **options):
        max_questions = options["questions_per_lesson"]

        with transaction.atomic():
            for lesson in Lesson.objects.filter(isActive=True):
                words = self.parse_content(lesson.content)

                if len(words) < 4:
                    self.stdout.write(f"Atlandı: {lesson.title}")
                    continue

                self.stdout.write(f"\n{lesson.title}")
                self.generate_multiple_choice(lesson, words, max_questions)
                self.generate_fill_blank(lesson, words, max_questions)

        self.stdout.write(self.style.SUCCESS("\nTamamlandı."))

    def parse_content(self, content):
        words = []

        for line in content.splitlines():
            line = line.strip()

            if not line or "=" not in line:
                continue

            english, turkish = line.split("=", 1)
            words.append({
                "english": english.strip().rstrip("."),
                "turkish": turkish.strip().rstrip("."),
            })

        return words

    def generate_multiple_choice(self, lesson, words, max_questions):
        activity, created = Activity.objects.get_or_create(
            lesson=lesson,
            title=f"{lesson.title} Testi",
            defaults={
                "activity_type": "multiple_choice",
                "order": lesson.activities.count() + 1,
                "isActive": True,
            },
        )

        existing = set(activity.questions.values_list("question_text", flat=True))
        added = 0

        for word in words[:max_questions]:
            question_text = f"{word['english']} ne demektir?"

            if question_text in existing:
                continue

            question = Question.objects.create(
                activity=activity,
                question_text=question_text,
                correct_answer="",
                order=activity.questions.count() + 1,
            )

            pool = [w for w in words if w["turkish"] != word["turkish"]]
            distractors = random.sample(pool, k=min(3, len(pool)))

            choices = [word["turkish"]] + [d["turkish"] for d in distractors]
            random.shuffle(choices)

            for text in choices:
                Choice.objects.create(
                    question=question,
                    text=text,
                    is_correct=(text == word["turkish"]),
                )

            added += 1

        self.stdout.write(f"  Testi: +{added} soru")

    def generate_fill_blank(self, lesson, words, max_questions):
        activity, created = Activity.objects.get_or_create(
            lesson=lesson,
            title=f"{lesson.title} Boşluk Doldurma",
            defaults={
                "activity_type": "fill_blank",
                "order": lesson.activities.count() + 1,
                "isActive": True,
            },
        )

        existing = set(activity.questions.values_list("question_text", flat=True))
        added = 0

        for word in words[:max_questions]:
            question_text = f"{word['turkish']} kelimesinin İngilizcesi nedir?"

            if question_text in existing:
                continue

            Question.objects.create(
                activity=activity,
                question_text=question_text,
                correct_answer=word["english"],
                order=activity.questions.count() + 1,
            )

            added += 1

        self.stdout.write(f"  Boşluk Doldurma: +{added} soru")