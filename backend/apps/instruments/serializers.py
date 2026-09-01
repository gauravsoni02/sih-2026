from decimal import Decimal

from rest_framework import serializers

from apps.engine.config_loader import get_accuracy_classes
from apps.engine.validators import validate_scale_intervals

from .models import Instrument


class InstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_deleted')

    def validate(self, data: dict) -> dict:
        def field(name):
            if name in data:
                return data[name]
            return getattr(self.instance, name, None) if self.instance else None

        d = field('actual_scale_interval_d')
        e = field('verification_scale_interval_e')
        accuracy_class = field('accuracy_class')

        if d is not None and e is not None and d > e:
            raise serializers.ValidationError(
                {'actual_scale_interval_d': 'd cannot be greater than e'}
            )

        if d is not None and e is not None and accuracy_class:
            interval_errors = validate_scale_intervals(d, e, accuracy_class)
            if interval_errors:
                raise serializers.ValidationError(
                    {'verification_scale_interval_e': interval_errors}
                )

        is_multi = field('is_multi_interval') or False
        config = field('multi_interval_config')
        if is_multi and not config:
            raise serializers.ValidationError(
                {'multi_interval_config': 'Required for multi-interval instruments'}
            )

        max_capacity = field('max_capacity')
        n = field('num_scale_intervals_n')

        # n = Max / e must hold exactly for single-interval instruments
        # (for multi-interval instruments e varies per partial range).
        if (
            not is_multi
            and max_capacity is not None
            and e is not None
            and e > 0
            and n is not None
        ):
            expected_n = Decimal(max_capacity) / Decimal(e)
            if expected_n != expected_n.to_integral_value():
                raise serializers.ValidationError({
                    'num_scale_intervals_n': (
                        f'Max/e = {expected_n.normalize()} is not a whole '
                        f'number of verification scale intervals'
                    )
                })
            if Decimal(n) != expected_n:
                raise serializers.ValidationError({
                    'num_scale_intervals_n': (
                        f'n must equal Max/e = '
                        f'{int(expected_n.to_integral_value())}, got {n}'
                    )
                })

        # n must lie within the accuracy class limits (R 76-1 Table 3).
        if n is not None and accuracy_class:
            class_info = get_accuracy_classes().get(accuracy_class)
            if class_info:
                n_min = class_info.get('n_min')
                n_max = class_info.get('n_max')
                if n_min is not None and n < n_min:
                    raise serializers.ValidationError({
                        'num_scale_intervals_n': (
                            f'Class {accuracy_class} requires n ≥ {n_min}, got {n}'
                        )
                    })
                if n_max is not None and n > n_max:
                    raise serializers.ValidationError({
                        'num_scale_intervals_n': (
                            f'Class {accuracy_class} requires n ≤ {n_max}, got {n}'
                        )
                    })

        return data


class InstrumentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = (
            'id', 'serial_number', 'manufacturer', 'model_name',
            'accuracy_class', 'max_capacity', 'unit', 'status',
        )
