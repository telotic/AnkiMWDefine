from typing import List, Dict, Optional, Tuple
import click
import re


# process running text
# https://dictionaryapi.com/products/json#sec-2.tokens
# https://dictionaryapi.com/products/json#sec-2.xrefregtokens
class RunningText:
    def __init__(self, text):
        self.text = text

    def __str__(self):
        # TODO: very incomplete support and expensive implementation
        text = self.text.replace("{bc}", ": ")

        text = re.sub(r"{sx\|([^\|]+)\|[^\|]*\|[^}]*}", r"\1", text)
        text = re.sub(r"{dxt\|([\w ]+)(:\d+)?\|[^}]*}", r"\1", text)
        text = re.sub(r"{a_link\|([\w ]+)}", r"\1", text)
        text = re.sub(r"{d_link\|([\w ]+)\|[^}]*}", r"\1", text)

        text = re.sub(r"{dx_def}(.*){\/dx_def}", r"(\1)", text)

        # remove all other tags
        text = re.sub(r"{\/?\w+}", "", text)
        return text


# Attribution of Quote: aq
# https://dictionaryapi.com/products/json#sec-2.aq
class AuthorQuotation:
    def __init__(self, data: Tuple[str, Dict]):
        assert data[0] == "aq", "Not an aq node!"

        self.auth: Optional[str] = None
        self.source: Optional[str] = None
        self.aqdate: Optional[str] = None
        # TODO: self.subsource: Optional[]

        for (k, v) in data[1].items():
            if k == "auth":
                self.auth = v
            elif k == "source":
                self.source = v
            elif k == "aqdata":
                self.aqdata = v
            # TODO: elif k == "subsource"

    def __str__(self):
        # TODO: what if ends up being None?
        l = list(filter(lambda x: x is not None, [self.auth, self.source, self.aqdate]))
        return " ".join(l)


# Verbal Illustrations: vis
# https://dictionaryapi.com/products/json#sec-2.vis
class VerbalIllustration:
    def __init__(self, data: Dict):
        self.text = RunningText(data["t"])
        self.aq: Optional[AuthorQuotation] = None
        if "aq" in data:
            # TODO: this is weird to form a tuple by hand
            self.aq = AuthorQuotation(("aq", data["aq"]))

    def __str__(self):
        r = click.style("// ", bold=True) + click.style(self.text, italic=True)
        if self.aq is not None:
            return r + " -- " + self.aq.__str__()
        else:
            return r


class VerbalIllustrationSet:
    def __init__(self, data: List):
        assert data[0] == "vis", "Not a vis node!"
        assert len(data) == 2, "Malformed vis node!"
        assert type(data[1]) is list, "Malformed vis node!"

        self.vis: List[VerbalIllustration] = []
        for elm in data[1]:
            self.vis.append(VerbalIllustration(elm))

    def __str__(self):
        return "\n".join([vi.__str__() for vi in self.vis])


# Defining Text: dt
# https://dictionaryapi.com/products/json#sec-2.dt
class DefiningText:
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


# Format SN according to its possible parts
# A sense number sn may contain bold Arabic numerals,
# bold lowercase letters, or parenthesized Arabic numerals.

SN_FORMAT = re.compile(r"^(?P<l1>\d+)? ?(?P<l2>[a-z])? ?(?P<l3>\(\d+\))?$")


class SenseNumber:
    def __init__(self, data: Tuple):
        assert data[0] == "sn", "Not an sn!"

        matches = SN_FORMAT.fullmatch(data[1])
        self.l1 = matches["l1"]
        self.l2 = matches["l2"]
        self.l3 = matches["l3"]
        # TODO: what if there's l4, what if all are None?

    def __str__(self):
        # TODO: improve this
        if self.l3 is not None:
            return (
                f"{self.l1 if self.l1 else ' '} {self.l2 if self.l2 else ' '} {self.l3}"
            )
        elif self.l2 is not None:
            return f"{self.l1 if self.l1 else ' '} {self.l2}"
        else:
            return f"{self.l1}"


# Divided Sense: sdsense
# https://dictionaryapi.com/products/json#sec-2.sdsense
class DividedSense:
    def __init__(self, data: Tuple):
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


# Sense: sense
# https://dictionaryapi.com/products/json#sec-2.sense
# Data Model:
#   object or array consisting of one dt (required) and zero
#   or more et, ins, lbs, prs, sdsense, sgram, sls, sn, or vrs
class Sense:
    # TODO: object or array???
    def __init__(self, data):
        # TODO: how to mandate dt?
        self.sn: Optional[SenseNumber] = None
        self.sdsense: Optional[DividedSense] = None

        if type(data) is dict:
            # TODO: this is weird
            self.dt = DefiningText(("dt", data["dt"]))

            # optional fields
            # TODO: incomplete
            for elm in data.items():
                if elm[0] == "sn":
                    self.sn = SenseNumber(elm)
                if elm[0] == "sdsense":
                    self.sdsense = DividedSense(elm)

        elif type(data) is list:
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


# Etymology: et
# https://dictionaryapi.com/products/json#sec-2.et
class Etymology:
    def __init__(self, data: Tuple):
        assert data[0] == "et", "Not an et node!"
        assert type(data[1]) is List, "Malformed et node!"

        # TODO: how to mandate self.text: str?
        # TODO: et_snote: Optional[str] = None

        for elm in data[1]:
            if elm[0] == "text":
                self.text = RunningText(elm[1])
            # TODO: not sure how et_snote is used
            # elif elm[0] == "et_snote":

    def __str__(self):
        return self.text.__str__()


# Truncated Sense: sen
# https://dictionaryapi.com/products/json#sec-2.sen
class TruncatedSense:
    # TODO: object or array???
    def __init__(self, data):
        self.sn: Optional[SenseNumber] = None
        self.et: Optional[Etymology] = None

        if type(data) is dict:
            # TODO: incomplete
            # at least one of the set et, ins, lbs, prs, sgram, sls, sn, vrs
            for elm in data.items():
                if elm[0] == "sn":
                    self.sn = SenseNumber(elm)
                if elm[0] == "et":
                    self.et = Etymology(elm)
        elif type(data) is list:
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


# Binding Substitute: bs
# https://dictionaryapi.com/products/json#sec-2.bs
class BindingSubstitute:
    def __init__(self, data: List):
        assert data[0] == "bs", "Not a bs node!"
        assert len(data) == 2, "Malformed bs node!"
        assert type(data[1]) is dict, "Malformed bs node!"

        self.sense = Sense(data[1]["sense"])

    def __str__(self):
        # TODO: bs should have effect on subsequent senses, which is
        #       not yet represented here
        return self.sense.__str__()


# Parenthesized Sense Sequence: pseq
# https://dictionaryapi.com/products/json#sec-2.pseq
class ParenthesizedSenseSequence:
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


# Sense Sequence: sseq
# https://dictionaryapi.com/products/json#sec-2.sseq
class SenseSequence:
    def __init__(self, data: Tuple):
        assert data[0] == "sseq", "Not an sseq node!"
        assert type(data[1]) is list, "Malformed sseq node!"

        self.sseq: List[List] = []

        # TODO: the structure of sseq is unclear
        for seq in data[1]:
            r = []
            for elm in seq:
                if elm[0] == "sense":
                    r.append(Sense(elm[1]))
                elif elm[0] == "sen":
                    r.append(TruncatedSense(elm[1]))
                elif elm[0] == "pseq":
                    r.append(ParenthesizedSenseSequence(elm[1]))
                elif elm[0] == "bs":
                    r.append(BindingSubstitute(elm))
                # TODO: elif sdsense ...
            self.sseq.append(r)

    def __str__(self):
        return "\n".join([elm.__str__() for seq in self.sseq for elm in seq])


# Verb Divider: vd
# https://dictionaryapi.com/products/json#sec-2.vd
class VerbDivider:
    def __init__(self, data):
        assert data[0] == "vd", "Not a vd node!"
        self.vd: str = data[1]

    def __str__(self):
        return click.style(self.vd, fg="blue", italic=True, underline=True)


# Definition Section: def
# https://dictionaryapi.com/products/json#sec-2.def
# https://dictionaryapi.com/products/json#sec-2.sense-struct
class DefinitionSection:
    def __init__(self, data: List):
        # The definition section groups together all the sense sequences
        # and verb dividers for a headword or defined run-on phrase.
        self.children = []

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
    def __init__(self, data: Dict):
        self.functional_label = data["fl"]
        self.definition = DefinitionSection(data["def"])

    def __str__(self):
        return (
            click.style(self.functional_label, fg="green", bold=True)
            + "\n"
            + self.definition.__str__()
        )
