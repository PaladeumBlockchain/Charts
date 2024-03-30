from ..models import TransactionTick
from ..services import BlockService
from ..models import AddressTick
from ..models import PriceTick
from ..models import TokenTick
from flask import Blueprint
from ..models import Stats
from .. import constants
from pony import orm

blueprint = Blueprint("stats", __name__)

@blueprint.route("/stats/latest", methods=["GET"])
@orm.db_session
def latest():
    if not (latest_block := BlockService.latest_block()):
        return {
            "error": "Sync not started", "result": None
        }

    return {"error": None, "result": {
        "created": int(latest_block.created.timestamp()),
        "blockhash": latest_block.blockhash,
        "transactions": latest_block.transactions,
        "addresses": latest_block.addresses,
        "tokens": latest_block.tokens,
        "height": latest_block.height
    }}

@blueprint.route("/stats/general", methods=["GET"])
@orm.db_session
def general():
    stats = Stats.select().first()

    models = [AddressTick, TransactionTick, TokenTick]
    change = []

    for model in models:
        value_change = 0

        ticks = model.select(
            lambda t: t.interval == constants.Interval.DAY
        ).order_by(
            lambda t: orm.desc(t.timestamp)
        ).limit(2)

        if len(ticks) == 2:
            value_change = (
                ticks[0].value - ticks[1].value
            )

        change.append(value_change)

    return {
        "error": None,
        "result": {
            "addresses": stats.addresses,
            "transactions": stats.transactions,
            "tokens": stats.tokens,
            "change": {
                "addresses": change[0],
                "transactions": change[1],
                "tokens": change[2]
            }
        }
    }

@blueprint.route("/stats/price", methods=["GET"])
@orm.db_session
def price():
    diff = lambda a, b : round(((a - b) / a) * 100, 2)
    amnt = lambda a : round(a, 4)

    ticks = PriceTick.select(
        lambda t: t.interval == constants.Interval.DAY
    ).order_by(
        lambda t: orm.desc(t.timestamp)
    ).limit(2)

    price_change = 0
    cap_change = 0
    volume_change = 0

    if len(ticks) == 2:
        price_change = diff(ticks[0].price, ticks[1].price)
        cap_change = diff(ticks[0].cap, ticks[1].cap)
        volume_change = diff(ticks[0].volume, ticks[1].volume)

    return {
        "error": None,
        "result": {
            "price": amnt(ticks[0].price),
            "marketcap": amnt(ticks[0].cap),
            "volume": amnt(ticks[0].volume),
            "change": {
                "price": amnt(price_change),
                "marketcap": amnt(cap_change),
                "volume": amnt(volume_change),
            }
        }
    }
