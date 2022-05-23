"""Print the definitions of a word by requesting Merriam-Webster dictionary API"""

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


def extract_audio_links(entry) -> List[str]:
    """Extract audio links from an entry"""
    links = []
    if "prs" in entry["hwi"]:
        prons = entry["hwi"]["prs"]
        for pron in prons:
            if "sound" in pron:
                sound = pron["sound"]
                audio = sound["audio"]
                if audio.startswith("bix"):
                    subdirectory = "bix"
                elif audio.startswith("gg"):
                    subdirectory = "gg"
                elif audio[0].isdigit() or audio[0] == "_":
                    subdirectory = "number"
                else:
                    subdirectory = audio[0]
                links.append(
                    "https://media.merriam-webster.com/"
                    f"audio/prons/en/us/wav/{subdirectory}/{audio}.wav"
                )
    return links


def is_head_word(word: str, entry) -> bool:
    "Return whether this entry is a headword entry for `word`"
    # https://dictionaryapi.com/products/json#sec-2.meta
    # TODO: probably should use the hom or hwi field?
    entry_id = entry["meta"]["id"]
    return re.fullmatch(word + r"(:\d+)?", entry_id) is not None


@click.command()
@click.argument("word")
def define(word: str) -> None:
    """Print the definitions for the given word"""

    mw_result = query_mw(word)
    click.echo("")
    for entry in mw_result:
        # NOTE: we only care about the headword entries
        if is_head_word(word, entry):
            audio_links = extract_audio_links(entry)
            if len(audio_links) > 0:
                for audio_link in audio_links:
                    click.echo(audio_link)
                click.echo("")
            click.echo(Entry(entry))
    click.echo("")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    define()
