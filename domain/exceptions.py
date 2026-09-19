class DomainError(ValueError):
    """Base exception for domain-layer validation and persistence errors."""


class AnalysisOutputError(DomainError):
    """Raised when an analysis output cannot be converted into a valid prediction input."""


class LLMGenerationError(DomainError):
    """Raised when the LLM fails to produce usable output."""


class PredictionValidationError(DomainError):
    """Raised when a prediction payload fails validation."""


class RealityValidationError(DomainError):
    """Raised when reality data is invalid for evaluation."""


class EvaluationValidationError(DomainError):
    """Raised when evaluation inputs or scores are invalid."""
