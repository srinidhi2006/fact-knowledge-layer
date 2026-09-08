"""
Custom domain exceptions for Fact Knowledge Layer.
"""

class FactLayerException(Exception):
    """Base exception for all domain errors."""
    pass


class DocumentParsingError(FactLayerException):
    """Raised when PDF extraction or parsing fails."""
    pass


class FactExtractionError(FactLayerException):
    """Raised when structured fact extraction encounters an unrecoverable failure."""
    pass


class NormalizationError(FactLayerException):
    """Raised when unit, scale, or period normalization fails."""
    pass


class MatchingError(FactLayerException):
    """Raised when candidate matching or vector generation fails."""
    pass


class ComparisonError(FactLayerException):
    """Raised when the relationship comparison engine fails."""
    pass
