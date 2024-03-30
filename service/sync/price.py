from service.models import PriceTick
from datetime import datetime
from .. import constants
from pony import orm
from .. import utils
import requests

@orm.db_session
def sync_price():
    try:
        result = requests.get(constants.PRICE_ENDPOINT).json()
        market_data = result["market_data"]

        created = datetime.strptime(
            market_data["last_updated"],
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )

        for interval in constants.INTERVALS:
            if constants.INTERVALS[interval] == constants.Interval.DAY:
                timestamp = utils.round_day(created)

            elif constants.INTERVALS[interval] == constants.Interval.WEEK:
                timestamp = utils.round_week(created)
            
            elif constants.INTERVALS[interval] == constants.Interval.MONTH:
                timestamp = utils.round_month(created)

            else:
                timestamp = utils.round_year(created)

            if not (tick := PriceTick.get(
                interval=constants.INTERVALS[interval],
                timestamp=timestamp
            )):
                tick = PriceTick(
                    interval=constants.INTERVALS[interval],
                    timestamp=timestamp
                )

            tick.cap = market_data["fully_diluted_valuation"]["usd"]
            tick.price = market_data["current_price"]["usd"]
            tick.volume = market_data["total_volume"]["usd"]

    except requests.exceptions.RequestException:
        print("Request to CoinGecko API failed")
