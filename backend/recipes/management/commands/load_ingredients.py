import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient
from django.conf import settings
from pathlib import Path

class Command(BaseCommand):
    help = 'Load ingredients from data/ingredients.json'

    def handle(self, *args, **kwargs):
        file_path = Path(settings.BASE_DIR).parent / 'data' / 'ingredients.json'

        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        Ingredient.objects.all().delete()  # очистка перед загрузкой

        objs = [
            Ingredient(
                name=item['name'],
                measurement_unit=item['measurement_unit']
            )
            for item in data
        ]

        Ingredient.objects.bulk_create(objs)

        self.stdout.write(self.style.SUCCESS(
            f'Successfully loaded {len(objs)} ingredients!'
        ))
