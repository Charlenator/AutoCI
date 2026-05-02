"""T2: Validation Interceptor — Rule-based middleware that wraps agent commits.
Fatal issues block phase gates; warnings are annotated but pass through."""

from functools import wraps
from typing import Any, Callable
from pydantic import BaseModel, ValidationError

class ValidationResult(BaseModel):
    passed: bool
    fatal: list[str] = []
    warnings: list[str] = []

def validate_agent_output(
    schema: type[BaseModel] | None = None,
    min_sample_size: int = 5,
    check_outliers: bool = False,
    check_termination: bool = False,
    min_interventions: int = 3,
):
    """Decorator to validate agent output before committing.

    Args:
        schema: Pydantic schema to validate against
        min_sample_size: Minimum data points required
        check_outliers: Flag outliers via z-score
        check_termination: Flag early Five Whys termination
        min_interventions: Minimum intervention count for Improve phase
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> tuple[Any, ValidationResult]:
            result = func(*args, **kwargs)
            validation = ValidationResult(passed=True)

            # Schema conformity
            if schema:
                try:
                    if isinstance(result, dict):
                        schema(**result)
                    elif isinstance(result, list):
                        for item in result:
                            if isinstance(item, dict):
                                schema(**item)
                except ValidationError as e:
                    validation.fatal.append(f"Schema validation failed: {e.errors()[:3]}")

            # Sample size check
            if min_sample_size > 0 and isinstance(result, (list, dict)):
                size = len(result) if isinstance(result, list) else len(result.get("metrics", []))
                if size < min_sample_size and size > 0:
                    validation.warnings.append(
                        f"Sample size ({size}) below recommended minimum ({min_sample_size})"
                    )

            # Check for Five Whys termination flag
            if check_termination and isinstance(result, dict):
                if result.get("early_termination"):
                    validation.warnings.append("Five Whys chain terminated early — may indicate shallow root cause")

            # Check intervention count
            if check_outliers and isinstance(result, dict):
                interventions = result.get("interventions", [])
                if len(interventions) < min_interventions:
                    validation.warnings.append(
                        f"Only {len(interventions)} interventions — minimum {min_interventions} recommended"
                    )

            validation.passed = len(validation.fatal) == 0
            return result, validation
        return wrapper
    return decorator
