#!/usr/bin/env python3
"""Tests for one canonical, relocatable pause state."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from pause_state import record, verify  # noqa: E402


class PauseStateTest(unittest.TestCase):
    def fixture(self):
        project = Path(tempfile.mkdtemp(prefix="pause-state-")) / "board"
        (project / "01_docs").mkdir(parents=True)
        (project / "03_src/route").mkdir(parents=True)
        (project / "06_build").mkdir()
        (project / "03_src/route/prefix.kicad_pcb").write_text("copper")
        (project / "06_build/receipt.json").write_text("{}")
        return project

    def test_record_verify_and_relocate(self):
        project = self.fixture()
        record(project, "routing", "03_src/route/prefix.kicad_pcb", "repair I2C",
               "python3 route.py --resume", ["06_build/receipt.json"])
        self.assertTrue(verify(project)[0])
        moved = project.parent / "moved-board"
        shutil.move(project, moved)
        # The project name is part of identity, so relocation is supported when
        # the root path changes but its checkout directory name stays the same.
        moved_same_name = moved.parent / "elsewhere" / "board"
        moved_same_name.parent.mkdir()
        shutil.move(moved, moved_same_name)
        self.assertTrue(verify(moved_same_name)[0])

    def test_changed_checkpoint_fails(self):
        project = self.fixture()
        record(project, "routing", "03_src/route/prefix.kicad_pcb", "repair I2C",
               "resume", [])
        (project / "03_src/route/prefix.kicad_pcb").write_text("changed")
        valid, failures = verify(project)
        self.assertFalse(valid)
        self.assertTrue(any("changed" in row for row in failures))

    def test_stale_status_view_fails(self):
        project = self.fixture()
        record(project, "routing", "03_src/route/prefix.kicad_pcb", "repair I2C",
               "resume", [])
        (project / "01_docs/STATUS.md").write_text("plausible stale prose")
        self.assertFalse(verify(project)[0])


if __name__ == "__main__":
    unittest.main()
