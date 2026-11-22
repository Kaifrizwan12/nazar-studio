"""Opt-in contribution of generic lessons and project pathways back to the open-source nazar skills.

  python contribute.py ask [--root .]
      prints the one question to ask the user (once per project) and the current answer, if any
  python contribute.py set yes|no|later [--root .]
      records the answer in <root>/.claude/nazar.json (asked once; "later" asks again at the next release)
  python contribute.py preview [--root .] [--skills .claude/skills]
      collects LESSONS.md entries added in this project (vs the skills' git origin, or all entries dated after the
      install date) and the project pathway (task recipe, steps run, deviations from STATUS.md), scrubs private
      details, and writes <root>/.claude/contribution_preview.md for the user to read line by line
  python contribute.py send [--root .]
      only if the answer is yes and the preview exists: opens an issue on the skills repo with the preview through
      the user's own `gh` (the user sees and confirms gh's prompt); otherwise prints how to send it by hand
  python contribute.py --selftest

Nothing leaves the machine without the user's yes for that exact text. Scrubbing is a safety net, not a guarantee:
the user reads the preview before sending.
"""
import json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
QUESTION = ("These skills learn from real work. Would you like to share what this project teaches them, in a generic form? "
            "Only lessons (what failed, the evidence, the fix) and the order of steps you took are shared, with brand names, client names, "
            "people, contacts, links, prices and file paths removed. You will read the exact text before anything is sent, and you can say no "
            "at that point too.\n  yes: prepare a preview at each release\n  no: never ask again for this project\n  later: ask at the next release")
REPO = "Kaifrizwan12/nazar-studio"


def _cfg_path(root): return os.path.join(root, ".claude", "nazar.json")


def _cfg(root):
    p = _cfg_path(root)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def ask(root="."):
    c = _cfg(root).get("contribute")
    print(QUESTION if c in (None, "later") else f"already answered: {c}")
    return c


def set_answer(ans, root="."):
    if ans not in ("yes", "no", "later"):
        raise SystemExit("answer is yes, no or later")
    c = _cfg(root); c["contribute"] = ans; c["asked"] = time.strftime("%Y-%m-%d"); c.setdefault("installed", time.strftime("%Y-%m-%d"))
    os.makedirs(os.path.dirname(_cfg_path(root)), exist_ok=True)
    json.dump(c, open(_cfg_path(root), "w", encoding="utf-8"), indent=1); print("contribute:", ans)


def private_terms(root):
    """Words that must never leave: brand and client names from SPEC/README/brief, plus anything in .claude/private_terms.txt."""
    terms = set()
    for f in ("SPEC.md", "README.md", "00_brief/brief-summary.md"):
        p = os.path.join(root, f)
        if not os.path.exists(p):
            continue
        t = open(p, encoding="utf-8", errors="replace").read()
        m = re.search(r"^#\s*([^:\n]+?)\s*(?::|$)", t, re.M)
        if m:
            terms.add(m.group(1).strip())
        for row in re.finditer(r"^\|\s*(Name|Client|Brand)\s*\|\s*([^|]+?)\s*\|", t, re.M | re.I):
            terms.add(row.group(2).strip())
    p = os.path.join(root, ".claude", "private_terms.txt")
    if os.path.exists(p):
        terms |= {ln.strip() for ln in open(p, encoding="utf-8") if ln.strip()}
    terms = {t for t in terms if len(t) > 2 and t.lower() not in ("project hub", "status", "locked decisions")}
    for t in list(terms):
        terms |= {w for w in re.split(r"[\s:,/]+", t) if len(w) > 3 and w[0].isupper()}
    return sorted(terms, key=len, reverse=True)


def scrub(text, terms):
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[email]", text)          # structural scrubs first, then names
    text = re.sub(r"https?://\S+", "[link]", text)
    text = re.sub(r"(?:[A-Za-z]:)?[\\/](?:[\w .-]+[\\/])+[\w.-]+\.\w+", "[path]", text)
    text = re.sub(r"(\+?\d[\d\s-]{8,}\d)", "[phone]", text)
    text = re.sub(r"\b(?:Rs\.?|PKR|USD|\$|€|£)\s?\d[\d,.]*", "[price]", text)
    for t in terms:
        text = re.sub(re.escape(t), "[brand]", text, flags=re.I)
    text = re.sub(r"@[A-Za-z0-9_.]{2,}", "[handle]", text)
    return text


def lessons(skills, since=None):
    """New LESSONS.md lines: vs git origin if the skills are a clone, else entries dated on/after `since`."""
    out = []
    try:
        diff = subprocess.run(["git", "-C", skills, "diff", "origin/HEAD", "--", "*LESSONS.md"], capture_output=True, text=True, timeout=30)
        if diff.returncode == 0 and diff.stdout:
            kit = None
            for ln in diff.stdout.splitlines():
                m = re.match(r"\+\+\+ b/(.+?)/LESSONS\.md", ln)
                if m:
                    kit = m.group(1)
                elif ln.startswith("+") and not ln.startswith("+++") and ln[1:].strip():
                    out.append((kit, ln[1:].strip()))
            return out
    except Exception:
        pass
    for d in sorted(os.listdir(skills)):
        p = os.path.join(skills, d, "LESSONS.md")
        if os.path.exists(p):
            for ln in open(p, encoding="utf-8"):
                m = re.match(r"-\s*(\d{4}-\d{2}-\d{2})", ln.strip())
                if m and (since is None or m.group(1) >= since):
                    out.append((d, ln.strip()))
    return out


def pathway(root):
    p = os.path.join(root, "STATUS.md"); steps = []
    if os.path.exists(p):
        steps = [ln.strip() for ln in open(p, encoding="utf-8") if ln.strip().startswith("- ")]
    readme = os.path.join(root, "README.md"); task = ""
    if os.path.exists(readme):
        m = re.search(r"## Task\n(.+?)\n\n", open(readme, encoding="utf-8").read(), re.S)
        task = m.group(1).strip() if m else ""
    return task, steps


def preview(root=".", skills=None):
    skills = skills or os.path.join(root, ".claude", "skills")
    c = _cfg(root); terms = private_terms(root)
    task, steps = pathway(root)
    ls = lessons(skills, c.get("installed"))
    body = ["# Contribution preview (read every line before sending)", "",
            "## Pathway", scrub(task, terms) or "(no task recorded)", "", "### Steps as they happened"]
    body += [scrub(s, terms) for s in steps] or ["(none)"]
    body += ["", "## Lessons"]
    body += [f"- **{k}**: {scrub(l.lstrip('- '), terms)}" for k, l in ls] or ["(no new lessons)"]
    body += ["", f"_Scrubbed: {len(terms)} private terms, emails, links, phones, paths, prices, handles. Check anyway._"]
    p = os.path.join(root, ".claude", "contribution_preview.md")
    os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w", encoding="utf-8").write("\n".join(body) + "\n")
    left = [t for t in terms if re.search(re.escape(t), "\n".join(body), re.I)]
    print(p, f"({len(ls)} lessons, {len(steps)} steps)", "LEAK: " + ", ".join(left) if left else "")
    return p, left


def send(root="."):
    if _cfg(root).get("contribute") != "yes":
        raise SystemExit("the user has not said yes to contributing for this project")
    p = os.path.join(root, ".claude", "contribution_preview.md")
    if not os.path.exists(p):
        raise SystemExit("run preview first and let the user read it")
    _, left = preview(root)
    if left:
        raise SystemExit(f"private terms still in the preview: {left}; edit it, then send")
    cmd = ["gh", "issue", "create", "-R", REPO, "--title", "Kit lessons from a real project", "--body-file", p, "--label", "kit-lesson"]
    print("To send (the user confirms):", " ".join(cmd))
    print(f"Or by hand: open https://github.com/{REPO}/issues/new and paste {p}")


def selftest():
    import tempfile
    root = tempfile.mkdtemp(prefix="nazar_contrib_"); sk = os.path.join(root, ".claude", "skills", "nazar-packaging")
    os.makedirs(sk)
    open(os.path.join(root, "SPEC.md"), "w").write("# Zestico: locked decisions\n\n| Name | Zestico Foods |  |\n| Client | Mr Rahim Traders |  |\n")
    open(os.path.join(root, "README.md"), "w").write("# Zestico: project hub\n\n## Task\n- **packaging**: brief > research\n\n## Start\n")
    open(os.path.join(root, "STATUS.md"), "w").write("- 2026-01-02: Zestico core pack approved after 3 rounds\n- 2026-01-05: released CLIENT_ZESTICO_v01\n")
    open(os.path.join(sk, "LESSONS.md"), "w").write("- 2026-01-03: Zestico mango pouch at Rs 450 failed the shelf test; mail a@b.co; see https://x.y/z and C:\\work\\zestico\\a.png; @zestico_pk\n- 2020-01-01: old\n")
    assert ask(root) is None
    set_answer("yes", root); c = _cfg(root); c["installed"] = "2026-01-01"; json.dump(c, open(_cfg_path(root), "w"))
    p, left = preview(root); t = open(p, encoding="utf-8").read()
    for bad in ("Zestico", "Rahim", "a@b.co", "https://", "Rs 450", "C:\\work", "@zestico"):
        assert bad.lower() not in t.lower(), bad
    assert "[brand]" in t and "[price]" in t and "old" not in t and not left and "shelf test" in t
    set_answer("no", root); assert ask(root) == "no"
    try:
        send(root); raise AssertionError("sent without yes")
    except SystemExit:
        pass
    print("SELFTEST PASS")


if __name__ == "__main__":
    a = sys.argv[1:]
    root = a[a.index("--root") + 1] if "--root" in a else "."
    skills = a[a.index("--skills") + 1] if "--skills" in a else None
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
    elif a[0] == "--selftest":
        selftest()
    elif a[0] == "ask":
        ask(root)
    elif a[0] == "set":
        set_answer(a[1], root)
    elif a[0] == "preview":
        preview(root, skills)
    elif a[0] == "send":
        send(root)
