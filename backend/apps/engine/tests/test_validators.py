from decimal import Decimal

from django.test import TestCase

from apps.engine.validators import (
    get_min_capacity,
    is_durability_test_applicable,
    is_tilt_test_applicable,
    validate_multi_interval_config,
    validate_scale_intervals,
    validate_test_load,
)


class TestValidateTestLoad(TestCase):
    """Test 26: Test load below Min."""

    def test_load_below_min(self) -> None:
        e = Decimal('1')
        warnings = validate_test_load(Decimal('10'), 'III', e)
        self.assertTrue(len(warnings) > 0)
        self.assertIn('below minimum', warnings[0])

    def test_load_at_min(self) -> None:
        e = Decimal('1')
        min_cap = get_min_capacity('III', e)
        warnings = validate_test_load(min_cap, 'III', e)
        self.assertEqual(len(warnings), 0)

    def test_load_above_min(self) -> None:
        e = Decimal('1')
        warnings = validate_test_load(Decimal('100'), 'III', e)
        self.assertEqual(len(warnings), 0)

    def test_min_capacity_class_I(self) -> None:
        self.assertEqual(get_min_capacity('I', Decimal('0.001')), Decimal('0.1'))

    def test_min_capacity_class_IIII(self) -> None:
        self.assertEqual(get_min_capacity('IIII', Decimal('5')), Decimal('50'))

    def test_negative_load(self) -> None:
        warnings = validate_test_load(Decimal('-1'), 'III', Decimal('1'))
        self.assertTrue(any('non-negative' in w for w in warnings))


class TestScaleIntervalValidation(TestCase):
    def test_valid_d_equals_e(self) -> None:
        warnings = validate_scale_intervals(Decimal('1'), Decimal('1'), 'III')
        self.assertEqual(len(warnings), 0)

    def test_d_less_than_e_class_I(self) -> None:
        warnings = validate_scale_intervals(Decimal('0.1'), Decimal('1'), 'I')
        self.assertEqual(len(warnings), 0)

    def test_d_greater_than_e(self) -> None:
        warnings = validate_scale_intervals(Decimal('2'), Decimal('1'), 'III')
        self.assertTrue(any('cannot be greater' in w for w in warnings))

    def test_e_exceeds_10d_class_I(self) -> None:
        warnings = validate_scale_intervals(Decimal('0.01'), Decimal('0.11'), 'I')
        self.assertTrue(any('10d' in w for w in warnings))


class TestMultiIntervalValidation(TestCase):
    def test_valid_config(self) -> None:
        ranges = [
            {'max': '2000', 'e': '1'},
            {'max': '5000', 'e': '2'},
            {'max': '15000', 'e': '10'},
        ]
        warnings = validate_multi_interval_config(ranges, 'III')
        self.assertEqual(len(warnings), 0)

    def test_empty_config(self) -> None:
        warnings = validate_multi_interval_config([], 'III')
        self.assertTrue(len(warnings) > 0)

    def test_non_ascending_max(self) -> None:
        ranges = [
            {'max': '5000', 'e': '1'},
            {'max': '2000', 'e': '2'},
        ]
        warnings = validate_multi_interval_config(ranges, 'III')
        self.assertTrue(any('greater than' in w for w in warnings))


class TestTiltApplicability(TestCase):
    def test_class_I_not_applicable(self) -> None:
        self.assertFalse(is_tilt_test_applicable('I'))

    def test_class_II_applicable(self) -> None:
        self.assertTrue(is_tilt_test_applicable('II'))

    def test_class_III_applicable(self) -> None:
        self.assertTrue(is_tilt_test_applicable('III'))

    def test_class_IIII_applicable(self) -> None:
        self.assertTrue(is_tilt_test_applicable('IIII'))


class TestDurabilityApplicability(TestCase):
    def test_under_100kg(self) -> None:
        self.assertTrue(is_durability_test_applicable(Decimal('50'), 'kg'))

    def test_at_100kg(self) -> None:
        self.assertTrue(is_durability_test_applicable(Decimal('100'), 'kg'))

    def test_over_100kg(self) -> None:
        self.assertFalse(is_durability_test_applicable(Decimal('101'), 'kg'))

    def test_gram_conversion(self) -> None:
        self.assertTrue(is_durability_test_applicable(Decimal('100000'), 'g'))
        self.assertFalse(is_durability_test_applicable(Decimal('100001'), 'g'))

    def test_tonne_not_applicable(self) -> None:
        self.assertFalse(is_durability_test_applicable(Decimal('1'), 't'))
