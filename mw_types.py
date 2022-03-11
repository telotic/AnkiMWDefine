from typing import List, Dict, Optional, Tuple, Any
import re
import click


class RunningText:
    """
    Running text contains marked up components
    https://dictionaryapi.com/products/json#sec-2.tokens
    https://dictionaryapi.com/products/json#sec-2.xrefregtokens
    """

    def __init__(self, text: str):
        self.text: List[Any] = []
        prev_index = 0
        index = 0
        while prev_index < len(text):
            index = text.find("{", prev_index)
            if index != -1:
                if prev_index != index:
                    self.text.append(text[prev_index:index])
                prev_index = index
                index = text.find("}", prev_index)
                if index == -1:
                    raise RuntimeError("Failed to find matching '}' in running text!")
                index += 1
                self.text.append(self.__parse_marked_up(text[prev_index:index]))
                prev_index = index
            else:
                self.text.append(text[prev_index:])
                prev_index = len(text)

    def __parse_marked_up(self, text: str) -> Tuple:
        return tuple(text.lstrip("{").rstrip("}").split("|"))

    def __str__(self):
        result: str = ""
        for elm in self.text:
            if isinstance(elm, str):
                result += elm
            elif elm[0] == "bc":
                result += ": "
            elif elm[0] == "sx":
                result += click.style(elm[1].upper(), fg="blue", underline=True)
            elif elm[0] == "dxt":
                result += elm[1].split(":", maxsplit=1)[0]
            elif elm[0] in ["a_link", "d_link"]:
                result += elm[1]
            elif elm[0] in ["dx_def", "/dx_def"]:
                # only needs the text in between
                continue
            # ignore all other tags
            # TODO: incomplete support
        return result


class AuthorQuotation:
    """
    Attribution of Quote: aq
    https://dictionaryapi.com/products/json#sec-2.aq
    """

    def __init__(self, data: Tuple[str, Dict]):
        assert data[0] == "aq", "Not an aq node!"

        self.auth: Optional[str] = None
        self.source: Optional[str] = None
        self.aqdate: Optional[str] = None
        # TODO: self.subsource: Optional[]

        for (key, value) in data[1].items():
            if key == "auth":
                self.auth = value
            elif key == "source":
                self.source = value
            elif key == "aqdate":
                self.aqdate = value
            # TODO: elif k == "subsource"

    def __str__(self):
        # TODO: what if ends up being None?
        parts = list(
            filter(lambda x: x is not None, [self.auth, self.source, self.aqdate])
        )
        return " ".join(parts)


class VerbalIllustration:
    """A single verbal illustration"""

    def __init__(self, data: Dict):
        self.text = RunningText(data["t"])
        self.aq: Optional[AuthorQuotation] = None
        if "aq" in data:
            # TODO: this is weird to form a tuple by hand
            self.aq = AuthorQuotation(("aq", data["aq"]))

    def __str__(self):
        line = click.style("// ", bold=True, fg="blue") + click.style(
            self.text, italic=True, fg="blue"
        )
        if self.aq is not None:
            return line + click.style(" -- " + self.aq.__str__(), fg="magenta")
        return line


class VerbalIllustrationSet:
    """
    Verbal Illustrations: vis
    https://dictionaryapi.com/products/json#sec-2.vis
    """

    def __init__(self, data: List):
        assert data[0] == "vis", "Not a vis node!"
        assert len(data) == 2, "Malformed vis node!"
        assert isinstance(data[1], list), "Malformed vis node!"

        self.vis: List[VerbalIllustration] = []
        for elm in data[1]:
            self.vis.append(VerbalIllustration(elm))

    def __str__(self):
        return "\n".join([vi.__str__() for vi in self.vis])


class DefiningText:
    """
    Defining Text: dt
    https://dictionaryapi.com/products/json#sec-2.dt
    """

    def __init__(self, data: Tuple[str, List]):
        assert data[0] == "dt", "Not a dt node!"

        # TODO: how to mandate self.text: str?
        self.vis: Optional[VerbalIllustrationSet] = None

        for elm in data[1]:
            if elm[0] == "text":
                self.text = RunningText(elm[1])
            elif elm[0] == "vis":
                self.vis = VerbalIllustrationSet(elm)
            # TODO: optional bnw, ca, ri, snote, uns, or vis elements

    def __str__(self):
        if self.vis is not None:
            return self.text.__str__() + "\n" + self.vis.__str__()
        else:
            return self.text.__str__()


class SenseNumber:
    """
    Sense Number: sn
    https://dictionaryapi.com/products/json#sec-2.sn
    Example: 2 a (3)
    """

    SN_FORMAT = re.compile(r"^(?P<l1>\d+)? ?(?P<l2>[a-z])? ?(?P<l3>\(\d+\))?$")

    def __init__(self, data: Tuple[str, str]):
        assert data[0] == "sn", "Not an sn!"

        matches = self.SN_FORMAT.fullmatch(data[1])
        l1: Optional[str] = matches["l1"] if matches is not None else None
        l2: Optional[str] = matches["l2"] if matches is not None else None
        l3: Optional[str] = matches["l3"] if matches is not None else None
        self.sense_number = (l1, l2, l3)
        # TODO: what if there's l4, what if all are None?

    def __str__(self):
        # TODO: improve this
        (l1, l2, l3) = self.sense_number
        if l3 is not None:
            return f"{l1 if l1 else ' '} {l2 if l2 else ' '} {l3}"
        if l2 is not None:
            return f"{l1 if l1 else ' '} {l2}"
        return l1


class DividedSense:
    """
    Divided Sense: sdsense
    https://dictionaryapi.com/products/json#sec-2.sdsense
    """

    def __init__(self, data: Tuple[str, Dict]):
        assert data[0] == "sdsense", "Not an sdsense node!"

        self.sense_divider = data[1]["sd"]
        # TODO: this is weird
        self.definition_text = DefiningText(("dt", data[1]["dt"]))
        # TODO: et, ins, lbs, prs, sgram, sls, vrs

    def __str__(self):
        return (
            click.style(self.sense_divider, italic=True)
            + self.definition_text.__str__()
        )


class Sense:
    """
    Sense: sense
    https://dictionaryapi.com/products/json#sec-2.sense
    Data Model:
        object or array consisting of one dt (required) and zero
        or more et, ins, lbs, prs, sdsense, sgram, sls, sn, or vrs
    """

    # TODO: object or array???
    def __init__(self, data: Any):
        # TODO: how to mandate dt?
        self.sn: Optional[SenseNumber] = None
        self.sdsense: Optional[DividedSense] = None

        if isinstance(data, dict):
            # TODO: this is weird
            self.dt = DefiningText(("dt", data["dt"]))

            # optional fields
            # TODO: incomplete
            for elm in data.items():
                if elm[0] == "sn":
                    self.sn = SenseNumber(elm)
                if elm[0] == "sdsense":
                    self.sdsense = DividedSense(elm)
        elif isinstance(data, list):
            raise RuntimeError("Not implemented!")

    def __str__(self):
        definition = self.dt.__str__()
        if self.sdsense is not None:
            definition += "\n" + self.sdsense.__str__()

        if self.sn is not None:
            # TODO: this is too hacky
            indent = "\n" + " " * (len(self.sn.__str__()) + 1)
            definition = re.sub(r"\n *", indent, definition)

            return click.style(self.sn, fg="red", bold=True) + " " + definition
        else:
            return definition


class Etymology:
    """
    Etymology: et
    https://dictionaryapi.com/products/json#sec-2.et
    """

    def __init__(self, data: Tuple[str, List]):
        assert data[0] == "et", "Not an et node!"
        assert isinstance(data[1], list), "Malformed et node!"

        # TODO: how to mandate self.text: str?
        # TODO: et_snote: Optional[str] = None

        for elm in data[1]:
            if elm[0] == "text":
                self.text = RunningText(elm[1])
            # TODO: not sure how et_snote is used
            # elif elm[0] == "et_snote":

    def __str__(self):
        return self.text.__str__()


class TruncatedSense:
    """
    Truncated Sense: sen
    https://dictionaryapi.com/products/json#sec-2.sen
    """

    # TODO: object or array???
    def __init__(self, data: Any):
        self.sn: Optional[SenseNumber] = None
        self.et: Optional[Etymology] = None

        if isinstance(data, dict):
            # TODO: incomplete
            # at least one of the set et, ins, lbs, prs, sgram, sls, sn, vrs
            for elm in data.items():
                if elm[0] == "sn":
                    self.sn = SenseNumber(elm)
                if elm[0] == "et":
                    self.et = Etymology(elm)
        elif isinstance(data, list):
            raise RuntimeError("Not implemented!")

    def __str__(self):
        if self.et is not None:
            text = "[ " + self.sn.__str__() + " ]"
            if self.sn is not None:
                return click.style(self.sn, fg="red", bold=True) + " " + text
            else:
                return text
        else:
            raise RuntimeError("Not implemented!")


class BindingSubstitute:
    """
    Binding Substitute: bs
    https://dictionaryapi.com/products/json#sec-2.bs
    """

    def __init__(self, data: List):
        assert data[0] == "bs", "Not a bs node!"
        assert len(data) == 2, "Malformed bs node!"
        assert isinstance(data[1], dict), "Malformed bs node!"

        self.sense = Sense(data[1]["sense"])

    def __str__(self):
        # TODO: bs should have effect on subsequent senses, which is
        #       not yet represented here
        return self.sense.__str__()


class ParenthesizedSenseSequence:
    """
    Parenthesized Sense Sequence: pseq
    https://dictionaryapi.com/products/json#sec-2.pseq
    """

    def __init__(self, data: List):
        # NOTE: one or more sense elements and an optional bs element
        self.children: List = []

        for elm in data:
            if elm[0] == "bs":
                self.children.append(BindingSubstitute(elm))
            elif elm[0] == "sense":
                self.children.append(Sense(elm[1]))

    def __str__(self):
        return "\n".join([elm.__str__() for elm in self.children])


class SenseSequence:
    """
    Sense Sequence: sseq
    https://dictionaryapi.com/products/json#sec-2.sseq
    """

    def __init__(self, data: Tuple[str, List]):
        assert data[0] == "sseq", "Not an sseq node!"
        assert isinstance(data[1], list), "Malformed sseq node!"

        self.sseq: List[List[Any]] = []

        # TODO: the structure of sseq is unclear
        for seq in data[1]:
            senses: List[Any] = []
            for elm in seq:
                if elm[0] == "sense":
                    senses.append(Sense(elm[1]))
                elif elm[0] == "sen":
                    senses.append(TruncatedSense(elm[1]))
                elif elm[0] == "pseq":
                    senses.append(ParenthesizedSenseSequence(elm[1]))
                elif elm[0] == "bs":
                    senses.append(BindingSubstitute(elm))
                # TODO: elif sdsense ...
            self.sseq.append(senses)

    def __str__(self):
        return "\n".join([elm.__str__() for seq in self.sseq for elm in seq])


class VerbDivider:
    """
    Verb Divider: vd
    https://dictionaryapi.com/products/json#sec-2.vd
    """

    def __init__(self, data: Tuple[str, str]):
        assert data[0] == "vd", "Not a vd node!"
        self.vd: str = data[1]

    def __str__(self):
        return click.style(self.vd, fg="blue", italic=True, underline=True)


class DefinitionSection:
    """
    Definition Section: def
    https://dictionaryapi.com/products/json#sec-2.def
    https://dictionaryapi.com/products/json#sec-2.sense-struct
    """

    def __init__(self, data: List[Any]):
        # The definition section groups together all the sense sequences
        # and verb dividers for a headword or defined run-on phrase.
        self.children: List[Any] = []

        for definition in data:
            for elm in definition.items():
                if elm[0] == "vd":
                    self.children.append(VerbDivider(elm))
                elif elm[0] == "sseq":
                    self.children.append(SenseSequence(elm))
                # "sls" isn't very interesting
                # https://dictionaryapi.com/products/json#sec-2.sls

    def __str__(self):
        return "\n".join([elm.__str__() for elm in self.children])


# TODO: an entry is very complex, here we only look at the interesting part
class Entry:
    """An entry in the MW dict API JSON response"""

    def __init__(self, data: Dict[str, Any]):
        self.functional_label = data["fl"]
        self.definition = DefinitionSection(data["def"])

    def __str__(self):
        return (
            click.style(self.functional_label, fg="green", bold=True)
            + "\n"
            + self.definition.__str__()
        )
