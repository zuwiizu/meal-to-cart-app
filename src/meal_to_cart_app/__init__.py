"""The take-home app: a stranger brings links, answers a form, gets a cart.

This package holds NO household values and never will. Values live in
profiles/<name>/values.json, and the demo profile's are invented.

Importing this package also points the ENGINE at this repository:
meal_to_cart.profile reads MTC_ROOT, so every profile the engine resolves for
this process -- values, rules, recipes -- is one of ours. That is the split made
real rather than promised: the household's private profile is not on any path
this process builds, and the engine stays the same single engine the household's
own runs use.
"""
from __future__ import annotations

import os
from pathlib import Path

# src/meal_to_cart_app/__init__.py -> src -> the repository root.
ROOT = Path(__file__).resolve().parents[2]

# The engine's profile root, relocated to the app. Unconditional: an app that
# read the household's profiles would be the two-repo split failing quietly. A
# test may still override it after import.
os.environ["MTC_ROOT"] = str(ROOT)
