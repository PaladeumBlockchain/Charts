from datetime import timedelta
import requests
import config
import json


def round_day(created):
    return created - timedelta(
        days=created.day % 1,
        hours=created.hour,
        minutes=created.minute,
        seconds=created.second,
        microseconds=created.microsecond,
    )


def round_week(created):
    return created - timedelta(
        days=created.weekday(),
        hours=created.hour,
        minutes=created.minute,
        seconds=created.second,
        microseconds=created.microsecond,
    )


def round_month(created):
    return created.replace(day=1) - timedelta(
        hours=created.hour,
        minutes=created.minute,
        seconds=created.second,
        microseconds=created.microsecond,
    )


def round_year(created):
    return created.replace(day=1).replace(month=1) - timedelta(
        hours=created.hour,
        minutes=created.minute,
        seconds=created.second,
        microseconds=created.microsecond,
    )


def dead_response(message="Invalid Request", rid="plb-charts"):
    return {"error": {"code": 404, "message": message}, "id": rid}


def response(result, error=None, rid="plb-charts", pagination=None):
    result = {"error": error, "id": rid, "result": result}

    if pagination:
        result["pagination"] = pagination

    return result


def make_request(method, params=[]):
    headers = {"content-type": "text/plain;"}
    data = json.dumps({"id": "plb-charts", "method": method, "params": params})

    try:
        return requests.post(config.endpoint, headers=headers, data=data).json()
    except Exception:
        return dead_response()
