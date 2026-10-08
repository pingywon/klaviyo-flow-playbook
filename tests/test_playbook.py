import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build_site  # noqa: E402


class Playbook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core, cls.planned = build_site.load("core"), build_site.load("planned")
        cls.page = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        cls.version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

    def test_flow_files_are_valid(self):
        for folder, flows in (("core", self.core), ("planned", self.planned)):
            for flow in flows:
                self.assertEqual(build_site.problems(flow, folder), [], flow["_path"])

    def test_outputs_are_current(self):
        run = subprocess.run([sys.executable, str(ROOT / "tools" / "build_site.py"), "--check"],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)

    def test_version_is_shown(self):
        self.assertRegex(self.version, r"^\d+\.\d+\.\d+$")
        self.assertIn(f"<strong>Flow Playbook</strong> v{self.version}", self.page)
        self.assertIn(f"v{self.version}", (ROOT / "README.md").read_text(encoding="utf-8"))

    def test_every_flow_is_on_the_page(self):
        for flow in self.core + self.planned:
            self.assertIn(f'id="{flow["id"]}"', self.page)

    def test_page_loads_nothing_from_other_sites(self):
        links = set(re.findall(r'(?:src|href)="(https?://[^"]+)"', self.page))
        self.assertEqual(links, {build_site.REPO_URL})
        self.assertEqual(re.findall(r"url\([\"']?https?:", self.page), [])

    def test_tab_icon_is_linked_and_present(self):
        for name in re.findall(r'<link rel="(?:icon|apple-touch-icon)" href="([^"]+)"', self.page):
            self.assertTrue((ROOT / "docs" / name).is_file(), name)
        self.assertIn('href="favicon.svg"', self.page)

    def test_times(self):
        self.assertEqual(build_site.after(0), "at once")
        self.assertEqual(build_site.after(5), "after 5 minutes")
        self.assertEqual(build_site.after(60), "after 1 hour")
        self.assertEqual(build_site.after(25 * 60), "after 25 hours")
        self.assertEqual(build_site.after(2885), "after 2 days")
        self.assertEqual(build_site.position(0), 0)
        self.assertEqual(build_site.position(build_site.SPAN), 100)
        welcome = next(f for f in self.core if f["id"] == "welcome-series")
        self.assertEqual([m for m, _, _ in build_site.timeline(welcome)[0]], [5, 2885, 7205])

    def test_a_bad_flow_is_caught(self):
        flow = {"_path": "flows/core/01-x.json", "id": "x", "name": "X", "status": "running", "moment": "shopping",
                "purpose": "p", "trigger": "t", "rules": [], "why": [], "watch": [],
                "steps": [{"do": "wait", "amount": 2, "unit": "weeks"}]}
        self.assertTrue(build_site.problems(flow, "core"))


if __name__ == "__main__":
    unittest.main()
