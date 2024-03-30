from webargs import fields, validate
from .. import constants

filter_args = {
    "resolution": fields.Str(
        missing="1D", validate=lambda r: r in constants.INTERVALS
    ),
    "after": fields.Int(missing=None, validate=lambda v: v > 0),
}

transactions_args = filter_args
transactions_args["currency"] = fields.Str(missing="PLB")
