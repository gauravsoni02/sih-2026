from rest_framework import serializers

from .models import TestObservation, TestResult, TestSession


class TestObservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestObservation
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_deleted')


class BulkObservationSerializer(serializers.ListSerializer):
    child = TestObservationSerializer()

    def create(self, validated_data: list[dict]) -> list[TestObservation]:
        observations = [TestObservation(**item) for item in validated_data]
        return TestObservation.objects.bulk_create(observations)


class TestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestResult
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_deleted')


class TestSessionSerializer(serializers.ModelSerializer):
    engineer_name = serializers.CharField(
        source='engineer.get_full_name', read_only=True
    )
    instrument_display = serializers.CharField(
        source='instrument.__str__', read_only=True
    )
    laboratory_name = serializers.CharField(
        source='laboratory.name', read_only=True
    )

    class Meta:
        model = TestSession
        fields = '__all__'
        read_only_fields = (
            'id', 'created_at', 'updated_at', 'is_deleted', 'overall_verdict',
        )


class TestSessionListSerializer(serializers.ModelSerializer):
    engineer_name = serializers.CharField(
        source='engineer.get_full_name', read_only=True
    )
    instrument_serial = serializers.CharField(
        source='instrument.serial_number', read_only=True
    )
    instrument_manufacturer = serializers.CharField(
        source='instrument.manufacturer', read_only=True
    )

    class Meta:
        model = TestSession
        fields = (
            'id', 'session_date', 'status', 'overall_verdict',
            'engineer_name', 'instrument_serial', 'instrument_manufacturer',
            'instrument', 'verification_type', 'evaluation_type',
        )
