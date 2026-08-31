from .constants import ComplianceStatus


def overall_verdict(results: list[ComplianceStatus]) -> ComplianceStatus:
    """Determine overall verdict from individual test results.

    If any test FAILS, the overall verdict is FAIL.
    NOT_APPLICABLE tests are ignored.
    If all applicable tests PASS, the overall verdict is PASS.
    If no applicable tests exist, returns NOT_APPLICABLE.
    """
    applicable = [r for r in results if r != ComplianceStatus.NOT_APPLICABLE]

    if not applicable:
        return ComplianceStatus.NOT_APPLICABLE

    if any(r == ComplianceStatus.FAIL for r in applicable):
        return ComplianceStatus.FAIL

    return ComplianceStatus.PASS
