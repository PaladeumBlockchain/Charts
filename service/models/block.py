from datetime import datetime
from decimal import Decimal
from email.policy import default
from .base import db
from pony import orm

class Block(db.Entity):
    _table_ = "chart_blocks"

    blockhash = orm.Required(str, index=True)
    height = orm.Required(int, index=True)
    created = orm.Required(datetime)

    transactions = orm.Required(int, default=0)
    addresses = orm.Required(int, default=0)
    tokens = orm.Required(int, default=0)

    previous_block = orm.Optional("Block")
    next_block = orm.Optional("Block")

    currency_transactions = orm.Set("CurrencyTransactions")

class CurrencyTransactions(db.Entity):
    _table_ = "chart_currency_transactions"

    transactions = orm.Required(int)
    currency = orm.Required(str)

    block = orm.Required("Block")
