#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

# ─── How to run ───
# 1. Install uv (if not installed):
#      curl -LsSf https://astral.sh/uv/install.sh | sh
# 2. Run directly (no venv, no pip install needed):
#      uv run scripts/verify.py .
# 3. Or make executable and run:
#      chmod +x scripts/verify.py && ./scripts/verify.py .
# ──────────────────

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def verify_git_whitespace(repo: Path) -> None:
    for args in (("diff", "--check"), ("diff", "--cached", "--check")):
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            print(result.stdout, end="")
            print(result.stderr, end="", file=sys.stderr)
            fail(f"git {' '.join(args)} failed")


def main() -> None:
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    skill_dir = repo / "skills" / "tool-schema-design"
    skill = skill_dir / "SKILL.md"
    readme = repo / "README.md"
    groupings = repo / "skills.sh.json"

    for path in (skill, readme, groupings):
        if not path.is_file():
            fail(f"missing required file: {path}")

    text = skill.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3:
        fail("SKILL.md must contain one YAML frontmatter block")
    frontmatter = parts[1]

    name_match = re.search(r"^name:\s*(\S+)\s*$", frontmatter, re.M)
    if not name_match or name_match.group(1) != skill_dir.name:
        fail("frontmatter name must equal the skill directory")

    desc_match = re.search(r"^description: >-\n((?:  .*\n)+)", frontmatter, re.M)
    if not desc_match:
        fail("description must use one folded YAML block scalar")
    description = " ".join(line.strip() for line in desc_match.group(1).splitlines())
    if len(description) > 1024:
        fail(f"description is {len(description)} characters; maximum is 1024")

    if len(text.splitlines()) > 500:
        fail("SKILL.md exceeds the repository's 500-line house budget")

    required_refs = {
        "references/provider-matrix.md",
        "references/authoring.md",
        "references/deep-dive.md",
        "references/conformance.md",
    }
    linked_refs = set(re.findall(r"\]\((references/[^)#]+\.md)\)", text))
    missing_links = required_refs - linked_refs
    if missing_links:
        fail(f"SKILL.md does not link required references: {sorted(missing_links)}")
    for rel in sorted(linked_refs):
        if not (skill_dir / rel).is_file():
            fail(f"broken relative link from SKILL.md: {rel}")

    for path in sorted((skill_dir / "references").glob("*.md")):
        ref_text = path.read_text(encoding="utf-8")
        if ref_text.count("```") % 2:
            fail(f"unbalanced fenced code blocks in {path}")
        for target in re.findall(r"\]\((?!https?://|#)([^)#]+\.md)\)", ref_text):
            if not (path.parent / target).resolve().is_file():
                fail(f"broken relative link in {path}: {target}")

    if text.count("```") % 2:
        fail("unbalanced fenced code blocks in SKILL.md")

    readme_text = readme.read_text(encoding="utf-8")
    if readme_text.count("[`tool-schema-design`](skills/tool-schema-design/SKILL.md)") != 1:
        fail("README must contain exactly one tool-schema-design row")
    for phrase in ("Loss-aware design", "semantic source contracts", "conformance cases"):
        if phrase not in readme_text:
            fail(f"README row is missing expected concept: {phrase}")

    data = json.loads(groupings.read_text(encoding="utf-8"))
    occurrences = sum(
        skill_name == "tool-schema-design"
        for grouping in data.get("groupings", [])
        for skill_name in grouping.get("skills", [])
    )
    if occurrences != 1:
        fail(f"tool-schema-design must appear in exactly one skills.sh grouping; found {occurrences}")

    stale_phrases = (
        'Root is a non-empty `type: "object"`',
        "adapters exist only for strict-mode transforms",
        "ignored but never rejected elsewhere",
        "xAI & loose Anthropic: omit from `required`",
        "Gemini/Vertex/Firebase",
        '`"count: "five"`',
    )
    changed_markdown = [readme, *sorted(skill_dir.rglob("*.md"))]
    all_skill_text = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(skill_dir.rglob("*.md"))
    )
    for path in changed_markdown:
        raw = path.read_text(encoding="utf-8")
        if not raw.endswith("\n"):
            fail(f"file must end with a newline: {path}")
        for number, line in enumerate(raw.splitlines(), 1):
            if line.rstrip() != line:
                fail(f"trailing whitespace in {path}:{number}")
    for phrase in stale_phrases:
        if phrase in all_skill_text:
            fail(f"stale or incorrect guidance remains: {phrase}")

    required_concepts = (
        "Semantic source contract",
        "Target profile",
        '"exact" | "reversible" | "lossy" | "unsupported"',
        "OPTIONAL_NULLABLE_STATE_COLLAPSE",
        "parametersJsonSchema",
        "no-argument",
        "runtime validator",
    )
    for phrase in required_concepts:
        if phrase not in all_skill_text:
            fail(f"required architecture concept missing: {phrase}")

    secret_patterns = {
        "GitHub token": r"gh[pousr]_[A-Za-z0-9]{16,}",
        "OpenAI-style secret": r"sk-[A-Za-z0-9]{20,}",
        "AWS access key": r"AKIA[0-9A-Z]{16}",
        "private key": r"-----BEGIN [A-Z ]*PRIVATE KEY",
        "Bearer token": r"Bearer [A-Za-z0-9._-]{20,}",
        "machine path": r"(?i)(?:/home/[A-Za-z0-9]|/Users/[A-Za-z0-9]|C:\\Users\\[A-Za-z0-9])",
    }
    for label, pattern in secret_patterns.items():
        if re.search(pattern, all_skill_text):
            fail(f"possible {label} in public skill content")

    if (repo / ".git").exists():
        verify_git_whitespace(repo)

    print("OK: tool-schema-design repository verification passed")
    print(f"OK: frontmatter description length = {len(description)}")
    print(f"OK: SKILL.md lines = {len(text.splitlines())}")
    print(f"OK: linked references = {len(linked_refs)}")


if __name__ == "__main__":
    main()
