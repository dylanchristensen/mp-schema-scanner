"""
Minimal Monterey Phoenix schema parser for INSuRE+C signal work.

Targets the subset of MP we use:
  ROOT Name : ( state1 | state2 | ... );
  state : event1 event2 [optional_event] ... ;
  ENSURE FOREACH $a: event_A, $b: event_B ($a BEFORE $b);
  IF #X1 op1 N1 AND #X2 op2 N2 ... THEN REJECT; FI;

Output is a structured Schema object with:
  roots:        dict[root_name -> list of state names]
  state_root:   dict[state_name -> root_name]
  consequents:  dict[state_name -> list of (event_name, is_optional)]
  event_to_state: dict[event_name -> state_name that emits it]
  orderings:    list[(event_a, event_b)]
  rejects:      list of REJECT records (see parse_reject)
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field


@dataclass
class Reject:
    """One REJECT rule, normalized.
    positives: identifiers required to be present (count > 0).
    negatives: identifiers required to be absent (count == 0).
    raw:       original textual rule body for diagnostics.

    A common form is:  one positive antecedent X, several negative
    "disjunct sources" Y_i.  That means: "X requires Y1 OR Y2 OR ...".
    is_single_pos_disjunction() detects this case.
    """
    positives: list[str]
    negatives: list[str]
    raw: str

    def is_single_pos_disjunction(self) -> bool:
        return len(self.positives) == 1 and len(self.negatives) >= 1

    def is_mutex(self) -> bool:
        return len(self.positives) >= 2 and len(self.negatives) == 0

    def is_conditional(self) -> bool:
        return len(self.positives) >= 2 and len(self.negatives) >= 1


@dataclass
class Schema:
    roots: dict = field(default_factory=dict)            # root_name -> [state]
    state_root: dict = field(default_factory=dict)       # state -> root
    consequents: dict = field(default_factory=dict)      # state -> [(event, optional)]
    event_to_state: dict = field(default_factory=dict)   # event -> state
    orderings: list = field(default_factory=list)        # (event_a, event_b)
    rejects: list = field(default_factory=list)          # list[Reject]

    def states_in_same_root(self, state: str) -> list[str]:
        return list(self.roots.get(self.state_root.get(state, ""), []))

    def identifiers(self) -> set[str]:
        """All states + all events. Used to classify REJECT operands."""
        out = set(self.state_root) | set(self.event_to_state)
        return out

    def is_state(self, ident: str) -> bool:
        return ident in self.state_root

    def is_event(self, ident: str) -> bool:
        return ident in self.event_to_state


# Strip /* ... */ comments and // line comments.
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENT = re.compile(r"//[^\n]*")


def _strip_comments(text: str) -> str:
    text = _BLOCK_COMMENT.sub(" ", text)
    text = _LINE_COMMENT.sub(" ", text)
    return text


_ROOT_RE = re.compile(
    r"\bROOT\s+(\w+)\s*:\s*\(\s*([^)]+?)\s*\)\s*;",
    re.DOTALL,
)


def _parse_roots(text: str, schema: Schema) -> None:
    for m in _ROOT_RE.finditer(text):
        root = m.group(1)
        states = [s.strip() for s in m.group(2).split("|")]
        schema.roots[root] = states
        for s in states:
            schema.state_root[s] = root


_REJECT_RE = re.compile(
    r"\bIF\b(.*?)\bTHEN\s+REJECT\s*;\s*FI\s*;",
    re.DOTALL,
)


def _parse_reject_body(body: str) -> Reject:
    """Parse 'IF ... THEN REJECT; FI;' body into a Reject record.

    Expected operand syntax: #identifier (> 0 | == 0 | > N | == N).
    Multiple clauses joined by AND.
    """
    body = body.strip()
    clauses = re.split(r"\bAND\b", body)
    positives, negatives = [], []
    for c in clauses:
        c = c.strip()
        if not c:
            continue
        m = re.match(r"#\s*(\w+)\s*(==|>=|<=|>|<|!=)\s*(\d+)", c)
        if not m:
            continue
        ident, op, n = m.group(1), m.group(2), int(m.group(3))
        if op == ">" and n == 0:
            positives.append(ident)
        elif op == "==" and n == 0:
            negatives.append(ident)
        elif op == ">=" and n >= 1:
            positives.append(ident)
        else:
            # other shapes not used in our schemas
            pass
    return Reject(positives=positives, negatives=negatives, raw=body)


def _parse_rejects(text: str, schema: Schema) -> None:
    for m in _REJECT_RE.finditer(text):
        schema.rejects.append(_parse_reject_body(m.group(1)))


_ORDER_RE = re.compile(
    r"\bENSURE\s+FOREACH\s+\$\w+\s*:\s*(\w+)\s*,"
    r"\s*\$\w+\s*:\s*(\w+)\s*\(\s*\$\w+\s+BEFORE\s+\$\w+\s*\)\s*;",
    re.DOTALL,
)


def _parse_orderings(text: str, schema: Schema) -> None:
    for m in _ORDER_RE.finditer(text):
        schema.orderings.append((m.group(1), m.group(2)))


_CONSEQ_RE = re.compile(
    r"^\s*(\w+)\s*:\s*([^;]*);",
    re.MULTILINE,
)


def _parse_consequents(text: str, schema: Schema) -> None:
    """Parse 'state : event1 event2 [optional_event];' lines.

    Skips lines that are actually ROOT declarations (which contain '|').
    """
    for m in _CONSEQ_RE.finditer(text):
        name = m.group(1).strip()
        body = m.group(2).strip()
        if name not in schema.state_root:
            continue  # not a known ROOT state
        if "|" in body or "(" in body:
            continue  # this is the ROOT line itself
        events = []
        # Tokenize: words, optionally bracketed [word]
        for tok in re.findall(r"\[\s*(\w+)\s*\]|(\w+)", body):
            opt_name, req_name = tok
            if opt_name:
                events.append((opt_name, True))
            elif req_name:
                events.append((req_name, False))
        schema.consequents[name] = events
        for ev, _ in events:
            schema.event_to_state[ev] = name


def parse_schema(path: str) -> Schema:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    text = _strip_comments(text)
    schema = Schema()
    _parse_roots(text, schema)
    _parse_rejects(text, schema)
    _parse_orderings(text, schema)
    _parse_consequents(text, schema)
    return schema


def summarize(schema: Schema) -> None:
    print(f"ROOTs:      {len(schema.roots)}")
    for r, ss in schema.roots.items():
        print(f"  {r}: {ss}")
    print(f"States:     {len(schema.state_root)}")
    print(f"Events:     {len(schema.event_to_state)}")
    print(f"Orderings:  {len(schema.orderings)}")
    for a, b in schema.orderings:
        print(f"  {a} BEFORE {b}")
    print(f"REJECTs:    {len(schema.rejects)}")
    for r in schema.rejects:
        pos = ", ".join(f"#{p}>0" for p in r.positives)
        neg = ", ".join(f"#{n}==0" for n in r.negatives)
        kind = ("single-pos-disj" if r.is_single_pos_disjunction()
                else "mutex" if r.is_mutex()
                else "conditional" if r.is_conditional()
                else "other")
        print(f"  [{kind}] {pos}  AND  {neg}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("usage: python schema_parser.py path/to/schema.mp")
        sys.exit(1)
    summarize(parse_schema(sys.argv[1]))
