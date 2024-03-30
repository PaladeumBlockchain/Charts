from .args import filter_args, transactions_args
from webargs.flaskparser import use_args
from ..models import TransactionTick
from ..models import AddressTick
from ..models import PriceTick
from ..models import TokenTick
from datetime import datetime
from flask import Blueprint
from ..models import Stats
from .. import constants
from pony import orm

blueprint = Blueprint("charts", __name__)

def get_ticks(model, resolution, after, currency=None):
    limit = constants.INTERVALS_LIMIT[resolution]
    interval = constants.INTERVALS[resolution]

    ticks = model.select(
        lambda t: t.interval == interval
    ).order_by(
        lambda t: orm.desc(t.timestamp)
    )

    if after:
        ticks = ticks.filter(
            lambda t: t.timestamp < datetime.fromtimestamp(after)
        )

    if currency:
        ticks = ticks.filter(
            lambda t: t.currency == currency
        )

    return ticks.limit(limit)

@blueprint.route("/chart/price", methods=["GET"])
@use_args(filter_args, location="query")
@orm.db_session
def price_chart(args):
    result = []

    for tick in get_ticks(PriceTick, args["resolution"], args["after"]):
        result.append({
            "timestamp": int(tick.timestamp.timestamp()),
            "value": round(tick.price, 4),
        })

    return {
        "error": None, "result": result
    }

@blueprint.route("/chart/transactions", methods=["GET"])
@use_args(transactions_args, location="query")
@orm.db_session
def transactions_chart(args):
    result = []

    for tick in get_ticks(
        TransactionTick, args["resolution"],
        args["after"], args["currency"]
    ):
        result.append({
            "timestamp": int(tick.timestamp.timestamp()),
            "value": tick.value,
        })

    return {
        "error": None, "result": result
    }


@blueprint.route("/chart/addresses", methods=["GET"])
@use_args(filter_args, location="query")
@orm.db_session
def addresses_chart(args):
    result = []

    for tick in get_ticks(
        AddressTick, args["resolution"], args["after"]
    ):
        result.append({
            "timestamp": int(tick.timestamp.timestamp()),
            "value": tick.value,
        })

    return {
        "error": None, "result": result
    }

@blueprint.route("/chart/tokens", methods=["GET"])
@use_args(filter_args, location="query")
@orm.db_session
def tokens_chart(args):
    result = []

    for tick in get_ticks(
        TokenTick, args["resolution"], args["after"]
    ):
        result.append({
            "timestamp": int(tick.timestamp.timestamp()),
            "value": tick.value,
        })

    return {
        "error": None, "result": result
    }
