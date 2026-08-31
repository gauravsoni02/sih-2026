from decimal import Decimal

from django.test import TestCase

from apps.engine.compliance import overall_verdict
from apps.engine.constants import ComplianceStatus
from apps.engine.mpe import get_mpe
from apps.engine.calculations import compute_error, check_error_compliance


class TestOverallVerdict(TestCase):
    def test_all_pass(self) -> None:
        results = [ComplianceStatus.PASS, ComplianceStatus.PASS, ComplianceStatus.PASS]
        self.assertEqual(overall_verdict(results), ComplianceStatus.PASS)

    def test_one_fail(self) -> None:
        results = [ComplianceStatus.PASS, ComplianceStatus.FAIL, ComplianceStatus.PASS]
        self.assertEqual(overall_verdict(results), ComplianceStatus.FAIL)

    def test_all_not_applicable(self) -> None:
        results = [ComplianceStatus.NOT_APPLICABLE, ComplianceStatus.NOT_APPLICABLE]
        self.assertEqual(overall_verdict(results), ComplianceStatus.NOT_APPLICABLE)

    def test_pass_with_not_applicable(self) -> None:
        results = [
            ComplianceStatus.PASS,
            ComplianceStatus.NOT_APPLICABLE,
            ComplianceStatus.PASS,
        ]
        self.assertEqual(overall_verdict(results), ComplianceStatus.PASS)

    def test_fail_with_not_applicable(self) -> None:
        results = [
            ComplianceStatus.PASS,
            ComplianceStatus.NOT_APPLICABLE,
            ComplianceStatus.FAIL,
        ]
        self.assertEqual(overall_verdict(results), ComplianceStatus.FAIL)

    def test_empty_results(self) -> None:
        self.assertEqual(overall_verdict([]), ComplianceStatus.NOT_APPLICABLE)


class TestEndToEndAccuracyClasses(TestCase):
    """Test 27: End-to-end with all 4 accuracy classes."""

    def _run_weighing_test(
        self,
        accuracy_class: str,
        e: Decimal,
        test_points: list[tuple[Decimal, Decimal]],
        verification_type: str = 'initial',
    ) -> ComplianceStatus:
        results = []
        for load, indicated in test_points:
            error = compute_error(indicated, load)
            mpe = get_mpe(accuracy_class, load, e, verification_type)
            results.append(check_error_compliance(error, mpe))
        return overall_verdict(results)

    def test_class_I_pass(self) -> None:
        e = Decimal('0.001')
        test_points = [
            (Decimal('0.1'), Decimal('0.1004')),
            (Decimal('10'), Decimal('10.0004')),
            (Decimal('50'), Decimal('49.9996')),
            (Decimal('100'), Decimal('100.0009')),
            (Decimal('200'), Decimal('199.9991')),
        ]
        self.assertEqual(self._run_weighing_test('I', e, test_points), ComplianceStatus.PASS)

    def test_class_II_pass(self) -> None:
        e = Decimal('0.01')
        test_points = [
            (Decimal('1'), Decimal('1.004')),
            (Decimal('50'), Decimal('49.995')),
            (Decimal('100'), Decimal('100.009')),
            (Decimal('500'), Decimal('500.014')),
            (Decimal('1000'), Decimal('999.985')),
        ]
        self.assertEqual(self._run_weighing_test('II', e, test_points), ComplianceStatus.PASS)

    def test_class_III_pass(self) -> None:
        e = Decimal('5')
        test_points = [
            (Decimal('100'), Decimal('102')),
            (Decimal('2500'), Decimal('2498')),
            (Decimal('5000'), Decimal('5004')),
            (Decimal('15000'), Decimal('15007')),
            (Decimal('50000'), Decimal('49993')),
        ]
        self.assertEqual(self._run_weighing_test('III', e, test_points), ComplianceStatus.PASS)

    def test_class_IIII_pass(self) -> None:
        e = Decimal('5')
        test_points = [
            (Decimal('50'), Decimal('52')),
            (Decimal('250'), Decimal('248')),
            (Decimal('500'), Decimal('504')),
            (Decimal('1000'), Decimal('997')),
            (Decimal('5000'), Decimal('4993')),
        ]
        self.assertEqual(self._run_weighing_test('IIII', e, test_points), ComplianceStatus.PASS)

    def test_class_III_fail(self) -> None:
        e = Decimal('5')
        test_points = [
            (Decimal('100'), Decimal('102')),
            (Decimal('2500'), Decimal('2510')),  # error=10, MPE=5 -> FAIL
            (Decimal('5000'), Decimal('5004')),
        ]
        self.assertEqual(self._run_weighing_test('III', e, test_points), ComplianceStatus.FAIL)
