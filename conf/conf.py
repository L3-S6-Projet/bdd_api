import json
from datetime import time


def __load() -> dict:
    with open('conf.json') as f:
        return json.load(f)


def timings() -> dict:
    return __load()['timings']


def start_time() -> time:
    data = timings()['start']
    return time(hour=data['hour'], minute=data['minute'], second=0)


def end_time() -> time:
    data = timings()['end']
    return time(hour=data['hour'], minute=data['minute'], second=0)
