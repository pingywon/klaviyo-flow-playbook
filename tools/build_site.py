#!/usr/bin/env python3
"""Build docs/index.html and the README flow tables from the flow files.

    python3 tools/build_site.py           write the page and the README tables
    python3 tools/build_site.py --check   exit 1 if a flow file is invalid or an output is stale
"""
import html
import json
import math
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO_URL = "https://github.com/pingywon/klaviyo-flow-playbook"

UNIT_MINUTES = {"minutes": 1, "hours": 60, "days": 1440}
SPAN = 300 * 1440  # the map's time axis ends at 300 days
EVENT_X = 30  # where a stop sits when its timing depends on an outside event
TICKS = [(0, "Start"), (5, "5 min"), (60, "1 hour"), (1440, "1 day"), (10080, "1 week"),
         (43200, "1 month"), (SPAN, "10 months")]
MINOR_TICKS = ("5 min", "1 month")  # labels dropped on a narrow screen, where they would collide
MOMENTS = [("new-subscriber", "New subscriber", "green"), ("shopping", "While shopping", "blue"),
           ("after-order", "After an order", "amber"), ("gone-quiet", "Gone quiet", "red")]
TIERS = [("next", "Next", "Uses events the store already sends. No new tools."),
         ("then", "Then", "Worth it once there are enough repeat buyers to group."),
         ("later", "Later", "Needs a new channel or Klaviyo's predictions.")]
STATUS = {"running": "Running", "built": "Built, not switched on", "planned": "Planned"}
SENDS = {"email": "Email", "alert": "Internal alert", "text": "Text message", "webhook": "Webhook"}
STEP_FIELDS = {"wait": ("amount", "unit"), "wait-for": ("event", "label"), "email": ("name", "job", "subject"),
               "alert": ("name", "job"), "text": ("name", "job"), "webhook": ("name", "job"),
               "split": ("ask", "yes", "no"), "note": ("text",)}
MAX_PURPOSE_WORDS = 12
MAX_VISIBLE_WORDS = 400


def e(text):
    return html.escape(str(text), quote=True)


def load(folder):
    flows = []
    for path in sorted((ROOT / "flows" / folder).glob("*.json")):
        flow = json.loads(path.read_text(encoding="utf-8"))
        flow["_path"] = path.relative_to(ROOT).as_posix()
        flows.append(flow)
    return flows


def problems(flow, folder):
    out, where = [], flow["_path"]
    need = ["id", "name", "status", "purpose", "trigger", "steps", "why"]
    need += ["moment", "rules", "watch"] if folder == "core" else ["tier", "needs"]
    missing = [k for k in need if k not in flow]
    if missing:
        return [f"{where}: missing {', '.join(missing)}"]
    if not re.fullmatch(r"\d\d-%s\.json" % re.escape(flow["id"]), Path(where).name):
        out.append(f"{where}: file name does not match id '{flow['id']}'")
    if folder == "core":
        if flow["moment"] not in [m[0] for m in MOMENTS]:
            out.append(f"{where}: unknown moment '{flow['moment']}'")
        if flow["status"] not in ("running", "built"):
            out.append(f"{where}: status must be running or built")
    else:
        if flow["tier"] not in [t[0] for t in TIERS]:
            out.append(f"{where}: unknown tier '{flow['tier']}'")
        if flow["status"] != "planned":
            out.append(f"{where}: status must be planned")
    if len(flow["purpose"].split()) > MAX_PURPOSE_WORDS:
        out.append(f"{where}: purpose is longer than {MAX_PURPOSE_WORDS} words")
    for n, step in enumerate(flow["steps"], 1):
        fields = STEP_FIELDS.get(step.get("do"))
        if fields is None:
            out.append(f"{where}: step {n} has unknown type '{step.get('do')}'")
        elif [f for f in fields if f not in step]:
            out.append(f"{where}: step {n} ({step['do']}) needs {', '.join(fields)}")
        elif step["do"] == "wait" and (step["unit"] not in UNIT_MINUTES or not isinstance(step["amount"], int)
                                       or step["amount"] < 1):
            out.append(f"{where}: step {n} wait needs a whole amount in minutes, hours or days")
    if out:
        return out
    sends, event = timeline(flow)
    if folder == "core":
        if not sends:
            out.append(f"{where}: a core flow needs at least one send")
        elif sends[-1][0] > SPAN:
            out.append(f"{where}: runs past the end of the map ({SPAN // 1440} days)")
        if event and (len(sends) != 1 or any(s["do"] == "wait" for s in flow["steps"])):
            out.append(f"{where}: a wait-for flow may hold one send and no timed waits")
    return out


def timeline(flow):
    """Every send as (minutes from the start, type, name), plus the wait-for step if there is one."""
    minutes, sends, event = 0, [], None
    for step in flow["steps"]:
        if step["do"] == "wait":
            minutes += step["amount"] * UNIT_MINUTES[step["unit"]]
        elif step["do"] == "wait-for":
            event = step
        elif step["do"] in SENDS:
            sends.append((minutes, step["do"], step["name"]))
    return sends, event


def position(minutes):
    return round(math.log10(minutes + 1) / math.log10(SPAN + 1) * 100, 2)


def after(minutes):
    if minutes == 0:
        return "at once"
    if minutes < 60:
        return f"after {minutes} minutes"
    if minutes < 2880 and minutes % 60 == 0:
        hours = minutes // 60
        return f"after {hours} hour{'' if hours == 1 else 's'}"
    days = round(minutes / 1440)
    return f"after {days} day{'' if days == 1 else 's'}"


def track(flow):
    sends, event = timeline(flow)
    bits = ['<i class="origin"></i>']
    if event:
        name = sends[0][2]
        bits.append(f'<i class="rail rail-open" style="width:{EVENT_X}%"></i>')
        bits.append(f'<b class="stop" style="left:{EVENT_X}%" data-tip="{e(name)}, when {e(event["event"])}"></b>')
        bits.append(f'<span class="cap" style="left:{EVENT_X}%">{e(event["label"])}</span>')
        label = f"1 send: {name}, when {event['event']}"
    else:
        bits.append(f'<i class="rail" style="width:{position(sends[-1][0])}%"></i>')
        for minutes, _, name in sends:
            x = position(minutes)
            bits.append(f'<b class="stop{" tip-r" if x > 60 else ""}" style="left:{x}%" '
                        f'data-tip="{e(name)}, {after(minutes)}"></b>')
        if len(sends) == 1 and sends[0][0] == 0:
            bits.append('<span class="cap" style="left:0%">sent at once</span>')
        label = f"{len(sends)} send{'' if len(sends) == 1 else 's'}: " + "; ".join(
            f"{name} {after(minutes)}" for minutes, _, name in sends)
    return f'<span class="track" role="img" aria-label="{e(label)}">{"".join(bits)}</span>'


def route(flow):
    emails = sum(1 for s in flow["steps"] if s["do"] == "email")
    items, n = [f'<li class="r-start">Starts when {e(flow["trigger"])}.</li>'], 0
    for step in flow["steps"]:
        do = step["do"]
        if do == "wait":
            unit = step["unit"][:-1] if step["amount"] == 1 else step["unit"]
            items.append(f'<li class="r-wait">Wait {step["amount"]} {unit}</li>')
        elif do == "wait-for":
            items.append(f'<li class="r-wait">Wait until {e(step["event"])}</li>')
        elif do in SENDS:
            kind = SENDS[do]
            if do == "email" and emails > 1:
                n += 1
                kind = f"Email {n}"
            subject = step.get("subject")
            subject = (f'<span class="r-subject">Example subject: &ldquo;{e(subject)}&rdquo;</span>'
                       if subject and subject != step["name"] else "")
            items.append(f'<li class="r-send"><span class="r-kind">{kind}</span><strong>{e(step["name"])}</strong>'
                         f'<span class="r-job">{e(step["job"])}</span>{subject}</li>')
        elif do == "split":
            items.append(f'<li class="r-split"><strong>{e(step["ask"])}</strong>'
                         f'<span class="r-job">Yes: {e(step["yes"])}</span>'
                         f'<span class="r-job">No: {e(step["no"])}</span></li>')
        elif do == "note":
            items.append(f'<li class="r-note">{e(step["text"])}</li>')
    return '<ol class="route">' + "".join(items) + "</ol>"


def notes(*blocks):
    out = []
    for title, lines in blocks:
        if lines:
            out.append(f"<div><h4>{title}</h4><ul>" + "".join(f"<li>{e(x)}</li>" for x in lines) + "</ul></div>")
    return '<div class="notes">' + "".join(out) + "</div>"


def lane(flow):
    built = flow["status"] == "built"
    status = f'<span class="lane-status">{STATUS["built"]}</span>' if built else ""
    return (
        f'      <details class="lane{" is-built" if built else ""}" id="{e(flow["id"])}">\n'
        f'        <summary><span class="row"><span class="info"><span class="lane-name">{e(flow["name"])}</span>'
        f'<span class="lane-purpose">{e(flow["purpose"])}</span>{status}</span>'
        f'{track(flow)}<span class="toggle" aria-hidden="true"></span></span></summary>\n'
        f'        <div class="body">{route(flow)}'
        f'{notes(("Rules", flow["rules"]), ("Why it is built this way", flow["why"]), ("Watch out", flow["watch"]))}'
        f'</div>\n      </details>\n'
    )


def station(flow):
    return (
        f'          <details class="station" id="{e(flow["id"])}"><summary>{e(flow["name"])}</summary>'
        f'<div class="station-body"><p class="station-purpose">{e(flow["purpose"])}</p>{route(flow)}'
        f'{notes(("What it needs", flow["needs"]), ("Why", flow["why"]))}</div></details>\n'
    )


def page(core, planned, version):
    groups = []
    for key, title, colour in MOMENTS:
        lanes = "".join(lane(f) for f in core if f["moment"] == key)
        if lanes:
            groups.append(f'    <div class="group g-{colour}">\n      <h3>{title}</h3>\n{lanes}    </div>\n')
    tiers = []
    for key, title, when in TIERS:
        stations = "".join(station(f) for f in planned if f["tier"] == key)
        tiers.append(f'      <div class="tier">\n        <h3>{title}</h3>\n        <p class="tier-when">{when}</p>\n'
                     f'        <div class="stations">\n{stations}        </div>\n      </div>\n')
    values = {
        "VERSION": version,
        "REPO_URL": REPO_URL,
        "N_CORE": str(len(core)),
        "N_PLANNED": str(len(planned)),
        "SCALE": "".join('<span%s style="left:%s%%">%s</span>'
                         % (' class="minor"' if label in MINOR_TICKS else "", position(m), label) for m, label in TICKS),
        "TICK_IMAGES": ",".join(["linear-gradient(var(--rule),var(--rule))"] * len(TICKS)),
        "TICK_POSITIONS": ",".join(f"{position(m)}% 0" for m, _ in TICKS),
        "GROUPS": "".join(groups).rstrip("\n"),
        "TIERS": "".join(tiers).rstrip("\n"),
    }
    out = (ROOT / "site" / "template.html").read_text(encoding="utf-8")
    for key, value in values.items():
        out = out.replace("{{%s}}" % key, value)
    left = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if left:
        sys.exit(f"build: template placeholders left unfilled: {sorted(set(left))}")
    return out


def readme(core, planned, version):
    lines = ["| Flow | What it is for | Status | File |", "|---|---|---|---|"]
    for f in core:
        lines.append(f"| {f['name']} | {f['purpose']} | {STATUS[f['status']]} | [{Path(f['_path']).name}]({f['_path']}) |")
    lines += ["", "Planned, in the order they become worth building:", "",
              "| When | Flow | What it is for | File |", "|---|---|---|---|"]
    names = {key: title for key, title, _ in TIERS}
    for f in planned:
        lines.append(f"| {names[f['tier']]} | {f['name']} | {f['purpose']} | [{Path(f['_path']).name}]({f['_path']}) |")
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    text, n1 = re.subn(r"(<!-- flows -->\n).*?(<!-- /flows -->)",
                       lambda m: m.group(1) + "\n".join(lines) + "\n" + m.group(2), text, flags=re.S)
    text, n2 = re.subn(r"(<!-- version -->).*?(<!-- /version -->)", lambda m: m.group(1) + "v" + version + m.group(2), text)
    if n1 != 1 or n2 < 1:
        sys.exit("build: README.md is missing its flows or version markers")
    return text


class Visible(HTMLParser):
    """Counts the words a reader sees before opening anything."""

    VOID = {"meta", "br", "link", "img", "hr", "input"}

    def __init__(self):
        super().__init__()
        self.words, self.hidden, self.stack = 0, 0, []

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            return
        cls = dict(attrs).get("class") or ""
        hide = tag in ("style", "script", "title") or cls in ("body", "station-body")
        self.stack.append(hide)
        self.hidden += hide

    def handle_endtag(self, tag):
        if self.stack and tag not in self.VOID:
            self.hidden -= self.stack.pop()

    def handle_data(self, data):
        if not self.hidden:
            self.words += len(data.split())


def main():
    check = "--check" in sys.argv[1:]
    core, planned = load("core"), load("planned")
    errors = [p for f in core for p in problems(f, "core")] + [p for f in planned for p in problems(f, "planned")]
    ids = [f.get("id") for f in core + planned]
    errors += [f"duplicate id '{i}'" for i in sorted({i for i in ids if ids.count(i) > 1})]
    if errors:
        sys.exit("build: flow files need fixing:\n  " + "\n  ".join(errors))
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    index = ROOT / "docs" / "index.html"
    outputs = {index: page(core, planned, version), ROOT / "README.md": readme(core, planned, version)}
    counter = Visible()
    counter.feed(outputs[index])
    if counter.words > MAX_VISIBLE_WORDS:
        sys.exit(f"build: the page shows {counter.words} words before anything is opened; the limit is {MAX_VISIBLE_WORDS}")
    stale = [p for p, text in outputs.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
    summary = f"v{version}, {len(core)} core, {len(planned)} planned, {counter.words} visible words"
    if check:
        if stale:
            sys.exit("build: stale, run python3 tools/build_site.py: "
                     + ", ".join(p.relative_to(ROOT).as_posix() for p in stale))
        print(f"build: up to date ({summary})")
        return
    for path in stale:
        path.write_text(outputs[path], encoding="utf-8")
    print(f"build: {summary}, {len(stale)} file(s) written")


if __name__ == "__main__":
    main()
