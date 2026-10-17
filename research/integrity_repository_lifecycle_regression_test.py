#!/usr/bin/env python3
"""Exercise lifecycle failures against isolated copies of the real repository inputs."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from integrity_tranche5c_documentation_lifecycle import CANONICAL_DOCS

ROOT = Path(__file__).resolve().parents[1]
CHECKER = "research/integrity_tranche5c_documentation_lifecycle.py"
CONTRACT = "config/repository-lifecycle-contract.json"


class RepositoryLifecycleRegression(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="fie-lifecycle-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        paths = {ROOT / name for name in (*CANONICAL_DOCS, CHECKER, CONTRACT)}
        paths.add(ROOT / "docs/current/README.md")
        paths.update((ROOT / ".github/workflows").glob("*.y*ml"))
        paths.update((ROOT / "docs/current").glob("V*.md"))
        paths.update((ROOT / "docs/audits").glob("*TRANCHE4*"))
        paths.update(ROOT.glob("APPLY_*.md"))
        paths.update(ROOT.glob("APPLY_*.txt"))
        for source in paths:
            target = self.root / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

    def check(self, expected: str | None = None) -> None:
        result = subprocess.run(
            [sys.executable, str(self.root / CHECKER), "--mode", "target"],
            cwd=self.root, text=True, capture_output=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, timeout=30,
        )
        output = result.stdout + result.stderr
        if expected is None:
            self.assertEqual(result.returncode, 0, output)
        else:
            self.assertNotEqual(result.returncode, 0, output)
            self.assertIn(expected, output)

    def contract(self, mutate) -> None:
        path = self.root / CONTRACT
        content = json.loads(path.read_text(encoding="utf-8"))
        mutate(content)
        path.write_text(json.dumps(content), encoding="utf-8")

    def add_workflow(self, name: str, schedule: bool = False) -> None:
        trigger = "  schedule:\n    - cron: '0 0 * * *'\n" if schedule else ""
        (self.root / ".github/workflows" / name).write_text(
            "name: Lifecycle fixture\non:\n  workflow_dispatch:\n" + trigger
            + "jobs:\n  fixture:\n    runs-on: ubuntu-latest\n"
            + "    steps:\n      - run: echo fixture\n", encoding="utf-8",
        )

    def test_current_tree_passes(self) -> None:
        self.check()

    def test_exact_component_registration_regression(self) -> None:
        self.contract(lambda d: d["scheduled_workflows"].remove("component-weekly.yml"))
        self.check("unregistered schedules=['component-weekly.yml']")

    def test_new_unregistered_schedule_fails(self) -> None:
        self.add_workflow("capture-lifecycle-fixture.yml", schedule=True)
        self.check("unregistered schedules=['capture-lifecycle-fixture.yml']")

    def test_new_schedule_and_registration_pass_together(self) -> None:
        self.add_workflow("capture-lifecycle-fixture.yml", schedule=True)
        self.contract(lambda d: d["scheduled_workflows"].append("capture-lifecycle-fixture.yml"))
        self.check()

    def test_unclassified_manual_workflow_fails(self) -> None:
        self.add_workflow("unclassified-lifecycle-fixture.yml")
        self.check("Unclassified workflows=['unclassified-lifecycle-fixture.yml']")

    def test_yaml_extension_is_not_invisible(self) -> None:
        self.add_workflow("capture-lifecycle-fixture.yaml", schedule=True)
        self.check("unregistered schedules=['capture-lifecycle-fixture.yaml']")

    def test_deleted_registered_workflow_fails(self) -> None:
        (self.root / ".github/workflows/component-weekly.yml").unlink()
        self.check("missing/unscheduled registered workflows=['component-weekly.yml']")

    def test_renamed_registered_workflow_fails(self) -> None:
        path = self.root / ".github/workflows/component-weekly.yml"
        path.rename(path.with_name("capture-component-renamed.yml"))
        self.check("unregistered schedules=['capture-component-renamed.yml']")

    def test_removed_schedule_fails(self) -> None:
        self.add_workflow("component-weekly.yml")
        self.check("missing/unscheduled registered workflows=['component-weekly.yml']")

    def test_removed_completion_trigger_fails(self) -> None:
        self.add_workflow("build-fie-window1c-weekly-actions.yml")
        self.check("Workflow lifecycle completion mismatch")

    def test_missing_canonical_document_fails(self) -> None:
        (self.root / "docs/current/TESTING.md").unlink()
        self.check("docs/current/TESTING.md")


if __name__ == "__main__":
    unittest.main(verbosity=2)
