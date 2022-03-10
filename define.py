from typing import List, Optional

import os.path
import requests
import json
import click
import re
from mw_types import Entry


def query_mw(word: str):
    CACHE_DIR = "cache"
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    cache_path = f"{CACHE_DIR}/response_{word}.json"
    if os.path.isfile(cache_path):
        f = open(cache_path)
        return json.load(f)
    else:
        with open("config.json") as config:
            api_key = json.load(config)["api_key"]
        r = requests.get(
            f"https://dictionaryapi.com/api/v3/references/collegiate/json/{word}",
            params={"key": api_key},
        )
        with open(cache_path, "w") as cache:
            cache.write(r.text)
        return r.json()


@click.command()
@click.argument("word")
def define(word):
    mw_result = query_mw(word)
    click.echo("")
    for entry in mw_result:
        # https://dictionaryapi.com/products/json#sec-2.meta
        # NOTE: we only care about the headword entries
        # TODO: probably should use the hom or hwi field?
        entry_id = entry["meta"]["id"]
        if re.fullmatch(word + r"(:\d+)?", entry_id) is not None:
            click.echo(Entry(entry))
    click.echo("")


if __name__ == "__main__":
    define()
