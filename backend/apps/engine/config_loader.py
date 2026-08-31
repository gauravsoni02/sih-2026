import json
import os
from decimal import Decimal
from functools import lru_cache
from typing import Any


DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), 'config', 'r76_2006.json'
)

DEFAULT_R76_2_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), 'config', 'r76_2_2006.json'
)


@lru_cache(maxsize=4)
def _load_raw(path: str) -> dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# R 76-1 accessors (metrological requirements)
# ---------------------------------------------------------------------------

def get_config(path: str | None = None) -> dict[str, Any]:
    config_path = path or os.environ.get('NAWI_STANDARD_CONFIG', DEFAULT_CONFIG_PATH)
    return _load_raw(config_path)


def get_mpe_table(config: dict[str, Any] | None = None) -> dict[str, list[tuple[int, int, Decimal]]]:
    cfg = config or get_config()
    table: dict[str, list[tuple[int, int, Decimal]]] = {}
    for cls, ranges in cfg['mpe_table'].items():
        table[cls] = [
            (r['lower'], r['upper'], Decimal(r['factor']))
            for r in ranges
        ]
    return table


def get_subsequent_multiplier(config: dict[str, Any] | None = None) -> Decimal:
    cfg = config or get_config()
    return Decimal(cfg['verification']['subsequent_multiplier'])


def get_accuracy_classes(config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = config or get_config()
    return cfg['accuracy_classes']


def get_min_capacity_multipliers(config: dict[str, Any] | None = None) -> dict[str, int]:
    cfg = config or get_config()
    return {
        cls: info['min_capacity_multiplier']
        for cls, info in cfg['accuracy_classes'].items()
    }


def get_test_param(test_name: str, param_name: str, config: dict[str, Any] | None = None) -> Any:
    cfg = config or get_config()
    return cfg['test_parameters'][test_name][param_name]


def get_test_applicability(test_name: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = config or get_config()
    return cfg['test_applicability'].get(test_name, {})


def get_scale_interval_rules(config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = config or get_config()
    return cfg['scale_intervals']


def get_unit_conversion(unit: str, target: str, config: dict[str, Any] | None = None) -> Decimal:
    cfg = config or get_config()
    key = f'to_{target}'
    return Decimal(cfg['units'][unit][key])


# ---------------------------------------------------------------------------
# R 76-2 accessors (test procedures)
# ---------------------------------------------------------------------------

def get_r76_2_config(path: str | None = None) -> dict[str, Any]:
    config_path = path or os.environ.get(
        'NAWI_PROCEDURE_CONFIG', DEFAULT_R76_2_CONFIG_PATH
    )
    return _load_raw(config_path)


def get_evaluation_type_config(
    evaluation_type: str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = config or get_r76_2_config()
    et = cfg['evaluation_types'].get(evaluation_type)
    if et is None:
        raise ValueError(f"Unknown evaluation type: {evaluation_type}")
    return et


def get_required_tests(
    evaluation_type: str,
    config: dict[str, Any] | None = None,
) -> list[str]:
    et = get_evaluation_type_config(evaluation_type, config)
    return list(et['required_tests'])


def get_evaluation_verification_type(
    evaluation_type: str,
    config: dict[str, Any] | None = None,
) -> str:
    et = get_evaluation_type_config(evaluation_type, config)
    return et['verification_type']


def get_weighing_performance_config(
    evaluation_type: str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    et = get_evaluation_type_config(evaluation_type, config)
    return et.get('weighing_performance', {})


def get_repeatability_config(
    evaluation_type: str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    et = get_evaluation_type_config(evaluation_type, config)
    return et.get('repeatability', {})


def get_environmental_conditions(
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = config or get_r76_2_config()
    return cfg['environmental_conditions']


def get_test_sequence(
    config: dict[str, Any] | None = None,
) -> list[str]:
    cfg = config or get_r76_2_config()
    return list(cfg['test_sequence'])


def get_report_format(
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = config or get_r76_2_config()
    return cfg['report_format']


# ---------------------------------------------------------------------------
# Cache management
# ---------------------------------------------------------------------------

def reload_config() -> None:
    _load_raw.cache_clear()
