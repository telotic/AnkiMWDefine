import re

from aqt import gui_hooks, mw
from aqt.editor import Editor

from .mw_types import Entry
from .utils import query_mw_api, is_head_word, extract_audio_links


def get_definition(editor: Editor):
    """Get definition and add to editor"""
    word = editor.note.fields[0]
    word = re.sub(r"\[.*?\]", "", word).strip()

    config = mw.addonManager.getConfig(__name__)
    api_key = config["api_key"]
    mw_result = query_mw_api(word, api_key)

    # NOTE: we only care about the headword entries
    hw_entries = list(filter(lambda x: is_head_word(word, x), mw_result))
    definition_text = "<br><br>".join([str(Entry(entry)) for entry in hw_entries])

    audio_links = []
    for entry in hw_entries:
        audio_links.extend(extract_audio_links(entry))
    audio_links = list(dict.fromkeys(audio_links))

    audio_files = [editor.urlToLink(url) for url in audio_links]
    if len(audio_files) > 0:
        editor.note.fields[0] = word + " " + "".join(audio_files)

    editor.note.fields[1] = definition_text
    editor.loadNote()
    # editor.saveNow()


def register_button(buttons: list[str], editor: Editor):
    """Register the lookup button"""
    lookup_button = editor.addButton(icon="", cmd="", func=get_definition)

    buttons.append(lookup_button)
    return buttons


gui_hooks.editor_did_init_buttons.append(register_button)
