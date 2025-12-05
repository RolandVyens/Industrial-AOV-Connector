# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Roland Vyens
"""Core module for Industrial AOV Connector."""

from .preferences import IDS_AddonPrefs
from .properties import register_properties, unregister_properties
from . import node_builder

__all__ = [
    "IDS_AddonPrefs",
    "register_properties",
    "unregister_properties",
    "node_builder",
]
