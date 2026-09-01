from decimal import Decimal

from django.test import TestCase

from apps.engine.calculations import (
    check_error_compliance,
    compute_eccentricity_test_load,
    compute_error,
    evaluate_creep,
    evaluate_discrimination,
    evaluate_eccentricity,
    evaluate_repeatability,
    evaluate_sensitivity,
    evaluate_temperature_zero_drift,
    evaluate_zero_return,
    is_discrimination_applicable,
)
from apps.engine.constants import ComplianceStatus


class TestErrorComputation(TestCase):
    """Tests 8-11: Error computation and compliance."""

    # Test 8: Error with positive, negative, and zero corrections
    def test_error_positive_correction(self) -> None:
        error = compute_error(Decimal('100.5'), Decimal('100'), Decimal('0.2'))
        self.assertEqual(error, Decimal('0.3'))

    def test_error_negative_correction(self) -> None:
        error = compute_error(Decimal('100.5'), Decimal('100'), Decimal('-0.2'))
        self.assertEqual(error, Decimal('0.7'))

    def test_error_zero_correction(self) -> None:
        error = compute_error(Decimal('100.5'), Decimal('100'), Decimal('0'))
        self.assertEqual(error, Decimal('0.5'))

    # Test 9: Error = indication - (load + correction)
    def test_error_sign_convention(self) -> None:
        # Positive error (over-reading)
        error = compute_error(Decimal('101'), Decimal('100'), Decimal('0'))
        self.assertEqual(error, Decimal('1'))

        # Negative error (under-reading)
        error = compute_error(Decimal('99'), Decimal('100'), Decimal('0'))
        self.assertEqual(error, Decimal('-1'))

        # Exact
        error = compute_error(Decimal('100'), Decimal('100'), Decimal('0'))
        self.assertEqual(error, Decimal('0'))

    # Test 10: Compliance at exactly MPE -> PASS
    def test_compliance_at_exactly_mpe(self) -> None:
        mpe = Decimal('0.5')
        self.assertEqual(
            check_error_compliance(Decimal('0.5'), mpe), ComplianceStatus.PASS
        )
        self.assertEqual(
            check_error_compliance(Decimal('-0.5'), mpe), ComplianceStatus.PASS
        )

    # Test 11: Compliance at MPE + 0.001 -> FAIL
    def test_compliance_just_over_mpe(self) -> None:
        mpe = Decimal('0.5')
        self.assertEqual(
            check_error_compliance(Decimal('0.501'), mpe), ComplianceStatus.FAIL
        )
        self.assertEqual(
            check_error_compliance(Decimal('-0.501'), mpe), ComplianceStatus.FAIL
        )


class TestEccentricity(TestCase):
    """Tests 12-16: Eccentricity tests.

    Per R 76-1 A.4.7 each position's error is referenced to the APPLIED
    LOAD (not the center reading), so a span bias cannot cancel out.
    """

    # Test 12: Test load with T+ > 0
    def test_eccentricity_load_with_tare(self) -> None:
        load = compute_eccentricity_test_load(Decimal('15000'), Decimal('3000'))
        self.assertEqual(load, Decimal('6000'))

    # Test 13: Test load with T+ = 0
    def test_eccentricity_load_no_tare(self) -> None:
        load = compute_eccentricity_test_load(Decimal('15000'), Decimal('0'))
        self.assertEqual(load, Decimal('5000'))

    def test_eccentricity_load_default_tare(self) -> None:
        load = compute_eccentricity_test_load(Decimal('15000'))
        self.assertEqual(load, Decimal('5000'))

    # Test 14: Readings equal to the applied load -> 0 error, PASS
    def test_eccentricity_identical_readings(self) -> None:
        readings = {
            'center': Decimal('5000'),
            'front_left': Decimal('5000'),
            'front_right': Decimal('5000'),
            'rear_left': Decimal('5000'),
            'rear_right': Decimal('5000'),
        }
        errors, status = evaluate_eccentricity(readings, Decimal('5000'), Decimal('1.5'))
        self.assertEqual(status, ComplianceStatus.PASS)
        for err in errors.values():
            self.assertEqual(err, Decimal('0'))

    # Test 15: Error vs applied load > MPE -> FAIL
    def test_eccentricity_over_mpe(self) -> None:
        mpe = Decimal('1.5')
        readings = {
            'front_left': Decimal('5002'),
            'front_right': Decimal('5000'),
            'rear_left': Decimal('5000'),
            'rear_right': Decimal('5000'),
        }
        errors, status = evaluate_eccentricity(readings, Decimal('5000'), mpe)
        self.assertEqual(status, ComplianceStatus.FAIL)
        self.assertEqual(errors['front_left'], Decimal('2'))

    # Test 16: Error exactly at MPE -> PASS
    def test_eccentricity_at_mpe(self) -> None:
        mpe = Decimal('1.5')
        readings = {
            'front_left': Decimal('5001.5'),
            'front_right': Decimal('4998.5'),
            'rear_left': Decimal('5000'),
            'rear_right': Decimal('5000'),
        }
        errors, status = evaluate_eccentricity(readings, Decimal('5000'), mpe)
        self.assertEqual(status, ComplianceStatus.PASS)

    def test_eccentricity_span_bias_not_cancelled(self) -> None:
        # All positions read 2 units high, including center. Under the old
        # (wrong) center-referenced criterion these would all "pass"; under
        # the load-referenced criterion every position fails when MPE < 2.
        mpe = Decimal('1.5')
        readings = {
            'center': Decimal('5002'),
            'front_left': Decimal('5002'),
            'front_right': Decimal('5002'),
            'rear_left': Decimal('5002'),
            'rear_right': Decimal('5002'),
        }
        errors, status = evaluate_eccentricity(readings, Decimal('5000'), mpe)
        self.assertEqual(status, ComplianceStatus.FAIL)
        for err in errors.values():
            self.assertEqual(err, Decimal('2'))

    def test_eccentricity_center_error_counts(self) -> None:
        # A center reading out of tolerance fails the test even when the
        # corner readings are compliant.
        mpe = Decimal('1.5')
        readings = {
            'center': Decimal('5002'),
            'front_left': Decimal('5000'),
            'front_right': Decimal('5000'),
            'rear_left': Decimal('5000'),
            'rear_right': Decimal('5000'),
        }
        errors, status = evaluate_eccentricity(readings, Decimal('5000'), mpe)
        self.assertEqual(status, ComplianceStatus.FAIL)
        self.assertEqual(errors['center'], Decimal('2'))


class TestRepeatability(TestCase):
    """Tests 17-18: Repeatability tests."""

    # Test 17: Range at boundary -> PASS
    def test_repeatability_at_boundary(self) -> None:
        mpe = Decimal('1.5')
        readings = [Decimal('5000'), Decimal('5001.5'), Decimal('5000.5')]
        range_val, status = evaluate_repeatability(readings, mpe)
        self.assertEqual(range_val, Decimal('1.5'))
        self.assertEqual(status, ComplianceStatus.PASS)

    # Test 18: Range exceeding MPE by smallest increment -> FAIL
    def test_repeatability_just_over_mpe(self) -> None:
        mpe = Decimal('1.5')
        readings = [Decimal('5000'), Decimal('5001.501'), Decimal('5000.5')]
        range_val, status = evaluate_repeatability(readings, mpe)
        self.assertEqual(status, ComplianceStatus.FAIL)

    def test_repeatability_insufficient_readings(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_repeatability([Decimal('100')], Decimal('1'))


class TestDiscrimination(TestCase):
    """Tests 19-22: Discrimination tests."""

    # Test 19: 1.4d added, indication changes -> PASS
    def test_discrimination_pass(self) -> None:
        d = Decimal('1')
        initial = Decimal('1000')
        after = Decimal('1001')
        changed, status = evaluate_discrimination(initial, after, d)
        self.assertEqual(status, ComplianceStatus.PASS)
        self.assertTrue(changed)

    # Test 20: 1.4d added, no change -> FAIL
    def test_discrimination_fail(self) -> None:
        d = Decimal('1')
        initial = Decimal('1000')
        after = Decimal('1000')
        changed, status = evaluate_discrimination(initial, after, d)
        self.assertEqual(status, ComplianceStatus.FAIL)
        self.assertFalse(changed)

    # Test 21: d < 5mg -> NOT_APPLICABLE
    def test_discrimination_not_applicable(self) -> None:
        self.assertFalse(is_discrimination_applicable(Decimal('0.004'), 'g'))
        self.assertFalse(is_discrimination_applicable(Decimal('4'), 'mg'))

    def test_discrimination_applicable_at_5mg(self) -> None:
        self.assertTrue(is_discrimination_applicable(Decimal('5'), 'mg'))
        self.assertTrue(is_discrimination_applicable(Decimal('0.005'), 'g'))
        self.assertTrue(is_discrimination_applicable(Decimal('1'), 'g'))

    # Test 22: Discrimination uses d, not e - test with d != e
    def test_discrimination_uses_d_not_e(self) -> None:
        d = Decimal('0.1')
        e = Decimal('1')
        # Extra load should be 1.4d = 0.14, NOT 1.4e = 1.4
        initial = Decimal('1000')
        after = Decimal('1000.1')
        changed, status = evaluate_discrimination(initial, after, d)
        self.assertEqual(status, ComplianceStatus.PASS)
        # If it incorrectly used e, a change of 0.1 (< 1.0) would fail
        # With d=0.1, a change of 0.1 (>= d) passes


class TestCreep(TestCase):
    """Tests 23-25: Creep / time dependence tests."""

    # Test 23: Both conditions met -> PASS
    def test_creep_pass(self) -> None:
        e = Decimal('1')
        drift_total, drift_15_30, status = evaluate_creep(
            Decimal('1000.0'), Decimal('1000.3'), Decimal('1000.4'), e
        )
        self.assertEqual(status, ComplianceStatus.PASS)
        self.assertEqual(drift_total, Decimal('0.4'))
        self.assertEqual(drift_15_30, Decimal('0.1'))

    # Test 24: 0-30min diff = 0.6e -> FAIL
    def test_creep_total_drift_fail(self) -> None:
        e = Decimal('1')
        _, _, status = evaluate_creep(
            Decimal('1000.0'), Decimal('1000.3'), Decimal('1000.6'), e
        )
        self.assertEqual(status, ComplianceStatus.FAIL)

    # Test 25: total OK but 15-30min diff too large -> FAIL
    def test_creep_partial_drift_fail(self) -> None:
        e = Decimal('1')
        _, _, status = evaluate_creep(
            Decimal('1000.0'), Decimal('1000.1'), Decimal('1000.4'), e
        )
        # drift_total = 0.4 <= 0.5 OK
        # drift_15_30 = 0.3 > 0.2 FAIL
        self.assertEqual(status, ComplianceStatus.FAIL)


class TestSensitivity(TestCase):
    """Sensitivity: indication change must be at least 0.4 x MPE."""

    def test_change_at_exactly_04_mpe_passes(self) -> None:
        # MPE = 10 -> required change = 4
        change, status = evaluate_sensitivity(
            Decimal('0'), Decimal('4'), Decimal('10')
        )
        self.assertEqual(change, Decimal('4'))
        self.assertEqual(status, ComplianceStatus.PASS)

    def test_change_below_04_mpe_fails(self) -> None:
        change, status = evaluate_sensitivity(
            Decimal('0'), Decimal('3.9'), Decimal('10')
        )
        self.assertEqual(status, ComplianceStatus.FAIL)

    def test_nonzero_but_insufficient_change_fails(self) -> None:
        # The old criterion passed on ANY non-zero movement; the correct
        # one requires 0.4 x MPE. Change of 1 unit vs MPE 10 must fail.
        change, status = evaluate_sensitivity(
            Decimal('1000'), Decimal('1001'), Decimal('10')
        )
        self.assertEqual(change, Decimal('1'))
        self.assertEqual(status, ComplianceStatus.FAIL)

    def test_change_above_04_mpe_passes(self) -> None:
        change, status = evaluate_sensitivity(
            Decimal('1000'), Decimal('1005'), Decimal('10')
        )
        self.assertEqual(status, ComplianceStatus.PASS)

    def test_zero_load_min_zone_mpe(self) -> None:
        # At zero load MPE = 0.5e; with e = 1 -> required change = 0.2
        change, status = evaluate_sensitivity(
            Decimal('0'), Decimal('0.2'), Decimal('0.5')
        )
        self.assertEqual(status, ComplianceStatus.PASS)
        change, status = evaluate_sensitivity(
            Decimal('0'), Decimal('0.1'), Decimal('0.5')
        )
        self.assertEqual(status, ComplianceStatus.FAIL)


class TestTemperatureZeroDrift(TestCase):
    """Test 28: Temperature zero drift."""

    def test_class_I_1e_per_1c(self) -> None:
        e = Decimal('0.001')
        # 1 degree change, zero drifts by 0.001 (= 1e) -> PASS
        status = evaluate_temperature_zero_drift(
            Decimal('0.001'), Decimal('1'), 'I', e
        )
        self.assertEqual(status, ComplianceStatus.PASS)

        # 1 degree change, zero drifts by 0.002 (= 2e) -> FAIL
        status = evaluate_temperature_zero_drift(
            Decimal('0.002'), Decimal('1'), 'I', e
        )
        self.assertEqual(status, ComplianceStatus.FAIL)

    def test_class_III_1e_per_5c(self) -> None:
        e = Decimal('1')
        # 5 degree change, zero drifts by 1 (= 1e) -> PASS
        status = evaluate_temperature_zero_drift(
            Decimal('1'), Decimal('5'), 'III', e
        )
        self.assertEqual(status, ComplianceStatus.PASS)

        # 5 degree change, zero drifts by 1.1 (> 1e) -> FAIL
        status = evaluate_temperature_zero_drift(
            Decimal('1.1'), Decimal('5'), 'III', e
        )
        self.assertEqual(status, ComplianceStatus.FAIL)

    def test_zero_temp_change(self) -> None:
        status = evaluate_temperature_zero_drift(
            Decimal('0.5'), Decimal('0'), 'III', Decimal('1')
        )
        self.assertEqual(status, ComplianceStatus.PASS)
