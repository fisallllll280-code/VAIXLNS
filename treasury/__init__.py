"""VAIXLNS paper treasury execution fabric.

This package is simulation/paper only. It never accesses real wallets,
exchanges, banks, custody systems, or secret keys.
"""

from .paper_treasury import PaperTreasury, TreasuryPolicy, TransactionIntent

__all__ = ["PaperTreasury", "TreasuryPolicy", "TransactionIntent"]
