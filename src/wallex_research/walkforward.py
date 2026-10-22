#!/usr/bin/env python
"""Chronological walk-forward evaluation with explicit train/validation/test split.

Prevents future-data leakage by enforcing temporal boundaries.  The split is
deterministic for identical configuration and input.  No strategy backtesting,
profitability claim, or live-trading authorization is implied.
"""