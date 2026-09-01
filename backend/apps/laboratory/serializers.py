import re

from rest_framework import serializers

from .models import Laboratory, OrgSettings

# ~500 KB of base64 ≈ 375 KB image, plenty for a logo
MAX_LOGO_LENGTH = 500_000
DATA_URI_RE = re.compile(r'^data:image/(png|jpeg|jpg|gif|webp);base64,[A-Za-z0-9+/=]+$')


class LaboratorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Laboratory
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_deleted')


class OrgSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrgSettings
        fields = (
            'jurisdiction', 'report_prefix', 'doc_control_number',
            'doc_issue_number', 'doc_rev_number', 'doc_issue_date',
            'default_remarks', 'logo_data_uri', 'updated_at',
        )
        read_only_fields = ('updated_at',)

    def validate_report_prefix(self, value: str) -> str:
        value = value.strip().upper()
        if not re.fullmatch(r'[A-Z0-9-]{1,20}', value):
            raise serializers.ValidationError(
                'Prefix may only contain letters, digits and dashes (max 20 chars).'
            )
        return value

    def validate_default_remarks(self, value) -> list:
        if not isinstance(value, list) or not all(isinstance(r, str) for r in value):
            raise serializers.ValidationError('Must be a list of strings.')
        return [r.strip() for r in value if r.strip()]

    def validate_logo_data_uri(self, value: str) -> str:
        if not value:
            return ''
        if len(value) > MAX_LOGO_LENGTH:
            raise serializers.ValidationError('Logo too large (max ~375 KB).')
        if not DATA_URI_RE.match(value):
            raise serializers.ValidationError(
                'Must be a base64 image data URI (png/jpeg/gif/webp).'
            )
        return value
