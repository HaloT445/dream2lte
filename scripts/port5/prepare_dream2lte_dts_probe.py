#!/usr/bin/env python3
"""Overlay the locked dream2lte DTS closure onto Linux 5.15 for a compile probe.

This is intentionally a temporary probe importer. It records every collision
with the Android Common 5.15 tree and does not authorize materialization of
legacy bindings without review.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
from pathlib import Path

EXPECTED_DONOR = "dcdaf6878e7f9497e1d90e25980decfa5d684f74"
TARGET = "exynos8895-dream2lte_eur_open_10.dtb"

FILES = (
    "arch/arm64/boot/dts/exynos/battery_data_dream2lte_common.dtsi",
    "arch/arm64/boot/dts/exynos/battery_data_dream2lte_eur_09.dtsi",
    "arch/arm64/boot/dts/exynos/ccic-s2mm005_01.dtsi",
    "arch/arm64/boot/dts/exynos/exynos8895-display-lcd.dtsi",
    "arch/arm64/boot/dts/exynos/exynos8895-dream2lte_common.dtsi",
    "arch/arm64/boot/dts/exynos/exynos8895-dream2lte_eur_open_10.dts",
    "arch/arm64/boot/dts/exynos/exynos8895-dream2lte_gpio_10.dtsi",
    "arch/arm64/boot/dts/exynos/exynos8895-dream2lte_motor.dtsi",
    "arch/arm64/boot/dts/exynos/exynos8895-dream2lte_svcled.dtsi",
    "arch/arm64/boot/dts/exynos/exynos8895-dreamlte_fingerprint-sensor_10.dtsi",
    "arch/arm64/boot/dts/exynos/exynos8895-dreamlte_mst_00.dtsi",
    "arch/arm64/boot/dts/exynos/exynos8895-ess.dtsi",
    "arch/arm64/boot/dts/exynos/exynos8895-pinctrl.dtsi",
    "arch/arm64/boot/dts/exynos/exynos8895-pm-domains.dtsi",
    "arch/arm64/boot/dts/exynos/exynos8895-rmem.dtsi",
    "arch/arm64/boot/dts/exynos/exynos8895-tmu-sensor-conf.dtsi",
    "arch/arm64/boot/dts/exynos/exynos8895.dtsi",
    "arch/arm64/boot/dts/exynos/exynos_gpio_config_macros.dtsi",
    "arch/arm64/boot/dts/exynos/modem-ss355ap-pdata.dtsi",
    "include/dt-bindings/clock/exynos8895.h",
    "include/dt-bindings/power/exynos-power.h",
    "include/dt-bindings/soc/samsung/exynos8895.h",
    "include/dt-bindings/sysmmu/sysmmu.h",
    "include/dt-bindings/thermal/thermal.h",
    "include/dt-bindings/thermal/thermal_exynos.h",
    "include/dt-bindings/ufs/ufs.h",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("donor", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()

    donor = args.donor.resolve()
    destination = args.destination.resolve()
    evidence = args.evidence.resolve()
    evidence.mkdir(parents=True, exist_ok=True)

    head = git_head(donor)
    if head != EXPECTED_DONOR:
        raise SystemExit(f"donor mismatch: {head}")

    manifest = evidence / "DTS_IMPORT_SHA256SUMS.txt"
    collisions = evidence / "DTS_COLLISIONS.tsv"
    imported = evidence / "DTS_IMPORTED_FILES.txt"

    manifest_lines: list[str] = []
    collision_lines = ["path\tdestination_sha256\tdonor_sha256\tsame\n"]
    imported_lines: list[str] = []

    for relative in FILES:
        source = donor / relative
        target = destination / relative
        if not source.is_file():
            raise SystemExit(f"missing locked donor file: {relative}")

        donor_sha = sha256(source)
        if target.exists():
            if not target.is_file():
                raise SystemExit(f"destination collision is not a file: {relative}")
            dest_sha = sha256(target)
            collision_lines.append(
                f"{relative}\t{dest_sha}\t{donor_sha}\t{str(dest_sha == donor_sha).lower()}\n"
            )

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if sha256(target) != donor_sha:
            raise SystemExit(f"copy checksum mismatch: {relative}")
        manifest_lines.append(f"{donor_sha}  {relative}\n")
        imported_lines.append(relative + "\n")

    makefile = destination / "arch/arm64/boot/dts/exynos/Makefile"
    if not makefile.is_file():
        raise SystemExit("Linux 5.15 Exynos DTS Makefile missing")
    line = f"dtb-$(CONFIG_ARCH_EXYNOS) += {TARGET}"
    text = makefile.read_text()
    if line not in text:
        makefile.write_text(text.rstrip() + "\n" + line + "\n")

    manifest.write_text("".join(manifest_lines))
    collisions.write_text("".join(collision_lines))
    imported.write_text("".join(imported_lines))
    (evidence / "DTS_PROBE_STATUS.txt").write_text(
        "migration=direct-4.4.302-to-5.15\n"
        "linux_4_19_dependency=none\n"
        f"donor_commit={EXPECTED_DONOR}\n"
        f"target={TARGET}\n"
        f"imported_files={len(FILES)}\n"
        "scope=temporary-compile-probe-only\n"
        "materialized=no\n"
        "physical_boot=not_tested\n"
    )

    print(f"Prepared direct DTS probe: {len(FILES)} files")
    print(f"Target: {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
