"""Utility methods"""

from typing import List
import re
import requests


def query_mw_api(word: str, api_key: str):
    """Querying Merriam-Webster dictionary API for word, using api_key"""
    response = requests.get(
        f"https://dictionaryapi.com/api/v3/references/collegiate/json/{word}",
        params={"key": api_key},
        timeout=10
    )
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
