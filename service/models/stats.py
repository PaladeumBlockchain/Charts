from .base import db, orm

class Stats(db.Entity):
    _table_ = "chart_stats"

    transactions = orm.Required(int, default=0)
    addresses = orm.Required(int, default=0)
    tokens = orm.Required(int, default=0)
    nodes = orm.Required(int, default=0)
