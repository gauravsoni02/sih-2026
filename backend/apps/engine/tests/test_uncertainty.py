from decimal import Decimal

from django.test import SimpleTestCase

from apps.engine.uncertainty import (
    compute_uncertainty_budget,
    repeatability_std_dev,
    round_uncertainty,
)


class TestRepeatabilityStdDev(SimpleTestCase):
    def test_identical_readings_zero_std_dev(self) -> None:
        readings = [Decimal('1000.0')] * 5
        self.assertEqual(repeatability_std_dev(readings), Decimal('0'))

    def test_known_std_dev(self) -> None:
        # readings 9, 10, 11 -> sample std dev = 1
        readings = [Decimal('9'), Decimal('10'), Decimal('11')]
        self.assertAlmostEqual(float(repeatability_std_dev(readings)), 1.0, places=9)

    def test_fewer_than_two_readings(self) -> None:
        self.assertEqual(repeatability_std_dev([]), Decimal('0'))
        self.assertEqual(repeatability_std_dev([Decimal('5')]), Decimal('0'))


class TestUncertaintyBudget(SimpleTestCase):
    def test_components_and_combination(self) -> None:
        budget = compute_uncertainty_budget(
            d=Decimal('0.01'), mpe=Decimal('0.015'),
        )
        # d/(2*sqrt(3)) = 0.01 / 3.4641... = 0.0028867...
        self.assertAlmostEqual(
            float(budget['u_resolution_zero']), 0.0028868, places=6)
        self.assertEqual(budget['u_resolution_zero'], budget['u_resolution_load'])
        # (mpe/3)/sqrt(3) = 0.005/1.7320... = 0.0028867...
        self.assertAlmostEqual(
            float(budget['u_reference_weights']), 0.0028868, places=6)
        # With no repeatability, u_c = sqrt(3 * 0.0028868^2)
        self.assertAlmostEqual(float(budget['u_combined']), 0.005, places=4)
        self.assertEqual(budget['k'], Decimal(2))
        self.assertAlmostEqual(float(budget['expanded']), 0.01, places=4)

    def test_repeatability_dominates(self) -> None:
        budget = compute_uncertainty_budget(
            d=Decimal('0.01'), mpe=Decimal('0.015'),
            rep_std_dev=Decimal('0.1'),
        )
        # Repeatability far larger than other terms -> u_c ~ 0.1, U ~ 0.2
        self.assertAlmostEqual(float(budget['u_combined']), 0.1, places=3)
        self.assertAlmostEqual(float(budget['expanded']), 0.2, places=2)

    def test_expanded_is_k_times_combined(self) -> None:
        budget = compute_uncertainty_budget(
            d=Decimal('0.5'), mpe=Decimal('1'), rep_std_dev=Decimal('0.3'),
        )
        self.assertEqual(budget['expanded'], budget['k'] * budget['u_combined'])


class TestRoundUncertainty(SimpleTestCase):
    def test_rounds_up_to_resolution(self) -> None:
        # 0.0123 rounded up at d=0.01 resolution -> 0.02
        self.assertEqual(
            round_uncertainty(Decimal('0.0123'), Decimal('0.01')),
            Decimal('0.02'),
        )

    def test_exact_value_not_inflated(self) -> None:
        self.assertEqual(
            round_uncertainty(Decimal('0.02'), Decimal('0.01')),
            Decimal('0.02'),
        )

    def test_integer_resolution(self) -> None:
        self.assertEqual(
            round_uncertainty(Decimal('3.2'), Decimal('1')), Decimal('4'))
