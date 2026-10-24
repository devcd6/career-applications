#!/usr/bin/env python3
"""Build resume.md and claims-used.md from an application-facts packet.

Usage:
    python scripts/build_application.py applications/<slug>            # reads the local application-facts.md
    python scripts/build_application.py applications/<slug> --check    # report only, write nothing

The spec holds the choices (which claims, which bracket options, which verb); this script
copies the claim wording verbatim so a bullet cannot drift from the KB. Review the spec,
then run scripts/check_application.py on the folder.

spec.json:
  title      heading for claims-used.md
  summary    the summary paragraph (ends with a "Committed to" or "Dedicated to" sentence)
  skills     list of "**Group:** text" lines for the skills block (KB wording)
  roles      {role id: [{"claims": [n, ...], "pick": {"0": 1}, "verb": "Served"}, ...]}
             claims: claim numbers within the role; the first supplies the bullet text, any
             others are mapped so their metrics cover numbers the first claim lacks.
             pick: which option to take for the Nth "[A | B]" group (default 0; -1 drops the group,
             as for a count alternative after a plain noun).
             Value brackets such as "6+ [six]" and groups after a number are dropped.
             verb: the starting verb; must match the first word of the bullet.
Legacy folders without an application-facts packet retain their existing fixed resume tail during migration.
"""
import argparse
import calendar
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_application as ca  # noqa: E402

HEADER = """## **DEVIKA C. DIXIT**

Dallas, TX | (925) 719-8412 | devikadixit25@gmail.com | LinkedIn: linkedin.com/in/devikadixittexas

## **SUMMARY**

{summary}

## **WORK EXPERIENCE**
"""

LEGACY_TAIL = """## **PUBLICATIONS**

Plante, A., & Dixit, D. C. (2026, April 22). *Chasing the High: Why Gambling Disorder Belongs in the Addiction Conversation*. National Council for Mental Wellbeing. https://www.thenationalcouncil.org/gambling-disorder-and-addiction/

## **EDUCATION**

**University of California, Santa Barbara**
Bachelor of Arts in Communications
Goleta, CA  2025

**Santa Barbara City College**
Associates in Political Science & Communications
Santa Barbara, CA  2022

## **CERTIFICATIONS & SKILLS**

**Certifications & Training:** Google Project Management Certificate, Google Data Analytics Certificate, Adult Mental Health First Aid, CDC Federal Grants Training Certification, Motivational Interviewing (OARS)
{skills}
"""


def resolve(canon, pick):
    """Resolve bracket groups: verb options are chosen, value alternatives are dropped."""
    out, last, gi = [], 0, 0
    for m in re.finditer(r"\[([^\]]*)\]", canon):
        out.append(canon[last:m.start()])
        body = m.group(1)
        if "|" in body:
            opts = [o.strip() for o in body.split("|")]
            choice = int(pick.get(str(gi), 0))
            gi += 1
            before = canon[:m.start()].rstrip()
            if choice != -1 and not (before and before[-1] in "+0123456789"):
                out.append(opts[choice])
        last = m.end()
    out.append(canon[last:])
    return re.sub(r"\s+,", ",", re.sub(r"\s{2,}", " ", "".join(out))).strip()


def claim_id_for_number(role_id, number, claims):
    wanted = str(int(number))
    matches = [
        claim_id for claim_id, claim in claims.items()
        if claim["role"] == role_id and claim_id.rsplit("-", 1)[-1].lstrip("0") == wanted
    ]
    return matches[0] if len(matches) == 1 else None


def format_month(value):
    if value.lower() == "present":
        return "Present"
    match = re.fullmatch(r"(\d{4})-(\d{2})", value)
    if not match:
        return value
    year, month = match.groups()
    return f"{calendar.month_abbr[int(month)]} {year}"


def format_dates(value):
    start, separator, end = value.partition(" to ")
    if not separator:
        return value
    return f"{format_month(start)} - {format_month(end)}"


def top_section(text, heading):
    match = re.search(rf"^# {re.escape(heading)}\s*$", text, re.MULTILINE)
    if not match:
        return None
    next_heading = re.search(r"^# (?!#)", text[match.end():], re.MULTILINE)
    end = match.end() + next_heading.start() if next_heading else len(text)
    return text[match.end():end]


def packet_entries(section, heading_pattern):
    if section is None:
        return {}
    headings = list(re.finditer(heading_pattern, section, re.MULTILINE))
    entries = {}
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(section)
        fields = {}
        for line in section[heading.end():end].splitlines():
            key, separator, value = line.partition(": ")
            if separator:
                fields[key] = value
        title = heading.group(2) if heading.lastindex and heading.lastindex > 1 else ""
        entries[heading.group(1)] = {"title": title, **fields}
    return entries


def parse_application_facts(text):
    summaries = packet_entries(top_section(text, "Selected summaries"), r"^### (S-\d{2})\s*$")
    education = packet_entries(
        top_section(text, "Selected education and credentials"),
        r"^### ((?:EDU|CERT|PUB)-\d+) (.+)$",
    )
    skills_section = top_section(text, "Selected skills") or ""
    skills = [line[2:].split(" | source:", 1)[0] for line in skills_section.splitlines() if line.startswith("- ")]
    return summaries, education, skills


def render_packet_tail(education, skills):
    publications = [entry for entry_id, entry in education.items() if entry_id.startswith("PUB-")]
    degrees = [entry for entry_id, entry in education.items() if entry_id.startswith("EDU-")]
    credentials = [entry["title"] for entry_id, entry in education.items() if entry_id.startswith("CERT-")]
    lines = []

    if publications:
        lines.extend(["## **PUBLICATIONS**", ""])
        for entry in publications:
            author = entry.get("authors", "")
            date = entry.get("date", "")
            title = entry.get("title", entry["title"])
            publisher = entry.get("publisher", "")
            url = entry.get("url", "")
            lines.append(f"{author} ({date}). *{title}*. {publisher}. {url}".strip())
            lines.append("")

    if degrees:
        lines.extend(["## **EDUCATION**", ""])
        for entry in degrees:
            lines.extend([
                f"**{entry.get('institution', '')}**",
                entry.get("degree", entry["title"]),
                f"{entry.get('location', '')}  {entry.get('end', '')}".strip(),
                "",
            ])

    lines.extend(["## **CERTIFICATIONS & SKILLS**", ""])
    lines.append(f"**Certifications & Training:** {', '.join(credentials)}")
    lines.extend(skills)
    return "\n".join(lines).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--claims", type=Path, help="application-facts packet (default: <folder>/application-facts.md)")
    ap.add_argument("--check", action="store_true", help="validate the spec, write nothing")
    args = ap.parse_args()
    folder = Path(args.folder)
    spec = json.loads((folder / "spec.json").read_text())
    claims_path = args.claims or folder / "application-facts.md"
    if not claims_path.exists() and (folder / "claims-packet.md").exists():
        claims_path = folder / "claims-packet.md"
    if not claims_path.exists():
        print(f"ERROR application-facts packet not found: {claims_path}")
        return 2
    packet_text = claims_path.read_text(encoding="utf-8")
    is_application_packet = packet_text.startswith("# Application facts packet\n")
    roles, claims = ca.load_claims(claims_path)
    summaries, education, packet_skills = parse_application_facts(packet_text) if is_application_packet else ({}, {}, [])

    resume = [HEADER.format(summary=spec["summary"])]
    used = [f"# {spec['title']}\n",
            "Format: bullet | claim ID | tier | verb. Tier from application-facts.md. Verb options resolved as "
            "set in spec.json; value brackets dropped so the canonical value stands.\n"]
    problems = []
    if is_application_packet:
        summary_source = spec.get("summary_source")
        if summary_source not in summaries:
            problems.append("summary_source must name a summary ID in application-facts.md")
        for skill_line in spec.get("skills", []):
            if not any(skill in skill_line for skill in packet_skills):
                problems.append(f"skills line is not supported by selected packet skills: {skill_line}")
    for role, bullets in spec["roles"].items():
        role_meta = roles.get(role)
        if not role_meta:
            problems.append(f"unknown role {role} in claims packet")
            continue
        employer = role_meta.get("employer", "").upper()
        title = role_meta.get("title", "").split("|")[0].strip()
        line = f"{role_meta.get('location', '')}  {format_dates(role_meta.get('dates', ''))}".strip()
        resume.append(f"## **{employer}**\n\n{title}\n{line}\n")
        used.append(f"\n## {employer}")
        for b in bullets:
            ids = [claim_id_for_number(role, n, claims) for n in b["claims"]]
            if any(claim_id is None for claim_id in ids):
                problems.append(f"unknown claim number(s) in {role}: {b['claims']}")
                continue
            missing = [i for i in ids if i not in claims]
            if missing:
                problems.append(f"unknown claim {missing}")
                continue
            text = resolve(claims[ids[0]]["canonical"], b.get("pick", {}))
            if not text.startswith(b["verb"]):
                problems.append(f"{ids[0]}: bullet starts '{text.split()[0]}', spec verb is '{b['verb']}'")
            resume.append(f"- {text}")
            used.append(f"- {text} | {', '.join(ids)} | {claims[ids[0]]['tier']} | {b['verb']}")
        resume.append("")
    if is_application_packet:
        resume.append(render_packet_tail(education, spec["skills"]))
    else:
        resume.append(LEGACY_TAIL.format(skills="\n".join(spec["skills"])))

    for p in problems:
        print("ERROR", p)
    if problems:
        return 1
    if args.check:
        print("spec ok")
        return 0
    (folder / "resume.md").write_text("\n".join(resume))
    (folder / "claims-used.md").write_text("\n".join(used) + "\n")
    print(f"wrote {folder}/resume.md and claims-used.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
