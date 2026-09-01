from django.db import models


class AccuracyClass(models.TextChoices):
    CLASS_I = 'I', 'Class I (Special)'
    CLASS_II = 'II', 'Class II (High)'
    CLASS_III = 'III', 'Class III (Medium)'
    CLASS_IIII = 'IIII', 'Class IIII (Ordinary)'


class VerificationType(models.TextChoices):
    INITIAL = 'initial', 'Initial Verification'
    SUBSEQUENT = 'subsequent', 'Subsequent Verification'


class EvaluationType(models.TextChoices):
    TYPE_EVALUATION = 'type_evaluation', 'Type Evaluation'
    INITIAL_VERIFICATION = 'initial_verification', 'Initial Verification'
    SUBSEQUENT_VERIFICATION = 'subsequent_verification', 'Subsequent Verification'


class TestType(models.TextChoices):
    WEIGHING_PERFORMANCE = 'weighing_performance', 'Weighing Performance'
    ECCENTRICITY = 'eccentricity', 'Eccentricity'
    REPEATABILITY = 'repeatability', 'Repeatability'
    DISCRIMINATION = 'discrimination', 'Discrimination'
    SENSITIVITY = 'sensitivity', 'Sensitivity'
    TARE = 'tare', 'Tare Device'
    CREEP = 'creep', 'Creep / Time Dependence'
    ZERO_RETURN = 'zero_return', 'Zero Return'
    TEMPERATURE = 'temperature', 'Temperature'
    TILT = 'tilt', 'Tilt'
    POWER_SUPPLY = 'power_supply', 'Power Supply Variation'
    DURABILITY = 'durability', 'Durability'
    SPAN_STABILITY = 'span_stability', 'Span Stability'
    ZERO_TRACKING = 'zero_tracking', 'Zero Tracking'


class ComplianceStatus(models.TextChoices):
    PASS = 'pass', 'Pass'
    FAIL = 'fail', 'Fail'
    NOT_APPLICABLE = 'not_applicable', 'Not Applicable'


class SessionStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'


class ReportStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    REVIEWED = 'reviewed', 'Reviewed'
    APPROVED = 'approved', 'Approved'


class Unit(models.TextChoices):
    MG = 'mg', 'Milligram'
    G = 'g', 'Gram'
    KG = 'kg', 'Kilogram'
    T = 't', 'Tonne'
    CT = 'ct', 'Metric Carat'


class EccentricityPosition(models.TextChoices):
    CENTER = 'center', 'Center'
    FRONT_LEFT = 'front_left', 'Front Left'
    FRONT_RIGHT = 'front_right', 'Front Right'
    REAR_LEFT = 'rear_left', 'Rear Left'
    REAR_RIGHT = 'rear_right', 'Rear Right'
