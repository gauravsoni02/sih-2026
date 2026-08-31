from rest_framework import serializers

from .models import Laboratory


class LaboratorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Laboratory
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_deleted')
