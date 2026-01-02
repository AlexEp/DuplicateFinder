"""Core interfaces for dependency inversion."""
from .view_interface import IView
from .repository_interface import IRepository, IFileRepository
from .strategy_interface import IComparisonStrategy, IMetadataCalculator
from .service_interface import IComparisonService, IFileService

__all__ = [
    'IView', 'IRepository', 'IFileRepository',
    'IComparisonStrategy', 'IMetadataCalculator',
    'IComparisonService', 'IFileService'
]
