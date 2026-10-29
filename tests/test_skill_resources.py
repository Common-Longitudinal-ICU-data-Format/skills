"""Portable skill-loading checks; no clinical data, model calls, or analysis imports."""

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "clif-icu"
GUIDES = (
    "SKILL.md",
    "reference/agentic-coding.md",
    "reference/compatibility-review.md",
    "reference/current-mcide.md",
    "reference/phi-safe-development.md",
    "reference/synthetic-datasets.md",
)


def check_document(test, document):
    content = document.read_text(encoding="utf-8")
    for link in re.findall(r"\]\(([^)]+)\)", content):
        target = urlsplit(link)
        if target.scheme or not target.path:
            continue
        relative = unquote(target.path)
        test.assertNotIn("\\", relative, f"Nonportable link in {document}: {link}")
        current = document.parent
        for part in Path(relative).parts:
            if part == "..":
                current = current.parent
            elif part != ".":
                test.assertTrue(current.is_dir(), str(current))
                test.assertIn(part, {p.name for p in current.iterdir()},
                              f"Missing or wrong-case link in {document}: {link}")
                current = current / part
        test.assertTrue(current.exists(), str(current))


class SkillResources(unittest.TestCase):
    def test_standard_metadata(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
        self.assertIsNotNone(match)
        metadata = yaml.safe_load(match.group(1))
        self.assertEqual(metadata["name"], SKILL.name)
        self.assertRegex(metadata["name"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        self.assertGreater(len(metadata["description"]), 0)
        self.assertLessEqual(len(metadata["description"]), 1024)

    def test_exact_case_local_links(self):
        for name in GUIDES:
            with self.subTest(document=name):
                check_document(self, SKILL / name)
        check_document(self, ROOT / "agents" / "clif-code-reviewer.md")

    def test_install_in_path_with_spaces(self):
        with tempfile.TemporaryDirectory(prefix="CLIF skill with spaces ") as temp:
            installed = Path(temp) / "clif-icu"
            shutil.copytree(SKILL, installed, ignore=shutil.ignore_patterns("__pycache__"))
            for name in GUIDES:
                with self.subTest(document=name):
                    check_document(self, installed / name)

    def test_no_case_only_file_collisions(self):
        seen = {}
        for path in SKILL.rglob("*"):
            relative = path.relative_to(SKILL).as_posix()
            key = relative.casefold()
            self.assertNotIn(key, seen, f"Case-only collision: {relative}, {seen.get(key)}")
            seen[key] = relative

    def test_plugin_resource_registration(self):
        manifest = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        for plugin in manifest["plugins"]:
            for relative in plugin["skills"] + plugin["agents"]:
                self.assertTrue((ROOT / relative).exists(), relative)


if __name__ == "__main__":
    unittest.main(verbosity=2)
