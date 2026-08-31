from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'common'

    def ready(self) -> None:
        from auditlog.registry import auditlog

        from apps.accounts.models import User
        from apps.instruments.models import Instrument
        from apps.laboratory.models import Laboratory
        from apps.reports.models import Report
        from apps.testing.models import TestObservation, TestResult, TestSession

        auditlog.register(User)
        auditlog.register(Laboratory)
        auditlog.register(Instrument)
        auditlog.register(TestSession)
        auditlog.register(TestObservation)
        auditlog.register(TestResult)
        auditlog.register(Report)
