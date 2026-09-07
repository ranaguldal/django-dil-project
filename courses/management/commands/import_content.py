import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from courses.models import (
    Language,
    Level,
    Course,
    Lesson,
    Activity,
    Question,
    Choice,
)


class Command(BaseCommand):

    help = "Dil öğrenme platformu içeriklerini JSON dosyasından içe aktarır."

    def add_arguments(self, parser):
        parser.add_argument(
            'filename',
            nargs='?',
            default='english_a1.json'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Zaten var olan kayıtları da JSON içeriğine göre günceller.'
        )

    def handle(self, *args, **options):

        self.stdout.write("İçerik aktarımı başlıyor...")

        self.update_existing = options['update']
        filename = options['filename']

        data_path = (
            Path(__file__).resolve()
            .parent.parent.parent
            / "data"
            / filename
        )

        if not data_path.exists():
            self.stdout.write(
                self.style.ERROR(
                    f"JSON dosyası bulunamadı: {data_path}"
                )
            )
            return

        with open(data_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        with transaction.atomic():
            self.import_content(data)

        self.stdout.write(
            self.style.SUCCESS(
                "İçerik aktarımı başarıyla tamamlandı."
            )
        )

    def save_object(self, model, lookup, defaults):
        """
        update_existing True ise var olan kaydı da defaults ile günceller,
        False ise sadece eksik olanı oluşturur (eski davranış).
        """

        if self.update_existing:
            obj, created = model.objects.update_or_create(
                defaults=defaults,
                **lookup
            )
        else:
            obj, created = model.objects.get_or_create(
                defaults=defaults,
                **lookup
            )

        return obj, created

    def import_content(self, data):

        # -------------------------------------------------
        # LANGUAGE
        # -------------------------------------------------

        language_data = data["language"]

        language, created = self.save_object(
            Language,
            lookup={"slug": language_data["slug"]},
            defaults={
                "name": language_data["name"],
                "flag": language_data.get("flag", ""),
                "order": language_data.get("order", 1),
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f"Dil oluşturuldu: {language.name}")
            )
        else:
            self.stdout.write(f"Dil zaten mevcut: {language.name}")

        # -------------------------------------------------
        # LEVEL
        # -------------------------------------------------

        level_data = data["level"]

        level, created = self.save_object(
            Level,
            lookup={"language": language, "name": level_data["name"]},
            defaults={}
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f"Seviye oluşturuldu: {level.name}")
            )
        else:
            self.stdout.write(f"Seviye zaten mevcut: {level.name}")

        # -------------------------------------------------
        # COURSE
        # -------------------------------------------------

        course_data = data["course"]

        course, created = self.save_object(
            Course,
            lookup={"level": level, "title": course_data["title"]},
            defaults={
                "description": course_data.get("description", ""),
                "imageUrl": course_data.get("imageUrl", ""),
                "isActive": course_data.get("isActive", True),
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f"Kurs oluşturuldu: {course.title}")
            )
        else:
            self.stdout.write(f"Kurs zaten mevcut: {course.title}")

        # -------------------------------------------------
        # LESSONS
        # -------------------------------------------------

        for lesson_data in course_data.get("lessons", []):

            lesson, lesson_created = self.save_object(
                Lesson,
                lookup={"course": course, "title": lesson_data["title"]},
                defaults={
                    "description": lesson_data.get("description", ""),
                    "content": lesson_data.get("content", ""),
                    "order": lesson_data.get("order", 1),
                    "isActive": lesson_data.get("isActive", True),
                }
            )

            if lesson_created:
                self.stdout.write(
                    self.style.SUCCESS(f"  Ders oluşturuldu: {lesson.title}")
                )
            else:
                self.stdout.write(f"  Ders zaten mevcut: {lesson.title}")

            # -------------------------------------------------
            # ACTIVITIES
            # -------------------------------------------------

            for activity_data in lesson_data.get("activities", []):

                activity, activity_created = self.save_object(
                    Activity,
                    lookup={"lesson": lesson, "title": activity_data["title"]},
                    defaults={
                        "activity_type": activity_data["activity_type"],
                        "order": activity_data.get("order", 1),
                        "isActive": activity_data.get("isActive", True),
                    }
                )

                if activity_created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"    Aktivite oluşturuldu: {activity.title}"
                        )
                    )
                else:
                    self.stdout.write(
                        f"    Aktivite zaten mevcut: {activity.title}"
                    )

                # -------------------------------------------------
                # QUESTIONS
                # -------------------------------------------------

                for question_data in activity_data.get("questions", []):

                    question, question_created = self.save_object(
                        Question,
                        lookup={
                            "activity": activity,
                            "order": question_data.get("order", 1),
                        },
                        defaults={
                            "question_text": question_data["question_text"],
                            "correct_answer": question_data.get(
                                "correct_answer", ""
                            ),
                        }
                    )

                    if question_created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                "      Soru oluşturuldu: "
                                f"{question.question_text}"
                            )
                        )
                    else:
                        self.stdout.write(
                            "      Soru zaten mevcut: "
                            f"{question.question_text}"
                        )

                    # -------------------------------------------------
                    # CHOICES
                    # -------------------------------------------------

                    for choice_data in question_data.get("choices", []):

                        choice, choice_created = self.save_object(
                            Choice,
                            lookup={
                                "question": question,
                                "text": choice_data["text"],
                            },
                            defaults={
                                "is_correct": choice_data.get(
                                    "is_correct", False
                                )
                            }
                        )

                        if choice_created:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"        Şık oluşturuldu: {choice.text}"
                                )
                            )
                        else:
                            self.stdout.write(
                                f"        Şık zaten mevcut: {choice.text}"
                            )