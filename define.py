"""Print the definitions of a word by requesting Merriam-Webster dictionary API"""

import json
import click

from mw_types import Entry
from utils import query_mw_api, is_head_word, extract_audio_links


@click.command()
@click.argument("word")
def define(word: str) -> None:
    """Print the definitions for the given word"""
    with open("config.json", encoding="UTF-8") as config:
        api_key = json.load(config)["api_key"]
    mw_result = query_mw_api(word, api_key)
    click.echo("")

    # NOTE: we only care about the headword entries
    hw_entries = filter(lambda x: is_head_word(word, x), mw_result)
    for entry in hw_entries:
        audio_links = extract_audio_links(entry)
        if len(audio_links) > 0:
            click.echo("\n".join(audio_links))
            click.echo("")
        click.echo(Entry(entry))
    click.echo("")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    define()
