from decimal import Decimal

from django.test import TestCase

from apps.engine.test_procedures import (
    generate_discrimination_loads,
    generate_repeatability_loads,
    generate_weighing_test_points,
    get_recommended_test_order,
    get_repeatability_min_repetitions,
    get_tests_for_evaluation,
    get_verification_type_for_evaluation,
    validate_environmental_conditions,
    validate_repeatability_readings,
    validate_test_completeness,
)


class TestEvaluationTypeMapping(TestCase):

    def test_type_evaluation_uses_initial_verification(self):
        self.assertEqual(
            get_verification_type_for_evaluation('type_evaluation'),
            'initial',
        )

    def test_initial_verification_uses_initial(self):
        self.assertEqual(
            get_verification_type_for_evaluation('initial_verification'),
            'initial',
        )

    def test_subsequent_verification_uses_subsequent(self):
        self.assertEqual(
            get_verification_type_for_evaluation('subsequent_verification'),
            'subsequent',
        )

    def test_invalid_evaluation_type_raises(self):
        with self.assertRaises(ValueError):
            get_verification_type_for_evaluation('nonexistent')


class TestRequiredTests(TestCase):

    def test_type_evaluation_includes_all_tests(self):
        tests = get_tests_for_evaluation('type_evaluation', 'III')
        self.assertIn('weighing_performance', tests)
        self.assertIn('eccentricity', tests)
        self.assertIn('repeatability', tests)
        self.assertIn('discrimination', tests)
        self.assertIn('sensitivity', tests)
        self.assertIn('tare', tests)
        self.assertIn('creep', tests)
        self.assertIn('temperature', tests)
        self.assertIn('tilt', tests)

    def test_initial_verification_subset(self):
        tests = get_tests_for_evaluation('initial_verification', 'III')
        self.assertIn('weighing_performance', tests)
        self.assertIn('eccentricity', tests)
        self.assertIn('repeatability', tests)
        self.assertIn('discrimination', tests)
        self.assertNotIn('temperature', tests)
        self.assertNotIn('tilt', tests)
        self.assertNotIn('power_supply', tests)

    def test_subsequent_verification_minimal(self):
        tests = get_tests_for_evaluation('subsequent_verification', 'III')
        self.assertIn('weighing_performance', tests)
        self.assertIn('repeatability', tests)
        self.assertEqual(len(tests), 2)

    def test_class_i_excludes_tilt(self):
        tests = get_tests_for_evaluation('type_evaluation', 'I')
        self.assertNotIn('tilt', tests)

    def test_class_iii_includes_tilt(self):
        tests = get_tests_for_evaluation('type_evaluation', 'III')
        self.assertIn('tilt', tests)

    def test_durability_excluded_for_heavy_instruments(self):
        tests = get_tests_for_evaluation(
            'type_evaluation', 'III', max_capacity_kg=Decimal('200')
        )
        self.assertNotIn('durability', tests)

    def test_durability_included_for_light_instruments(self):
        tests = get_tests_for_evaluation(
            'type_evaluation', 'III', max_capacity_kg=Decimal('50')
        )
        self.assertIn('durability', tests)


class TestWeighingTestPointGeneration(TestCase):

    def test_class_iii_type_evaluation_generates_enough_points(self):
        points = generate_weighing_test_points(
            accuracy_class='III',
            max_capacity=Decimal('30000'),
            e=Decimal('20'),
            min_capacity=Decimal('400'),
            evaluation_type='type_evaluation',
        )
        self.assertIn(Decimal('400'), points)
        self.assertIn(Decimal('30000'), points)
        self.assertGreaterEqual(len(points), 9)

    def test_class_iii_initial_verification_fewer_points(self):
        te_points = generate_weighing_test_points(
            accuracy_class='III',
            max_capacity=Decimal('30000'),
            e=Decimal('20'),
            min_capacity=Decimal('400'),
            evaluation_type='type_evaluation',
        )
        iv_points = generate_weighing_test_points(
            accuracy_class='III',
            max_capacity=Decimal('30000'),
            e=Decimal('20'),
            min_capacity=Decimal('400'),
            evaluation_type='initial_verification',
        )
        self.assertGreater(len(te_points), len(iv_points))

    def test_subsequent_verification_fewest_points(self):
        sv_points = generate_weighing_test_points(
            accuracy_class='III',
            max_capacity=Decimal('30000'),
            e=Decimal('20'),
            min_capacity=Decimal('400'),
            evaluation_type='subsequent_verification',
        )
        iv_points = generate_weighing_test_points(
            accuracy_class='III',
            max_capacity=Decimal('30000'),
            e=Decimal('20'),
            min_capacity=Decimal('400'),
            evaluation_type='initial_verification',
        )
        self.assertLessEqual(len(sv_points), len(iv_points))

    def test_includes_min_and_max(self):
        points = generate_weighing_test_points(
            accuracy_class='III',
            max_capacity=Decimal('30000'),
            e=Decimal('20'),
            min_capacity=Decimal('400'),
        )
        self.assertEqual(points[0], Decimal('400'))
        self.assertEqual(points[-1], Decimal('30000'))

    def test_includes_mpe_zone_boundary(self):
        points = generate_weighing_test_points(
            accuracy_class='III',
            max_capacity=Decimal('30000'),
            e=Decimal('20'),
            min_capacity=Decimal('400'),
        )
        boundary = Decimal('500') * Decimal('20')  # 10000g
        self.assertIn(boundary, points)

    def test_points_are_sorted(self):
        points = generate_weighing_test_points(
            accuracy_class='III',
            max_capacity=Decimal('30000'),
            e=Decimal('20'),
            min_capacity=Decimal('400'),
        )
        self.assertEqual(points, sorted(points))

    def test_class_i_generates_points(self):
        points = generate_weighing_test_points(
            accuracy_class='I',
            max_capacity=Decimal('100'),
            e=Decimal('0.001'),
            min_capacity=Decimal('0.1'),
        )
        self.assertIn(Decimal('0.1'), points)
        self.assertIn(Decimal('100'), points)
        self.assertGreaterEqual(len(points), 4)

    def test_invalid_accuracy_class_raises(self):
        with self.assertRaises(ValueError):
            generate_weighing_test_points(
                accuracy_class='V',
                max_capacity=Decimal('1000'),
                e=Decimal('1'),
                min_capacity=Decimal('20'),
            )


class TestRepeatabilityProcedure(TestCase):

    def test_type_evaluation_10_repetitions(self):
        self.assertEqual(
            get_repeatability_min_repetitions('type_evaluation'), 10
        )

    def test_initial_verification_3_repetitions(self):
        self.assertEqual(
            get_repeatability_min_repetitions('initial_verification'), 3
        )

    def test_subsequent_verification_3_repetitions(self):
        self.assertEqual(
            get_repeatability_min_repetitions('subsequent_verification'), 3
        )

    def test_repeatability_loads_initial(self):
        loads = generate_repeatability_loads(
            Decimal('30000'), 'initial_verification'
        )
        self.assertIn(Decimal('15000'), loads)
        self.assertIn(Decimal('30000'), loads)

    def test_repeatability_loads_subsequent(self):
        loads = generate_repeatability_loads(
            Decimal('30000'), 'subsequent_verification'
        )
        self.assertEqual(loads, [Decimal('30000')])

    def test_validate_insufficient_readings(self):
        warnings = validate_repeatability_readings(2, 'type_evaluation')
        self.assertEqual(len(warnings), 1)
        self.assertIn('10', warnings[0])

    def test_validate_sufficient_readings(self):
        warnings = validate_repeatability_readings(10, 'type_evaluation')
        self.assertEqual(len(warnings), 0)


class TestDiscriminationLoads(TestCase):

    def test_initial_verification_three_loads(self):
        loads = generate_discrimination_loads(
            Decimal('30000'), Decimal('400'), 'initial_verification'
        )
        self.assertEqual(len(loads), 3)
        self.assertIn(Decimal('400'), loads)
        self.assertIn(Decimal('15000'), loads)
        self.assertIn(Decimal('30000'), loads)

    def test_min_used_for_zero_fraction(self):
        loads = generate_discrimination_loads(
            Decimal('30000'), Decimal('400'), 'type_evaluation'
        )
        self.assertIn(Decimal('400'), loads)
        self.assertNotIn(Decimal('0'), loads)


class TestEnvironmentalConditions(TestCase):

    def test_valid_conditions_no_warnings(self):
        warnings = validate_environmental_conditions(
            temperature_start=Decimal('20.0'),
            temperature_end=Decimal('20.5'),
            humidity=Decimal('50.0'),
            barometric_pressure=Decimal('1013.0'),
        )
        self.assertEqual(len(warnings), 0)

    def test_temperature_too_high(self):
        warnings = validate_environmental_conditions(
            temperature_start=Decimal('26.0'),
            temperature_end=None,
            humidity=None,
            barometric_pressure=None,
        )
        self.assertEqual(len(warnings), 1)
        self.assertIn('temperature', warnings[0].lower())

    def test_temperature_too_low(self):
        warnings = validate_environmental_conditions(
            temperature_start=Decimal('14.0'),
            temperature_end=None,
            humidity=None,
            barometric_pressure=None,
        )
        self.assertEqual(len(warnings), 1)

    def test_temperature_variation_too_large(self):
        warnings = validate_environmental_conditions(
            temperature_start=Decimal('19.0'),
            temperature_end=Decimal('21.0'),
            humidity=None,
            barometric_pressure=None,
        )
        self.assertEqual(len(warnings), 1)
        self.assertIn('variation', warnings[0].lower())

    def test_humidity_too_high(self):
        warnings = validate_environmental_conditions(
            temperature_start=None,
            temperature_end=None,
            humidity=Decimal('85.0'),
            barometric_pressure=None,
        )
        self.assertEqual(len(warnings), 1)
        self.assertIn('humidity', warnings[0].lower())

    def test_pressure_out_of_range(self):
        warnings = validate_environmental_conditions(
            temperature_start=None,
            temperature_end=None,
            humidity=None,
            barometric_pressure=Decimal('850.0'),
        )
        self.assertEqual(len(warnings), 1)
        self.assertIn('pressure', warnings[0].lower())

    def test_all_none_no_warnings(self):
        warnings = validate_environmental_conditions(
            None, None, None, None
        )
        self.assertEqual(len(warnings), 0)


class TestTestCompleteness(TestCase):

    def test_all_required_present(self):
        missing, extra = validate_test_completeness(
            ['weighing_performance', 'repeatability'],
            'subsequent_verification',
            'III',
        )
        self.assertEqual(missing, [])
        self.assertEqual(extra, [])

    def test_missing_tests(self):
        missing, extra = validate_test_completeness(
            ['weighing_performance'],
            'subsequent_verification',
            'III',
        )
        self.assertIn('repeatability', missing)

    def test_extra_tests(self):
        missing, extra = validate_test_completeness(
            ['weighing_performance', 'repeatability', 'temperature'],
            'subsequent_verification',
            'III',
        )
        self.assertEqual(missing, [])
        self.assertIn('temperature', extra)

    def test_initial_verification_completeness(self):
        missing, extra = validate_test_completeness(
            ['weighing_performance', 'eccentricity', 'repeatability', 'discrimination'],
            'initial_verification',
            'III',
        )
        self.assertEqual(missing, [])
        self.assertEqual(extra, [])


class TestTestOrdering(TestCase):

    def test_recommended_order(self):
        tests = ['repeatability', 'weighing_performance', 'eccentricity']
        ordered = get_recommended_test_order(tests)
        self.assertEqual(ordered[0], 'weighing_performance')
        self.assertEqual(ordered[1], 'eccentricity')
        self.assertEqual(ordered[2], 'repeatability')
