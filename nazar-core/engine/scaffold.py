"""Project scaffold for a brand that walks in with only the skills at the root. The task decides the folders.

  python scaffold.py tasks
      lists the task recipes (steps, kits, folders)
  python scaffold.py init "<Brand or working name>" --task packaging[,social,...] [--root .] [--new-brand]
      creates only the folders the task(s) need, a hub README.md, SPEC.md, STATUS.md, CLAUDE.md, .gitignore,
      _archive/MANIFEST.md, installs the nazar-researcher subagent and lays out 01_research/ for the tasks' research
      profiles. Re-run with a new task when the project grows: it adds what's missing and never overwrites.
  python scaffold.py archive <path> "<why>" [--root .]
      moves a file or folder into _archive/ (never deletes) and appends a line to _archive/MANIFEST.md
  python scaffold.py release <src_dir> <BRAND> vNN [--root .] [--kind CLIENT|BEHANCE]
      copies a finished output folder to the root as <KIND>_<BRAND>_vNN_<date>/ (real copies, so later rebuilds
      can never rewrite a sent release) and archives the previous release of that kind
  python scaffold.py status [--root .]
      what exists, the current release, SPEC locks still empty
  python scaffold.py --selftest

Never deletes, never overwrites. Client names stay in the client repo, never in the skills repo.
"""
import os, re, shutil, sys, json, time, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.normpath(os.path.join(HERE, "..", ".."))

FOLDERS = {
    "00": ("00_brief", "what the client gave, untouched, plus brief-summary.md"),
    "01": ("01_research", "nazar-research output: angles, sources, gaps, codes, summary, dataset/ (reference only)"),
    "02": ("02_strategy", "positioning, naming, tagline, messaging (locked lines go to SPEC.md)"),
    "03": ("03_identity", "logo, colour, type, illustration, photo style, brand book"),
    "04": ("04_packaging", "_architecture (formats, SKU list), core-reference/01_versions, 02_dielines, 03_mockups, print-production"),
    "05": ("05_social-media", "profile kit, backdrops, templates, pillars, posts"),
    "06": ("06_web", "structure, design, build, audit"),
    "07": ("07_campaign-ooh", "idea, key visual, adaptations per site, collateral"),
    "08": ("08_photo-video", "shot plans, plates, composites, films"),
    "09": ("09_meetings", "agendas and notes (YYYY-MM_topic.md)"),
    "10": ("10_deliverables", "client PDFs per version"),
}
SUB = {"04": ["_architecture", "core-reference/01_versions", "core-reference/02_dielines", "core-reference/03_mockups", "print-production"],
       "03": ["logo", "colour", "type"], "05": ["backdrops", "templates", "posts"], "08": ["plates", "films"]}
# task -> (steps, research kits, folders, folders added for a new brand)
TASKS = {
    "identity":  ("brief > research > strategy (lock name, tagline) > logo > colour + type > brand book > applications > story > release",
                  ["strategy", "logo", "brand-book", "type", "colour"], ["00", "01", "02", "03", "09", "10"], []),
    "packaging": ("brief > research (category, competitors, shelf, dataset of real packs) > core pack on a real dieline (one approved) > range + family rules > support pieces > shoot > story > release",
                  ["packaging", "dieline", "shoot"], ["00", "01", "04", "08", "09", "10"], ["02", "03"]),
    "rebrand":   ("brief > research (current assets: fame x uniqueness) > keep/change/drop > strategy if positioning moves > mark refresh > system > rollout > release",
                  ["strategy", "logo", "brand-book"], ["00", "01", "02", "03", "09", "10"], []),
    "social":    ("brief > research (feeds, competitors, culture) > pillars > backdrops > templates > first posts > playbook",
                  ["social", "backdrops"], ["00", "01", "05", "09"], ["03"]),
    "campaign":  ("brief > research (place, street media, culture) > idea + routes > key visual > adaptations > mockups in place > release",
                  ["ooh", "strategy"], ["00", "01", "07", "08", "09", "10"], []),
    "web":       ("brief > research (competitor and leader sites, customers) > structure > design > build > audit",
                  ["web"], ["00", "01", "06", "09"], ["03"]),
    "motion":    ("brief > research (idents in the category, specs) > storyboard > review stills > render > exports",
                  ["motion"], ["00", "01", "08", "09"], []),
    "shoot":     ("brief > research (best photography of the category) > shot plan > plates > composites > realism gates",
                  ["shoot", "art-direction", "study"], ["00", "01", "08", "09"], []),
    "piece":     ("brief > short research pass > make > QA", [], ["00", "01"], []),
}


def _w(path, text):
    if os.path.exists(path):
        return False
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    open(path, "w", encoding="utf-8").write(text); return True


def _tasks(arg):
    ts = [t.strip() for t in arg.split(",") if t.strip()]
    bad = [t for t in ts if t not in TASKS]
    if bad:
        raise SystemExit(f"unknown task(s) {bad}; known: {', '.join(TASKS)}")
    return ts


def init(brand, tasks, root=".", new_brand=False):
    made = []
    keys = sorted({k for t in tasks for k in TASKS[t][2] + (TASKS[t][3] if new_brand else [])})
    for k in keys:
        name, what = FOLDERS[k]
        os.makedirs(os.path.join(root, name), exist_ok=True)
        for sub in SUB.get(k, []):
            os.makedirs(os.path.join(root, name, sub), exist_ok=True)
        if _w(os.path.join(root, name, "README.md"), f"# {name}\n\n{what}\n"):
            made.append(name + "/")
    today = time.strftime("%Y-%m-%d")
    plan = "\n".join(f"- **{t}**: {TASKS[t][0]}" for t in tasks)
    fmap = "\n".join(f"{FOLDERS[k][0] + '/':22s}{FOLDERS[k][1]}" for k in keys)
    files = {
        "README.md": f"# {brand}: project hub\n\n> Confidential client work. Keep this repo private.\n\n## Task\n{plan}\n\n## Start here\n1. `SPEC.md` (locked decisions)\n2. `STATUS.md` (where we are)\n3. `01_research/summary.md`\n\n## Folder map\n```\n{fmap}\nCLIENT_<BRAND>_vNN_<date>/  release the client receives (latest only at the root)\nBEHANCE_<BRAND>_vNN_<date>/ portfolio release\n_archive/             superseded, moved never deleted (MANIFEST.md)\n```\n\n## Conventions\n- Images `brand_what-it-shows.jpg` · artwork `sku_size_side_vNN` · notes `YYYY-MM_topic.md`\n- Sent versions are frozen; archive, never delete; show before commit.\n",
        "SPEC.md": f"# {brand}: locked decisions\n\nLock each line in writing before production. A change after the lock costs a rebuild.\n\n| Decision | Value | Locked on |\n|---|---|---|\n| Name |  |  |\n| Tagline |  |  |\n| Core idea (one sentence) |  |  |\n| Palette |  |  |\n| Type |  |  |\n| Scope |  |  |\n\n## Open questions\n- \n",
        "STATUS.md": f"# Status\n\n- {today}: project scaffolded for {', '.join(tasks)}.\n",
        "CLAUDE.md": f"# {brand} (client project)\n\nUse the nazar skills: read `.claude/skills/nazar-core/SKILL.md` and `references/project_playbook.md` first.\nTask(s): {', '.join(tasks)}. Follow the recipe in the playbook, adjusted to the brief.\nResearch goes through `nazar-research` (subagent `nazar-researcher`) into `01_research/`.\nShow previews before big renders and before every commit; commit only on a clear yes.\nNever delete: `scaffold.py archive`. Sent versions are frozen.\n",
        ".gitignore": "*.zip\n__pycache__/\n_cache/\n.DS_Store\nThumbs.db\n",
        "_archive/MANIFEST.md": "# Archive manifest\n\nMoved here, never deleted. One line per move: date, what, from, why.\n\n",
    }
    for f, t in files.items():
        if _w(os.path.join(root, f), t):
            made.append(f)
    ag = os.path.join(SKILLS, "nazar-research", "agents", "nazar-researcher.md")
    dst = os.path.join(root, ".claude", "agents", "nazar-researcher.md")
    if os.path.exists(ag) and not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(ag, dst); made.append(".claude/agents/nazar-researcher.md")
    kits = sorted({k for t in tasks for k in TASKS[t][1]})
    ds = os.path.join(SKILLS, "nazar-research", "engine", "dataset.py")
    if kits and os.path.exists(ds):
        subprocess.run([sys.executable, ds, "plan", os.path.join(root, "01_research"), f"{brand}: {', '.join(tasks)}", "--kit", ",".join(kits)],
                       check=False, stdout=subprocess.DEVNULL)
    if made:
        open(os.path.join(root, "STATUS.md"), "a", encoding="utf-8").write(f"- {today}: added {', '.join(made)}\n")
    print(f"{brand}: tasks {tasks}; created {len(made)}: {', '.join(made) or 'nothing new'}")
    return made


def archive(path, why, root="."):
    src = os.path.join(root, path) if not os.path.isabs(path) else path
    if not os.path.exists(src):
        raise SystemExit(f"not found: {path}")
    dst = os.path.join(root, "_archive", os.path.basename(os.path.normpath(src)))
    if os.path.exists(dst):
        dst += time.strftime("_%Y%m%d-%H%M%S")
    os.makedirs(os.path.join(root, "_archive"), exist_ok=True)
    shutil.move(src, dst)
    _w(os.path.join(root, "_archive", "MANIFEST.md"), "# Archive manifest\n\n")
    open(os.path.join(root, "_archive", "MANIFEST.md"), "a", encoding="utf-8").write(
        f"- {time.strftime('%Y-%m-%d')}: `{os.path.basename(dst)}` from `{os.path.relpath(src, root)}`: {why}\n")
    print("archived", os.path.relpath(src, root), "->", os.path.relpath(dst, root)); return dst


def release(src, brand, ver, root=".", kind="CLIENT"):
    if not re.fullmatch(r"v\d{2}", ver):
        raise SystemExit("version must look like v03")
    name = f"{kind}_{brand.upper()}_{ver}_{time.strftime('%Y-%m-%d')}"
    dst = os.path.join(root, name)
    if os.path.exists(dst):
        raise SystemExit(f"{name} exists: a sent release is frozen; bump the version")
    for old in sorted(d for d in os.listdir(root) if d.startswith(f"{kind}_{brand.upper()}_v") and d != name):
        archive(old, f"superseded by {name}", root)
    shutil.copytree(src, dst)                       # real copies: a rebuild can never rewrite what was sent
    open(os.path.join(root, "STATUS.md"), "a", encoding="utf-8").write(f"- {time.strftime('%Y-%m-%d')}: released {name}\n")
    print("released", name); return dst


def status(root="."):
    rel = sorted(d for d in os.listdir(root) if re.match(r"(CLIENT|BEHANCE)_.+_v\d{2}_", d))
    have = [FOLDERS[k][0] for k in FOLDERS if os.path.isdir(os.path.join(root, FOLDERS[k][0]))]
    empty = []
    sp = os.path.join(root, "SPEC.md")
    if os.path.exists(sp):
        empty = [m.group(1).strip() for m in re.finditer(r"^\|\s*([^|]+?)\s*\|\s*\|", open(sp, encoding="utf-8").read(), re.M)]
    r = dict(folders=have, releases=rel, spec_unlocked=empty,
             research_summary=os.path.exists(os.path.join(root, "01_research", "summary.md")))
    print(json.dumps(r, indent=1)); return r


def selftest():
    import tempfile
    root = tempfile.mkdtemp(prefix="nazar_scaffold_")
    init("Testbrand", ["packaging"], root)
    assert os.path.isdir(os.path.join(root, "04_packaging", "core-reference", "01_versions"))
    assert not os.path.exists(os.path.join(root, "05_social-media")) and not os.path.exists(os.path.join(root, "02_strategy"))
    assert os.path.exists(os.path.join(root, "01_research", "summary.md"))
    open(os.path.join(root, "SPEC.md"), "a").write("kept")
    init("Testbrand", ["social"], root)                                   # project grows; nothing overwritten
    assert os.path.isdir(os.path.join(root, "05_social-media")) and open(os.path.join(root, "SPEC.md")).read().endswith("kept")
    init("Newco", ["packaging"], tempfile.mkdtemp(), new_brand=True)
    out = os.path.join(root, "out"); os.makedirs(out); open(os.path.join(out, "a.pdf"), "w").write("1")
    r1 = release(out, "Testbrand", "v01", root); open(os.path.join(out, "a.pdf"), "w").write("2")
    assert open(os.path.join(r1, "a.pdf")).read() == "1"                   # copies, not links
    os.rename(r1, r1.replace(time.strftime("%Y-%m-%d"), "2000-01-01"))
    release(out, "Testbrand", "v02", root)
    rel = [d for d in os.listdir(root) if d.startswith("CLIENT_")]; assert len(rel) == 1 and "_v02_" in rel[0]
    assert "CLIENT_TESTBRAND_v01" in open(os.path.join(root, "_archive", "MANIFEST.md")).read()
    s = status(root); assert "Name" in s["spec_unlocked"] and s["research_summary"]
    print("SELFTEST PASS")


if __name__ == "__main__":
    a = sys.argv[1:]
    def opt(k, d=None):
        return a[a.index(k) + 1] if k in a else d
    root = opt("--root", ".")
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
    elif a[0] == "--selftest":
        selftest()
    elif a[0] == "tasks":
        for t, (steps, kits, f, nb) in TASKS.items():
            print(f"{t:10s} {steps}\n{'':10s} folders {', '.join(FOLDERS[k][0] for k in f)}" + (f" (+ {', '.join(FOLDERS[k][0] for k in nb)} for a new brand)" if nb else "") + "\n")
    elif a[0] == "init":
        init(a[1], _tasks(opt("--task", "piece")), root, "--new-brand" in a)
    elif a[0] == "archive":
        archive(a[1], a[2], root)
    elif a[0] == "release":
        release(a[1], a[2], a[3], root, opt("--kind", "CLIENT"))
    elif a[0] == "status":
        status(root)
