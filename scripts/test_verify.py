#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

# ─── How to run ───
# 1. Run from the repository root:
#      python3 scripts/test_verify.py
# 2. Or run directly:
#      uv run scripts/test_verify.py
# ──────────────────

from __future__ import annotations

import contextlib
import io
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import verify


class VerifyScriptTests(unittest.TestCase):
    def copy_repository(self, destination: Path) -> None:
        source = Path(__file__).resolve().parents[1]
        shutil.copy2(source / "README.md", destination / "README.md")
        shutil.copy2(source / "LICENSE", destination / "LICENSE")
        shutil.copy2(source / "AGENTS.md", destination / "AGENTS.md")
        shutil.copy2(source / "skills.sh.json", destination / "skills.sh.json")
        shutil.copytree(
            source / "skills" / "tool-schema-design",
            destination / "skills" / "tool-schema-design",
        )

    def run_verifier(self, repository: Path, *arguments: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(sys, "argv", ["verify.py", str(repository), *arguments]):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                try:
                    verify.main()
                except SystemExit as error:
                    return int(error.code), stdout.getvalue(), stderr.getvalue()
        return 0, stdout.getvalue(), stderr.getvalue()

    def test_rejects_extra_arguments(self) -> None:
        code, _, stderr = self.run_verifier(Path("."), "extra")
        self.assertEqual(code, 1)
        self.assertIn("usage: verify.py [repository]", stderr)

    def test_missing_path_error_is_repository_relative(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory) / "missing-repository"
            code, _, stderr = self.run_verifier(repository)
        self.assertEqual(code, 1)
        self.assertIn("skills/tool-schema-design/SKILL.md", stderr)
        self.assertNotIn(str(repository), stderr)

    def test_accepts_optional_frontmatter_fields_in_different_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            (repository / "skills").mkdir()
            self.copy_repository(repository)
            skill = repository / "skills" / "tool-schema-design" / "SKILL.md"
            original = skill.read_text(encoding="utf-8")
            frontmatter = original.split("---", 2)[1]
            description = re.search(
                r"^description: >-\n((?:  .*\n)+)", frontmatter, re.M
            )
            self.assertIsNotNone(description)
            reordered = (
                "\nname: tool-schema-design\n"
                "license: MIT\n"
                "metadata:\n"
                "  author: minpeter\n"
                "description: >-\n"
                f"{description.group(1)}"
            )
            skill.write_text(original.replace(frontmatter, reordered), encoding="utf-8")
            code, stdout, stderr = self.run_verifier(repository)
        self.assertEqual((code, stderr), (0, ""))
        self.assertIn("repository verification passed", stdout)

    def test_scans_other_public_skills(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            (repository / "skills").mkdir()
            self.copy_repository(repository)
            other = repository / "skills" / "other-skill"
            other.mkdir()
            (other / "SKILL.md").write_text(
                "---\nname: other-skill\ndescription: >-\n  bad person@private.test\n---\n",
                encoding="utf-8",
            )
            code, _, stderr = self.run_verifier(repository)
        self.assertEqual(code, 1)
        self.assertIn("non-example email", stderr)

    def test_scans_top_level_public_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            (repository / "skills").mkdir()
            self.copy_repository(repository)
            agents = repository / "AGENTS.md"
            agents.write_text(
                f"{agents.read_text(encoding='utf-8')}bad person@private.test\n",
                encoding="utf-8",
            )
            code, _, stderr = self.run_verifier(repository)
        self.assertEqual(code, 1)
        self.assertIn("non-example email", stderr)

    def test_scans_public_groupings_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            (repository / "skills").mkdir()
            self.copy_repository(repository)
            groupings = repository / "skills.sh.json"
            groupings.write_text(
                groupings.read_text(encoding="utf-8").replace(
                    "{", '{"contact": "person@private.test",', 1
                ),
                encoding="utf-8",
            )
            code, _, stderr = self.run_verifier(repository)
        self.assertEqual(code, 1)
        self.assertIn("non-example email", stderr)

    def test_scans_public_license_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            (repository / "skills").mkdir()
            self.copy_repository(repository)
            license_file = repository / "LICENSE"
            license_file.write_text(
                f"{license_file.read_text(encoding='utf-8')}contact person@private.test\n",
                encoding="utf-8",
            )
            code, _, stderr = self.run_verifier(repository)
        self.assertEqual(code, 1)
        self.assertIn("non-example email", stderr)

    def test_scans_non_email_public_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            (repository / "skills").mkdir()
            self.copy_repository(repository)
            other = repository / "skills" / "other-skill"
            other.mkdir()
            (other / "SKILL.md").write_text(
                "---\nname: other-skill\ndescription: >-\n"
                "  api.internal 10.0.0.1 postgres://db ghp_" + "A" * 20 + "\n---\n",
                encoding="utf-8",
            )
            code, _, stderr = self.run_verifier(repository)
        self.assertEqual(code, 1)
        self.assertIn("GitHub token", stderr)

    def test_ignores_maintainer_pattern_documentation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            (repository / "skills").mkdir()
            self.copy_repository(repository)
            maintainer = repository / "skills" / "minpeter-skills-maintainer"
            maintainer.mkdir()
            (maintainer / "SKILL.md").write_text(
                "contact dev@private.test; use api.internal; /Users/[A-Za-z0-9]\n",
                encoding="utf-8",
            )
            code, _, stderr = self.run_verifier(repository)
        self.assertEqual((code, stderr), (0, ""))

    def test_scans_non_pattern_maintainer_documentation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            (repository / "skills").mkdir()
            self.copy_repository(repository)
            maintainer = repository / "skills" / "minpeter-skills-maintainer" / "references"
            maintainer.mkdir(parents=True)
            (maintainer / "authoring.md").write_text(
                "contact dev@private.test\n",
                encoding="utf-8",
            )
            code, _, stderr = self.run_verifier(repository)
        self.assertEqual(code, 1)
        self.assertIn("non-example email", stderr)

    def test_rejects_string_loss_flag_in_c05(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            (repository / "skills").mkdir()
            self.copy_repository(repository)
            conformance = repository / "skills" / "tool-schema-design" / "references" / "conformance.md"
            text = conformance.read_text(encoding="utf-8")
            text = text.replace(
                '"wire_fidelity": "lossy",\n  "distinction_lost": true,',
                '"wire_fidelity": "lossy",\n  "distinction_lost": "true",',
                1,
            )
            text = text.replace(
                "### C06: nested closed objects",
                "### C06: nested closed objects\n\n```json\n"
                '{"wire_fidelity": "lossy", "distinction_lost": true, '
                '"diagnostic_code": "OPTIONAL_NULLABLE_STATE_COLLAPSE", '
                '"default_action": "reject"}\n```',
                1,
            )
            conformance.write_text(text, encoding="utf-8")
            code, _, stderr = self.run_verifier(repository)
        self.assertEqual(code, 1)
        self.assertIn("boolean loss and rejection", stderr)

    def test_git_whitespace_uses_fixed_argv_and_timeout(self) -> None:
        completed = type("Completed", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        with patch("verify.subprocess.run", return_value=completed) as run:
            verify.verify_git_whitespace(Path("/repo"))
        self.assertEqual(run.call_count, 2)
        first_args, first_kwargs = run.call_args_list[0]
        self.assertEqual(first_args[0][:3], ["git", "-C", "/repo"])
        self.assertEqual(first_kwargs["timeout"], 30)
        self.assertFalse(first_kwargs["check"])


if __name__ == "__main__":
    unittest.main()
