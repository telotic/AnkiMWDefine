from typing import List, Optional

import os.path
import urllib.request
import json
import click
import re

API_FORMAT = (
    "https://dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={api_key}"
)

SN_FORMAT = re.compile(r"^(?P<l1>\d+)? ?(?P<l2>[a-z])? ?(?P<l3>\(\d+\))?$")


# TODO: can avoid passsing in word
def visit_entry(entry, word):
    # https://dictionaryapi.com/products/json#sec-2.meta
    # NOTE: we only care about the headword entries
    # TODO: probably should use the hom or hwi field?
    entry_id = entry["meta"]["id"]
    if re.fullmatch(word + r"(:\d+)?", entry_id) is None:
        return

    functional_label = entry["fl"]
    click.secho(functional_label, fg="green", bold=True)

    # if 'shortdef' in entry:
    #     visit_shortdef(entry["shortdef"])

    visit_def(entry["def"])
    click.echo("")


def visit_shortdef(shortdefs: List):
    for shortdef in shortdefs:
        print(shortdef)


# Definition Section: def
# https://dictionaryapi.com/products/json#sec-2.def
# https://dictionaryapi.com/products/json#sec-2.sense-struct
def visit_def(definitions: List):
    for definition in definitions:
        # Verb Divider: vd
        # https://dictionaryapi.com/products/json#sec-2.vd
        if "vd" in definition:
            click.secho(definition["vd"], fg="blue", italic=True, underline=True)

        # "sls" isn't very interesting
        # https://dictionaryapi.com/products/json#sec-2.sls

        if "sseq" in definition:
            visit_sseq(definition["sseq"])


# Sense Sequence: sseq
# https://dictionaryapi.com/products/json#sec-2.sseq
def visit_sseq(sseq: List):
    for sequence in sseq:
        for entry in sequence:
            key = entry[0]
            value = entry[1]
            if key == "sense":
                visit_sense(value)
            elif key == "sen":
                visit_sen(value)
            elif key == "pseq":
                visit_pseq(value)
            elif key == "bs":
                visit_bs(value)
            # TODO: sdsense


# Sense: sense
# https://dictionaryapi.com/products/json#sec-2.sense
# Data Model:
#   object or array consisting of one dt (required) and zero
#   or more et, ins, lbs, prs, sdsense, sgram, sls, sn, or vrs
def visit_sense(sense):
    sense_number = print_sn(sense["sn"]) if "sn" in sense else None
    defining_text = visit_dt(sense["dt"])

    if "sdsense" in sense:
        defining_text += "\n"
        defining_text += visit_sdsense(sense["sdsense"])

    if sense_number is not None:
        # TODO: this is too hacky
        indent = "\n" + " " * (len(sense_number) + 1)
        defining_text = re.sub(r"\n *", indent, defining_text)
        click.echo(click.style(sense_number, fg="red", bold=True) + " " + defining_text)
    else:
        click.echo(defining_text)


# Truncated Sense: sen
# https://dictionaryapi.com/products/json#sec-2.sen
def visit_sen(sen):
    sense_number = print_sn(sen["sn"]) if "sn" in sen else None
    if "et" in sen:
        text = "[ " + visit_et(sen["et"]) + " ]"
        if sense_number is not None:
            click.echo(click.style(sense_number, fg="red", bold=True) + " " + text)
        else:
            click.echo(text)


# Divided Sense: sdsense
# https://dictionaryapi.com/products/json#sec-2.sdsense
def visit_sdsense(sdsense) -> str:
    sense_divider = sdsense["sd"]
    # TODO: et, ins, lbs, prs, sgram, sls, vrs
    defining_text = visit_dt(sdsense["dt"])
    return click.style(sense_divider, italic=True) + defining_text


# Format SN according to its possible parts
# A sense number sn may contain bold Arabic numerals,
# bold lowercase letters, or parenthesized Arabic numerals.
def print_sn(sn: str) -> str:
    matches = SN_FORMAT.fullmatch(sn)
    l1 = matches["l1"]
    l2 = matches["l2"]
    l3 = matches["l3"]
    if l3 is not None:
        return f"{l1 if l1 else ' '} {l2 if l2 else ' '} {l3}"
    elif l2 is not None:
        return f"{l1 if l1 else ' '} {l2}"
    else:
        return f"{l1}"


# Parenthesized Sense Sequence: pseq
# https://dictionaryapi.com/products/json#sec-2.pseq
def visit_pseq(pseq):
    for entry in pseq:
        key = entry[0]
        value = entry[1]
        if key == "bs":
            # bs is optional
            visit_bs(value)
        elif key == "sense":
            visit_sense(value)


# Binding Substitute: bs
# https://dictionaryapi.com/products/json#sec-2.bs
def visit_bs(bs):
    visit_sense(bs["sense"])


# Defining Text: dt
# https://dictionaryapi.com/products/json#sec-2.dt
def visit_dt(dt: List) -> str:
    content = None
    vis = []
    for entry in dt:
        key = entry[0]
        value = entry[1]
        if key == "text":
            content = value
        elif key == "vis":
            for vis_field in value:
                vis.append(click.style("// ", bold=True) + visit_vis(vis_field))
    if len(vis) > 0:
        return print_running_text(content + "\n" + "\n".join(vis))
    else:
        return print_running_text(content)


# Etymology: et
# https://dictionaryapi.com/products/json#sec-2.et
def visit_et(et: List) -> str:
    content = None
    for entry in et:
        key = entry[0]
        value = entry[1]
        if key == "text":
            content = value
        # TODO: not sure how et_snote is used
        # elif key == "et_snote":
    return print_running_text(content)


# Verbal Illustrations: vis
# https://dictionaryapi.com/products/json#sec-2.vis
def visit_vis(vis) -> str:
    text = click.style(print_running_text(vis["t"]), italic=True)
    attribution = visit_aq(vis["aq"]) if "aq" in vis else None
    if attribution is not None:
        return f"{text} -- {attribution}"
    return text


# Attribution of Quote: aq
# https://dictionaryapi.com/products/json#sec-2.aq
def visit_aq(aq) -> Optional[str]:
    # TODO: incomplete support
    if "auth" in aq:
        return aq["auth"]
    elif "source" in aq:
        return aq["source"]
    return None


# process running text
# https://dictionaryapi.com/products/json#sec-2.tokens
def print_running_text(text) -> str:
    text = text.replace("{bc}", ": ")

    # TODO: very incomplete support
    # https://dictionaryapi.com/products/json#sec-2.xrefregtokens
    text = re.sub(r"{sx\|([^\|]+)\|[^\|]*\|[^}]*}", r"\1", text)
    text = re.sub(r"{dxt\|([\w ]+)(:\d+)?\|[^}]*}", r"\1", text)
    text = re.sub(r"{a_link\|([\w ]+)}", r"\1", text)
    text = re.sub(r"{d_link\|([\w ]+)\|[^}]*}", r"\1", text)

    text = re.sub(r"{dx_def}(.*){\/dx_def}", r"(\1)", text)

    # remove all other tags
    text = re.sub(r"{\/?\w+}", "", text)
    return text


def query_mw(word: str):
    if not os.path.exists("cache/"):
        os.makedirs("cache/")
    cache_path = f"cache/response_{word}.json"
    if os.path.isfile(cache_path):
        f = open(cache_path)
        return json.load(f)
    else:
        with open("config.json") as config:
            api_key = json.load(config)["api_key"]
        url = API_FORMAT.format(word=word, api_key=api_key)
        f = urllib.request.urlopen(url)
        r = f.read().decode("utf-8")
        with open(f"cache/response_{word}.json", "w") as cache:
            cache.write(r)
        return json.loads(r)


@click.command()
@click.argument("word")
def define(word):
    mw_result = query_mw(word)
    click.echo("")
    for entry in mw_result:
        visit_entry(entry, word)


if __name__ == "__main__":
    define()
