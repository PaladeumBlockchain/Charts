from ..models import TransactionTick
from ..services import BlockService
from ..models import AddressTick
from ..models import TokenTick
from datetime import datetime
from service import constants
from ..models import Stats
from pony import orm
from .. import utils


def log_block(message, block, tx=[]):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    time = block.created.strftime("%Y-%m-%d %H:%M:%S")
    print(
        f"{now} {message}: hash={block.blockhash} height={block.height} tx={block.transactions} addr={block.addresses} tkn={block.tokens} date='{time}'"
    )


def log_message(message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{now} {message}")


def get_current_height():
    return utils.make_request("getblockcount")["result"]


def get_height(height: int):
    return utils.make_request("getblockhash", [height])["result"]


def get_block_hash(height: int):
    return utils.make_request("getblockhash", [height])["result"]


def get_block(blockhash: str):
    return utils.make_request("getblock", [blockhash])["result"]


def get_transaction(txid: str):
    data = utils.make_request("getrawtransaction", [txid, True])

    for index, vin in enumerate(data["result"]["vin"]):
        if "txid" in vin:
            vin_data = utils.make_request(
                "getrawtransaction", [vin["txid"], True]
            )
            if vin_data["error"] is None:
                data["result"]["vin"][index]["scriptPubKey"] = vin_data[
                    "result"
                ]["vout"][vin["vout"]]["scriptPubKey"]

    return data["result"]


@orm.db_session
def sync_chain():
    if not BlockService.latest_block():
        data = get_block(get_height(0))

        created = datetime.fromtimestamp(data["time"])

        block = BlockService.create(data["hash"], data["height"], created)

        log_block("Genesis block", block)

        orm.commit()

    current_height = get_current_height()
    latest_block = BlockService.latest_block()

    log_message(
        f"Current node height: {current_height}, db height: {latest_block.height}"
    )

    # Get stats object
    if not (stats := Stats.select().for_update().first()):
        stats = Stats()

    while latest_block.blockhash != get_block_hash(latest_block.height):
        log_block("Found reorg", latest_block)

        reorg_block = latest_block
        latest_block = reorg_block.previous_block

        stats.transactions -= reorg_block.transactions
        stats.addresses -= reorg_block.addresses
        stats.tokens -= reorg_block.tokens

        for interval in constants.INTERVALS:
            if constants.INTERVALS[interval] == constants.Interval.DAY:
                timestamp = utils.round_day(block.created)

            elif constants.INTERVALS[interval] == constants.Interval.WEEK:
                timestamp = utils.round_week(block.created)

            elif constants.INTERVALS[interval] == constants.Interval.MONTH:
                timestamp = utils.round_month(block.created)

            else:
                timestamp = utils.round_year(block.created)

            if token_tick := TokenTick.get_for_update(
                timestamp=timestamp, interval=constants.INTERVALS[interval]
            ):
                token_tick.value -= reorg_block.tokens

                if token_tick.value <= 0:
                    token_tick.delete()

            if address_tick := AddressTick.get_for_update(
                timestamp=timestamp, interval=constants.INTERVALS[interval]
            ):
                address_tick.value -= reorg_block.addresses

                if address_tick.value <= 0:
                    address_tick.delete()

            for currency in block.currency_transactions:
                if transaction_tick := TransactionTick.get_for_update(
                    timestamp=timestamp,
                    interval=constants.INTERVALS[interval],
                    currency=currency,
                ):
                    transaction_tick.value -= currency.transactions

                    if transaction_tick.value <= 0:
                        transaction_tick.delete()

                currency.delete()

        reorg_block.delete()
        orm.commit()

    for height in range(latest_block.height + 1, current_height + 1):
        block_data = get_block(get_height(height))
        created = datetime.fromtimestamp(block_data["time"])
        stake = block_data["flags"] == "proof-of-stake"

        block = BlockService.create(
            block_data["hash"], block_data["height"], created
        )

        block.previous_block = latest_block

        currency_transactions = {"PLB": 0}
        addresses = 0
        tokens = 0

        for index, txid in enumerate(block_data["tx"]):
            if stake and index <= 1:
                continue

            tx = get_transaction(txid)

            for vin in tx["vin"]:
                if "scriptPubKey" in vin:
                    addresses += len(vin["scriptPubKey"]["addresses"])

            for vout in tx["vout"]:
                if "scriptPubKey" in vout and "token" in vout["scriptPubKey"]:
                    currency = vout["scriptPubKey"]["token"]["name"]

                    if "!" not in currency:
                        if vout["scriptPubKey"]["type"] == "new_token":
                            tokens += 1

                        if currency not in currency_transactions:
                            currency_transactions[currency] = 0

                        currency_transactions[currency] += 1

            currency_transactions["PLB"] += 1

        block.transactions += currency_transactions["PLB"]
        block.addresses += addresses
        block.tokens += tokens

        stats.transactions += currency_transactions["PLB"]
        stats.addresses += addresses
        stats.tokens += tokens

        # Make ticks for day, month and year
        for interval in constants.INTERVALS:
            if constants.INTERVALS[interval] == constants.Interval.DAY:
                timestamp = utils.round_day(block.created)

            elif constants.INTERVALS[interval] == constants.Interval.WEEK:
                timestamp = utils.round_week(block.created)

            elif constants.INTERVALS[interval] == constants.Interval.MONTH:
                timestamp = utils.round_month(block.created)

            else:
                timestamp = utils.round_year(block.created)

            # Generate tokens tick
            if not (
                token_tick := TokenTick.get_for_update(
                    timestamp=timestamp, interval=constants.INTERVALS[interval]
                )
            ):
                token_tick = TokenTick(
                    timestamp=timestamp, interval=constants.INTERVALS[interval]
                )

            token_tick.value += tokens

            # Generate address tick
            if not (
                address_tick := AddressTick.get_for_update(
                    timestamp=timestamp, interval=constants.INTERVALS[interval]
                )
            ):
                address_tick = AddressTick(
                    timestamp=timestamp, interval=constants.INTERVALS[interval]
                )

            address_tick.value += addresses

            # Generate transaction tick for each currency involved
            for currency in currency_transactions:
                if not (
                    transaction_tick := TransactionTick.get_for_update(
                        timestamp=timestamp,
                        interval=constants.INTERVALS[interval],
                        currency=currency,
                    )
                ):
                    transaction_tick = TransactionTick(
                        timestamp=timestamp,
                        interval=constants.INTERVALS[interval],
                        currency=currency,
                    )

                transaction_tick.value += currency_transactions[currency]

        latest_block = block

        log_block("New block", block, block_data["tx"])

        if block.height % 1000 == 0:
            orm.commit()
