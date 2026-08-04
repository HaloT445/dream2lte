#!/usr/bin/env python3
"""Inventory the pinned Linux 4.4 Exynos8895 donor surface for a 5.15 port.

This script does not copy files. It produces a deterministic manifest and a
classification report so later import steps can use strict allowlists.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

EXPECTED_COMMIT = "dcdaf6878e7f9497e1d90e25980decfa5d684f74"

GROUPS: dict[str, tuple[str, ...]] = {
    "device_tree": (
        "arch/arm64/boot/dts/exynos/exynos8895*.dts",
        "arch/arm64/boot/dts/exynos/exynos8895*.dtsi",
    ),
    "dt_bindings": (
        "include/dt-bindings/clock/exynos8895.h",
        "include/dt-bindings/soc/samsung/exynos8895.h",
        "include/dt-bindings/ufs/*.h",
        "include/dt-bindings/sysmmu/*.h",
        "include/dt-bindings/thermal/*.h",
    ),
    "clock_cal_pmucal": (
        "drivers/clk/samsung/clk-exynos8895.c",
        "drivers/clk/samsung/composite.c",
        "drivers/clk/samsung/composite.h",
        "drivers/soc/samsung/cal-if/**",
        "include/soc/samsung/cal-if.h",
        "include/soc/samsung/ect_parser.h",
        "include/soc/samsung/exynos-pmu.h",
    ),
    "pinctrl_eint": (
        "drivers/pinctrl/samsung/pinctrl-exynos.c",
        "drivers/pinctrl/samsung/pinctrl-exynos.h",
        "drivers/pinctrl/samsung/pinctrl-samsung.c",
        "drivers/pinctrl/samsung/pinctrl-samsung.h",
    ),
    "power_domain_pmu": (
        "drivers/soc/samsung/exynos-pd.c",
        "drivers/soc/samsung/exynos-pmu.c",
        "drivers/soc/samsung/exynos-pm.c",
        "drivers/soc/samsung/exynos-reboot.c",
    ),
    "ufs_host_phy": (
        "drivers/scsi/ufs/ufs-exynos.c",
        "drivers/scsi/ufs/ufs-exynos.h",
        "drivers/phy/**/*ufs*.c",
        "drivers/phy/**/*ufs*.h",
        "drivers/phy/samsung/**/*ufs*.c",
        "drivers/phy/samsung/**/*ufs*.h",
    ),
    "early_boot_console_irq": (
        "drivers/tty/serial/samsung.c",
        "drivers/irqchip/irq-gic-v3.c",
        "drivers/clocksource/exynos_mct.c",
        "arch/arm64/kernel/psci.c",
    ),
    "android_device_config": (
        "arch/arm64/configs/*dream2lte*",
        "arch/arm64/configs/*exynos8895*",
    ),
}

DO_NOT_COPY = (
    "arch/arm64/kernel core implementation",
    "drivers/base and generic power-management core",
    "drivers/clk common-clock core and generic Samsung clock core",
    "drivers/irqchip generic GIC implementation",
    "drivers/pinctrl core",
    "drivers/scsi/ufs/ufshcd.c and generic UFS core",
    "drivers/scsi core",
    "drivers/phy core",
    "fs, mm, kernel and security core trees",
    "Android binder core from Linux 4.4",
    "KernelSU, SUSFS and root-hiding changes during BOOT_SAFE bring-up",
    "overclock, voltage and aggressive thermal changes",
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


def expand(root: Path, pattern: str) -> list[Path]:
    return sorted(path for path in root.glob(pattern) if path.is_file())


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "usage: inventory_4_4_donor.py <vendor-tree> <output-directory>"
        )

    root = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]).resolve()
    out.mkdir(parents=True, exist_ok=True)

    head = git_head(root)
    if head != EXPECTED_COMMIT:
        raise SystemExit(
            f"vendor commit mismatch: expected {EXPECTED_COMMIT}, got {head}"
        )

    selected: dict[str, list[dict[str, object]]] = {}
    seen: set[Path] = set()

    for group, patterns in GROUPS.items():
        entries: list[dict[str, object]] = []
        for pattern in patterns:
            for path in expand(root, pattern):
                relative = path.relative_to(root)
                if relative in seen:
                    continue
                seen.add(relative)
                entries.append(
                    {
                        "path": relative.as_posix(),
                        "size": path.stat().st_size,
                        "sha256": sha256(path),
                    }
                )
        entries.sort(key=lambda item: str(item["path"]))
        selected[group] = entries

    flat = [entry for entries in selected.values() for entry in entries]
    manifest = {
        "source_repository": "https://github.com/boloaimer/exynos-8895.git",
        "source_commit": head,
        "purpose": "Linux 5.15 direct dream2lte bring-up donor inventory",
        "copy_policy": "data-and-device-extension-only; adapt to 5.15 APIs",
        "groups": selected,
        "totals": {
            "files": len(flat),
            "bytes": sum(int(entry["size"]) for entry in flat),
        },
        "do_not_copy": list(DO_NOT_COPY),
        "physical_boot": "not tested",
    }

    (out / "exynos8895-4.4-donor-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )

    with (out / "exynos8895-4.4-donor-SHA256SUMS.txt").open("w") as handle:
        for entry in sorted(flat, key=lambda item: str(item["path"])):
            handle.write(f"{entry['sha256']}  {entry['path']}\n")

    with (out / "exynos8895-4.4-donor-summary.txt").open("w") as handle:
        handle.write(f"source_commit={head}\n")
        handle.write(f"files={len(flat)}\n")
        handle.write(f"bytes={sum(int(entry['size']) for entry in flat)}\n")
        for group, entries in selected.items():
            handle.write(f"group.{group}.files={len(entries)}\n")
        handle.write("copy_policy=data-and-device-extension-only\n")
        handle.write("generic_4_4_core_copy=forbidden\n")
        handle.write("kernel_su_susfs=excluded-from-boot-safe\n")
        handle.write("physical_boot=not_tested\n")

    (out / "DO_NOT_COPY_4_4_CORE.txt").write_text(
        "\n".join(f"- {item}" for item in DO_NOT_COPY) + "\n"
    )

    print(
        f"Pinned Exynos8895 donor inventory: {len(flat)} files, "
        f"{sum(int(entry['size']) for entry in flat)} bytes"
    )


if __name__ == "__main__":
    main()
