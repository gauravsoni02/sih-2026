"""Measurement uncertainty budget for NAWI verification (simplified EURAMET cg-18).

Components considered for each weighing test point:

- Type A: repeatability of the instrument, taken as the sample standard
  deviation of the repeatability trial readings.
- Type B: rounding of the indication at zero and at load, each d/(2*sqrt(3))
  (rectangular distribution over one scale interval).
- Type B: reference standard weights. Legal metrology practice requires the
  error of the standards used to be no worse than 1/3 of the instrument MPE,
  treated as a rectangular distribution: (MPE/3)/sqrt(3).

Combined standard uncertainty is the root sum of squares; the expanded
uncertainty U uses a coverage factor k=2 (~95% confidence).
"""

from decimal import ROUND_CEILING, Decimal

SQRT3 = Decimal(3).sqrt()
K_DEFAULT = Decimal(2)


def repeatability_std_dev(readings: list[Decimal]) -> Decimal:
    """Sample standard deviation (n-1 denominator) of repeatability readings."""
    n = len(readings)
    if n < 2:
        return Decimal('0')
    mean = sum(readings) / n
    variance = sum((r - mean) ** 2 for r in readings) / (n - 1)
    return variance.sqrt()


def compute_uncertainty_budget(
    *,
    d: Decimal,
    mpe: Decimal,
    rep_std_dev: Decimal = Decimal('0'),
    k: Decimal = K_DEFAULT,
    u_ref_override: Decimal | None = None,
) -> dict:
    """Build the uncertainty budget for one test point.

    Returns a dict with each component, the combined standard uncertainty,
    and the expanded uncertainty U = k * u_c.

    Reference-weight component (u_reference_weights):
    when ``u_ref_override`` is provided it is used directly — this should be
    the standard uncertainty taken from the reference weights' calibration
    certificate (certificate U divided by its coverage factor), which is the
    metrologically correct source. When it is None, the legal-metrology
    fallback applies: the maximum permissible error of the standards is
    assumed to be no worse than 1/3 of the instrument MPE (OIML R 76-1,
    3.7.1) and is treated as a rectangular distribution, giving
    (MPE/3)/sqrt(3). This fallback is an assumption of the standards'
    conformity class, not their actual calibration data, and should only be
    relied on when the calibration certificate uncertainty is unavailable.
    """
    u_rep = rep_std_dev
    u_res_zero = d / (2 * SQRT3)
    u_res_load = d / (2 * SQRT3)
    u_ref = u_ref_override if u_ref_override is not None else (mpe / 3) / SQRT3

    u_combined = (
        u_rep ** 2 + u_res_zero ** 2 + u_res_load ** 2 + u_ref ** 2
    ).sqrt()
    expanded = k * u_combined

    return {
        'u_repeatability': u_rep,
        'u_resolution_zero': u_res_zero,
        'u_resolution_load': u_res_load,
        'u_reference_weights': u_ref,
        'u_combined': u_combined,
        'k': k,
        'expanded': expanded,
    }


def round_uncertainty(value: Decimal, d: Decimal) -> Decimal:
    """Round U up (conservative) to the resolution of the scale interval d.

    NABL practice never rounds uncertainty down. If d has an unusual
    exponent, fall back to 6 decimal places.
    """
    try:
        quantum = d.normalize()
        if quantum <= 0:
            quantum = Decimal('0.000001')
    except Exception:
        quantum = Decimal('0.000001')
    return value.quantize(quantum, rounding=ROUND_CEILING)
