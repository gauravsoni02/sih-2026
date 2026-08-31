from rest_framework import serializers

from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(
        source='generated_by.get_full_name', read_only=True
    )
    approved_by_name = serializers.CharField(
        source='approved_by.get_full_name', read_only=True, default=None
    )

    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = (
            'id', 'created_at', 'updated_at', 'is_deleted',
            'report_number', 'version', 'pdf_path', 'docx_path',
        )


class ReportListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = (
            'id', 'report_number', 'overall_verdict', 'status',
            'version', 'created_at',
        )
