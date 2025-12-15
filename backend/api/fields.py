import base64

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            header, data = data.split(';base64,')
        try:
            decoded_file = base64.b64decode(data)
        except Exception as exc:
            raise serializers.ValidationError('Невозможно декодировать изображение') from exc  # noqa: E501

        file_name = 'image'
        file_extension = 'jpg'
        complete_file_name = f'{file_name}.{file_extension}'

        data = ContentFile(decoded_file, name=complete_file_name)
        return super().to_internal_value(data)
