from decimal import Decimal

from django.test import TestCase

from apps.engine.mpe import get_mpe, get_mpe_multi_interval


class TestMPELookup(TestCase):
    """Tests 1-5: MPE lookup for all accuracy classes."""

    # Test 1: MPE at every boundary point for all classes
    def test_class_I_boundaries(self) -> None:
        e = Decimal('0.001')
        self.assertEqual(get_mpe('I', Decimal('0'), e), Decimal('0.0005'))
        self.assertEqual(get_mpe('I', Decimal('50') * e, e), Decimal('0.0005'))
        self.assertEqual(get_mpe('I', Decimal('50000') * e, e), Decimal('0.0005'))
        self.assertEqual(get_mpe('I', Decimal('50001') * e, e), Decimal('0.001'))
        self.assertEqual(get_mpe('I', Decimal('200000') * e, e), Decimal('0.001'))

    def test_class_II_boundaries(self) -> None:
        e = Decimal('0.01')
        self.assertEqual(get_mpe('II', Decimal('0'), e), Decimal('0.005'))
        self.assertEqual(get_mpe('II', Decimal('5000') * e, e), Decimal('0.005'))
        self.assertEqual(get_mpe('II', Decimal('5001') * e, e), Decimal('0.01'))
        self.assertEqual(get_mpe('II', Decimal('20000') * e, e), Decimal('0.01'))
        self.assertEqual(get_mpe('II', Decimal('20001') * e, e), Decimal('0.015'))
        self.assertEqual(get_mpe('II', Decimal('100000') * e, e), Decimal('0.015'))

    def test_class_III_boundaries(self) -> None:
        e = Decimal('1')
        self.assertEqual(get_mpe('III', Decimal('0'), e), Decimal('0.5'))
        self.assertEqual(get_mpe('III', Decimal('500'), e), Decimal('0.5'))
        self.assertEqual(get_mpe('III', Decimal('501'), e), Decimal('1.0'))
        self.assertEqual(get_mpe('III', Decimal('2000'), e), Decimal('1.0'))
        self.assertEqual(get_mpe('III', Decimal('2001'), e), Decimal('1.5'))
        self.assertEqual(get_mpe('III', Decimal('10000'), e), Decimal('1.5'))

    def test_class_IIII_boundaries(self) -> None:
        e = Decimal('5')
        self.assertEqual(get_mpe('IIII', Decimal('0'), e), Decimal('2.5'))
        self.assertEqual(get_mpe('IIII', Decimal('250'), e), Decimal('2.5'))
        self.assertEqual(get_mpe('IIII', Decimal('255'), e), Decimal('5'))
        self.assertEqual(get_mpe('IIII', Decimal('1000'), e), Decimal('5'))
        self.assertEqual(get_mpe('IIII', Decimal('1005'), e), Decimal('7.5'))
        self.assertEqual(get_mpe('IIII', Decimal('5000'), e), Decimal('7.5'))

    # Test 2: MPE at boundary +/- 1
    def test_class_III_boundary_plus_minus_one(self) -> None:
        e = Decimal('1')
        # 499e -> 0.5e (still in first range)
        self.assertEqual(get_mpe('III', Decimal('499'), e), Decimal('0.5'))
        # 500e -> 0.5e (AT boundary, stays in lower range)
        self.assertEqual(get_mpe('III', Decimal('500'), e), Decimal('0.5'))
        # 501e -> 1.0e (crossed boundary)
        self.assertEqual(get_mpe('III', Decimal('501'), e), Decimal('1.0'))

    # Test 3: MPE at zero load
    def test_zero_load(self) -> None:
        for cls in ('I', 'II', 'III', 'IIII'):
            e = Decimal('1')
            mpe = get_mpe(cls, Decimal('0'), e)
            self.assertEqual(mpe, Decimal('0.5'))

    # Test 4: Initial vs subsequent verification
    def test_subsequent_verification_doubles_mpe(self) -> None:
        e = Decimal('1')
        initial = get_mpe('III', Decimal('500'), e, 'initial')
        subsequent = get_mpe('III', Decimal('500'), e, 'subsequent')
        self.assertEqual(subsequent, initial * 2)
        self.assertEqual(initial, Decimal('0.5'))
        self.assertEqual(subsequent, Decimal('1.0'))

    def test_subsequent_all_classes(self) -> None:
        e = Decimal('1')
        for cls, load in [('I', 100), ('II', 1000), ('III', 300), ('IIII', 30)]:
            initial = get_mpe(cls, Decimal(str(load)), e, 'initial')
            subsequent = get_mpe(cls, Decimal(str(load)), e, 'subsequent')
            self.assertEqual(subsequent, initial * 2)

    # Test 5: Class I has no upper bound (n_max unlimited, R 76-1 Table 3);
    # loads beyond 200 000e stay in the 1.0e band.
    def test_class_I_unbounded_above_200000e(self) -> None:
        e = Decimal('0.001')
        self.assertEqual(get_mpe('I', Decimal('200001') * e, e), Decimal('0.001'))
        self.assertEqual(get_mpe('I', Decimal('1000000') * e, e), Decimal('0.001'))

    def test_invalid_accuracy_class(self) -> None:
        with self.assertRaises(ValueError):
            get_mpe('V', Decimal('100'), Decimal('1'))

    def test_negative_load_raises(self) -> None:
        with self.assertRaises(ValueError):
            get_mpe('III', Decimal('-1'), Decimal('1'))

    def test_zero_e_raises(self) -> None:
        with self.assertRaises(ValueError):
            get_mpe('III', Decimal('100'), Decimal('0'))


class TestMPEMultiInterval(TestCase):
    """Tests 6-7: Multi-interval MPE calculation."""

    def setUp(self) -> None:
        # R-76 Section 3.3.1 worked example: Class III, Max=15kg
        self.ranges = [
            {'max': Decimal('2000'), 'e': Decimal('1')},
            {'max': Decimal('5000'), 'e': Decimal('2')},
            {'max': Decimal('15000'), 'e': Decimal('10')},
        ]

    # Test 6: Multi-interval worked example from R-76
    def test_range1_500g(self) -> None:
        mpe = get_mpe_multi_interval('III', Decimal('500'), self.ranges)
        self.assertEqual(mpe, Decimal('0.5'))

    def test_range1_501g(self) -> None:
        mpe = get_mpe_multi_interval('III', Decimal('501'), self.ranges)
        self.assertEqual(mpe, Decimal('1.0'))

    def test_range1_2000g(self) -> None:
        mpe = get_mpe_multi_interval('III', Decimal('2000'), self.ranges)
        self.assertEqual(mpe, Decimal('1.0'))

    def test_range2_2001g(self) -> None:
        # m=2001g, falls in range 2 (e2=2g), m/e2 = 1000.5 -> MPE=1.0*e2=2.0g
        mpe = get_mpe_multi_interval('III', Decimal('2001'), self.ranges)
        self.assertEqual(mpe, Decimal('2.0'))

    def test_range2_4000g(self) -> None:
        # m=4000g, range 2, m/e2 = 2000 -> MPE=1.0*e2=2.0g
        mpe = get_mpe_multi_interval('III', Decimal('4000'), self.ranges)
        self.assertEqual(mpe, Decimal('2.0'))

    def test_range2_4001g(self) -> None:
        # m=4001g, range 2, m/e2 = 2000.5 -> MPE=1.5*e2=3.0g
        mpe = get_mpe_multi_interval('III', Decimal('4001'), self.ranges)
        self.assertEqual(mpe, Decimal('3.0'))

    def test_range2_5000g(self) -> None:
        # m=5000g, range 2, m/e2 = 2500 -> MPE=1.5*e2=3.0g
        mpe = get_mpe_multi_interval('III', Decimal('5000'), self.ranges)
        self.assertEqual(mpe, Decimal('3.0'))

    def test_range3_5001g(self) -> None:
        # m=5001g, range 3 (e3=10g), m/e3 = 500.1 -> MPE=1.0*e3=10.0g
        mpe = get_mpe_multi_interval('III', Decimal('5001'), self.ranges)
        self.assertEqual(mpe, Decimal('10.0'))

    def test_range3_15000g(self) -> None:
        # m=15000g, range 3, m/e3 = 1500 -> MPE=1.0*e3=10.0g
        mpe = get_mpe_multi_interval('III', Decimal('15000'), self.ranges)
        self.assertEqual(mpe, Decimal('10.0'))

    # Test 7: Load exactly at partial range boundary
    def test_exactly_at_max1(self) -> None:
        # Load = 2000g = exactly Max1. Should use e1=1g.
        mpe = get_mpe_multi_interval('III', Decimal('2000'), self.ranges)
        # m/e1 = 2000, which is in range (500, 2000] -> factor 1.0
        self.assertEqual(mpe, Decimal('1.0'))

    def test_above_max_range_raises(self) -> None:
        with self.assertRaises(ValueError):
            get_mpe_multi_interval('III', Decimal('15001'), self.ranges)

    def test_empty_ranges_raises(self) -> None:
        with self.assertRaises(ValueError):
            get_mpe_multi_interval('III', Decimal('100'), [])

    def test_zero_load_multi_interval(self) -> None:
        mpe = get_mpe_multi_interval('III', Decimal('0'), self.ranges)
        self.assertEqual(mpe, Decimal('0.5'))
