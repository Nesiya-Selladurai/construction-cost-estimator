"""Compatibility shim for legacy sklearn pickle module paths."""

from sklearn._loss import *  # noqa: F401,F403
from sklearn._loss.loss import *  # noqa: F401,F403
