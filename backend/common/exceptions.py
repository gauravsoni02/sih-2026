from rest_framework.exceptions import APIException


class CalculationError(APIException):
    status_code = 422
    default_detail = 'Calculation failed due to invalid input.'
    default_code = 'calculation_error'


class ReportGenerationError(APIException):
    status_code = 500
    default_detail = 'Report generation failed.'
    default_code = 'report_generation_error'
