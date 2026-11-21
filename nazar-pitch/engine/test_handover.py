"""Self-check for handover.py (no network, temp folder only): python test_handover.py
Runs the engine's own --selftest (naming, sanitising, missing and stale sources, parking, checksums, zip tree,
dry run, release diff), then the CLI exit codes and the example manifests."""
import json, os, shutil, subprocess, sys, tempfile
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
EX = os.path.normpath(os.path.join(HERE, "..", "examples"))
sys.path.insert(0, HERE)
import handover as ho  # noqa: E402


def cli(*args):
    env = dict(os.environ, PYTHONUTF8="1")
    return subprocess.run([sys.executable, os.path.join(HERE, "handover.py"), *args], capture_output=True, text=True, env=env)


def main():
    n = ho.selftest()
    assert n >= 30, n

    tmp = tempfile.mkdtemp(prefix="handover_cli_")
    try:
        src = os.path.join(tmp, "src"); os.makedirs(src)
        for i in (1, 2): Image.new("RGB", (1600, 1200), (60 * i, 90, 120)).save(os.path.join(src, f"panel_{i:02d}.png"))
        man = {"project": "Test Co", "version": 1, "date": "2026-11-21", "source_root": "src", "release_root": "rel",
               "targets": {"portfolio": {"kind": "portfolio", "platform": "dribbble", "folder": "DRIBBBLE_{slug}_{stamp}",
                                         "cover": {"src": "panel_01.png"}}},
               "items": [{"src": "panel_*.png", "name": "{slug}_shot_{nn}"}]}
        mp = os.path.join(tmp, "m.json"); json.dump(man, open(mp, "w", encoding="utf-8"))

        # dry run: exit 0, prints the plan, writes nothing
        r = cli("build", mp, "--dry-run"); assert r.returncode == 0, r.stderr
        assert "DRY RUN" in r.stdout and "TEST_CO_shot_01.png" in r.stdout and not os.path.exists(os.path.join(tmp, "rel")), r.stdout
        # real build, then the JSON report
        r = cli("build", mp, "--json", os.path.join(tmp, "rep.json")); assert r.returncode == 0, r.stderr
        rep = json.load(open(os.path.join(tmp, "rep.json"), encoding="utf-8"))
        assert rep["targets"]["portfolio"]["folder"] == "DRIBBBLE_TEST_CO_v01_2026-11-21"
        assert os.path.isfile(os.path.join(tmp, "rel", "DRIBBBLE_TEST_CO_v01_2026-11-21", "00_COVER_1600x1200.png"))
        # release diff via the CLI
        Image.new("RGB", (1600, 1200), "#FF0000").save(os.path.join(src, "panel_02.png"))
        man["version"] = 2; json.dump(man, open(mp, "w", encoding="utf-8"))
        assert cli("build", mp).returncode == 0
        r = cli("diff", os.path.join(tmp, "rel", "DRIBBBLE_TEST_CO_v01_2026-11-21"), os.path.join(tmp, "rel", "DRIBBBLE_TEST_CO_v02_2026-11-21.zip"))
        assert r.returncode == 0 and "re-upload: 02" in r.stdout, r.stdout
        # missing source: exit 1, every problem listed, nothing written
        man["items"].append({"src": "ghost.png", "name": "ghost"}); man["release_root"] = "rel2"; json.dump(man, open(mp, "w", encoding="utf-8"))
        r = cli("build", mp); assert r.returncode == 1 and "HANDOVER FAILED" in r.stderr and "ghost.png" in r.stderr, r.stderr
        assert not os.path.exists(os.path.join(tmp, "rel2"))
        # broken JSON: exit 1, not a traceback
        open(mp, "w").write("{ nope"); r = cli("build", mp); assert r.returncode == 1 and "Traceback" not in r.stderr, r.stderr
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # example manifests: valid shape, known platforms, ISO date, labelled demo
    for f in ("handover_manifest.json", "handover_manifest_demo_bagh.json"):
        m, _ = ho.load_manifest(os.path.join(EX, f)); ho.base_context(m)
    assert "DEMO ONLY" in json.load(open(os.path.join(EX, "handover_manifest_demo_bagh.json"), encoding="utf-8"))["_about"]
    print("test_handover: all checks passed")


if __name__ == "__main__":
    main()
