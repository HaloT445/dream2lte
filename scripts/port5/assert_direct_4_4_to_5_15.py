#!/usr/bin/env python3
"""Enforce the direct dream2lte Linux 4.4.302 -> Android Common 5.15 path.

Linux 4.19 branches may remain in the repository as archived evidence, but no
active Linux 5.15 workflow or port script may consume them as source, parent,
patch donor, build artifact or ABI bridge.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXPECTED = {
    "destination_branch": "android14-5.15",
    "destination_commit": "b10e5e5b5c5e01d49829aec34b65a0d717d6f2f5",
    "destination_tree": "7c3cd26c765b741df608a8b81cc6b93f1240fa36",
    "donor_commit": "dcdaf6878e7f9497e1d90e25980decfa5d684f74",
    "rollback_version": "4.4.302",
}

ACTIVE_GLOBS = (
    ".github/workflows/*5.15*.yml",
    ".github/workflows/*5.15*.yaml",
    "scripts/port5/**/*.py",
    "scripts/port5/**/*.sh",
    "scripts/port5/**/*.md",
    "scripts/port/discover_oneui8_kernel_paths.sh",
)

FORBIDDEN_PATTERNS = (
    re.compile(r"port/linux-4\.19", re.I),
    re.compile(r"android(?:/common)?[-_/ ]?4\.19", re.I),
    re.compile(r"linux[-_/ ]?4\.19[-_/ ]?(?:source|bringup|artifact|patch|abi)", re.I),
    re.compile(r"from[^\n]{0,80}4\.19", re.I),
    re.compile(r"depends?[^\n]{0,80}4\.19", re.I),
)


def active_files() -> list[Path]:
    found: set[Path] = set()
    for pattern in ACTIVE_GLOBS:
        found.update(path for path in ROOT.glob(pattern) if path.is_file())
    return sorted(found)


def require_text(path: Path, needle: str, label: str) -> None:
    text = path.read_text(errors="replace")
    if needle not in text:
        raise SystemExit(f"missing {label} in {path}: {needle}")


def main() -> int:
    files = active_files()
    if not files:
        raise SystemExit("no active Linux 5.15 workflow/port files found")

    violations: list[str] = []
    for path in files:
        text = path.read_text(errors="replace")
        for pattern in FORBIDDEN_PATTERNS:
            match = pattern.search(text)
            if match:
                line = text.count("\n", 0, match.start()) + 1
                violations.append(
                    f"{path.relative_to(ROOT)}:{line}: forbidden 4.19 dependency: "
                    f"{match.group(0)!r}"
                )

    if violations:
        print("Direct migration policy: FAIL", file=sys.stderr)
        print("\n".join(violations), file=sys.stderr)
        return 1

    materialize = ROOT / ".github/workflows/materialize-5.15-android-common-source.yml"
    donor = ROOT / ".github/workflows/probe-5.15-phase1-donor-inventory.yml"

    require_text(materialize, EXPECTED["destination_branch"], "5.15 destination branch")
    require_text(materialize, EXPECTED["destination_commit"], "5.15 destination commit")
    require_text(materialize, EXPECTED["destination_tree"], "5.15 destination tree")
    require_text(donor, EXPECTED["donor_commit"], "locked Linux 4.4 donor commit")

    migration = ROOT / "MIGRATION_5_15.md"
    require_text(migration, EXPECTED["rollback_version"], "locked rollback version")

    print("Direct migration policy: PASS")
    print(f"source_device_kernel=Linux {EXPECTED['rollback_version']}")
    print(f"device_donor_commit={EXPECTED['donor_commit']}")
    print(f"destination_android_common_branch={EXPECTED['destination_branch']}")
    print(f"destination_android_common_commit={EXPECTED['destination_commit']}")
    print("linux_4_19_dependency=none")
    print("linux_4_19_status=archived-evidence-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
