import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из data/ingredients.csv'

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parents[3]
        file_path = base_dir / 'data' / 'ingredients.csv'
        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f'Файл {file_path} не найден'))
            return

        created = 0
        with file_path.open(encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                name, unit = row
                obj, is_created = Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=unit,
                )
                if is_created:
                    created += 1
        self.stdout.write(self.style.SUCCESS(
            f'Импорт ингредиентов завершён, создано: {created}'
        ))
