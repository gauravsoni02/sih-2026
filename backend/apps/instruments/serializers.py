from rest_framework import serializers

from .models import Instrument


class InstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_deleted')

    def validate(self, data: dict) -> dict:
        d = data.get('actual_scale_interval_d')
        e = data.get('verification_scale_interval_e')
        if d is not None and e is not None and d > e:
            raise serializers.ValidationError(
                {'actual_scale_interval_d': 'd cannot be greater than e'}
            )

        is_multi = data.get('is_multi_interval', False)
        config = data.get('multi_interval_config')
        if is_multi and not config:
            raise serializers.ValidationError(
                {'multi_interval_config': 'Required for multi-interval instruments'}
            )

        return data


class InstrumentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = (
            'id', 'serial_number', 'manufacturer', 'model_name',
            'accuracy_class', 'max_capacity', 'unit', 'status',
        )
