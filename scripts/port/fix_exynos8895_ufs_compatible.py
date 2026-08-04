#!/usr/bin/env python3
"""Align the upstream Exynos UFS backport with the locked dream2lte DTS."""

from pathlib import Path

path = Path("drivers/scsi/ufs/ufs-exynos.c")
text = path.read_text()
old = "samsung,exynos8895-ufs"
new = "samsung,exynos-ufs"
count = text.count(old)
if count != 2:
    raise SystemExit(f"expected two {old!r} occurrences, found {count}")
path.write_text(text.replace(old, new))
print(f"Exynos UFS compatible aligned with DTS: {new}")
