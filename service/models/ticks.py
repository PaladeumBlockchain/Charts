from datetime import datetime
from .base import db
from pony import orm


class TokenTick(db.Entity):
    _table_ = "chart_tokens"

    value = orm.Required(int, default=0)
    timestamp = orm.Required(datetime)
    interval = orm.Required(int)


class TransactionTick(db.Entity):
    _table_ = "chart_transactions"

    value = orm.Required(int, default=0)
    timestamp = orm.Required(datetime)
    currency = orm.Required(str)
    interval = orm.Required(int)


class AddressTick(db.Entity):
    _table_ = "chart_addresses"

    value = orm.Required(int, default=0)
    timestamp = orm.Required(datetime)
    interval = orm.Required(int)


class PriceTick(db.Entity):
    _table_ = "chart_prices"

    volume = orm.Required(float, default=0)
    price = orm.Required(float, default=0)
    cap = orm.Required(float, default=0)
    timestamp = orm.Required(datetime)
    interval = orm.Required(int)
