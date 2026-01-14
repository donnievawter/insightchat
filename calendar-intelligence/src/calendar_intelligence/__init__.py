"""
Calendar Intelligence Library

A reusable library for analyzing calendar events and queries across different data sources.

Main exports:
- CalendarAnalyzer: Main orchestrator for calendar intelligence
- CalendarRepository: Abstract base class for data sources
- IcsRepository: ICS/iCal API implementation
- IntentDetector: Natural language query understanding
- EventFormatter: Event display formatting
"""

from .analyzer import CalendarAnalyzer
from .repositories import CalendarRepository, IcsRepository
from .intent import IntentDetector
from .formatter import EventFormatter

__version__ = "0.1.0"

__all__ = [
    'CalendarAnalyzer',
    'CalendarRepository',
    'IcsRepository',
    'IntentDetector',
    'EventFormatter',
]
