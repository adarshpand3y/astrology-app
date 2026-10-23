"""Pure-Python Vedic astrology engine (no Django dependency).

Public entry points live in :mod:`.chart`.
"""
from .chart import ENGINE_VERSION, BirthInput, ChartContext, compute_chart, compute_strengths  # noqa: F401
