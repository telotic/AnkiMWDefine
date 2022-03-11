from typing import List
import os.path
import re
import json
import requests
import click

from mw_types import Entry


CACHE_DIR = "./cache"


def query_mw(word: str) -> List:
    """Query Merriam-Webster dictionary API for the word for its definitions"""

    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    cache_path = f"{CACHE_DIR}/response_{word}.json"

    if os.path.isfile(cache_path):
        with open(cache_path, encoding="UTF-8") as cached_response:
            return json.load(cached_response)

    with open("config.json", encoding="UTF-8") as config:
        api_key = json.load(config)["api_key"]
    response = requests.get(
        f"https://dictionaryapi.com/api/v3/references/collegiate/json/{word}",
        params={"key": api_key},
    )
    with open(cache_path, mode="w", encoding="UTF-8") as cache:
        cache.write(response.text)
    return response.json()


@click.command()
@click.argument("word")
def define(word: str) -> None:
    """Print the definitions for the given word"""

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
