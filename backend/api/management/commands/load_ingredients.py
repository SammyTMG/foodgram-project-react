import csv
from django.conf import settings
from django.core.management.base import BaseCommand
from api.models import Ingredient


class Command(BaseCommand):
    help = ' Загрузить ингредиенты в базу.'

    def handle(self, *args, **kwargs):
        path = settings.BASE_DIR
        with open(f'{path}/data/ingredients.csv', 'r',
                  encoding='utf-8') as file:
            file_reader = csv.reader(file)
            for row in file_reader:
                name, unit = row
                Ingredient.objects.get_or_create(name=name,
                                                 measurement_unit=unit)
