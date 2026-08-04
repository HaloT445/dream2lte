#!/usr/bin/env python3
"""Map boot-critical paths for a direct Linux 4.4.302 -> 5.15 port.

This tool is read-only. It identifies destination APIs already present in
Android Common 5.15 and device-specific data/glue in the locked Exynos8895
Linux 4.4.302 donor. It never treats Linux 4.19 as a source or dependency.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Spec:
    group: str
    side: str
    strategy: str
    patterns: tuple[str, ...]
    required: bool = False


SPECS = (
    Spec("kernel_root", "destination-5.15", "use", ("Makefile",), True),
    Spec("gki_defconfig", "destination-5.15", "use", ("arch/arm64/configs/gki_defconfig",), True),
    Spec("android_build_config", "destination-5.15", "use", ("build.config.gki.aarch64",), True),
    Spec("binder", "destination-5.15", "use-5.15-core", ("drivers/android/binder.c",), True),
    Spec("vendor_hooks", "destination-5.15", "use-when-present", ("include/trace/hooks", "drivers/android/vendor_hooks.c")),
    Spec("exynos_dts_root", "destination-5.15", "extend", ("arch/arm64/boot/dts/exynos",), True),
    Spec("clock_framework", "destination-5.15", "keep-core-port-8895-data", ("drivers/clk/samsung",), True),
    Spec("pinctrl_framework", "destination-5.15", "keep-core-port-8895-tables", ("drivers/pinctrl/samsung",), True),
    Spec("power_domain_framework", "destination-5.15", "keep-genpd-port-domain-data", ("drivers/pmdomain/samsung", "drivers/soc/samsung"), True),
    Spec("ufs_host", "destination-5.15", "use-upstream-host-adapt-8895", ("drivers/ufs/host/ufs-exynos.c", "drivers/scsi/ufs/ufs-exynos.c"), True),
    Spec("ufs_phy", "destination-5.15", "use-upstream-phy-adapt-calibration", ("drivers/phy/samsung/phy-samsung-ufs.c", "drivers/phy/samsung/phy-exynos7-ufs.c"), True),
    Spec("erofs", "destination-5.15", "use-5.15-core", ("fs/erofs",), True),
    Spec("incfs", "destination-5.15", "use-5.15-core", ("fs/incfs",), True),

    Spec("dream2lte_dts", "donor-4.4.302", "port-device-data", ("arch/arm64/boot/dts/**/*dream2lte*.dts", "arch/arm64/boot/dts/**/*dream2lte*.dtsi"), True),
    Spec("exynos8895_dtsi", "donor-4.4.302", "port-soc-data", ("arch/arm64/boot/dts/**/*exynos8895*.dtsi",), True),
    Spec("exynos8895_dt_bindings", "donor-4.4.302", "port-bindings-selectively", ("include/dt-bindings/**/*8895*",), True),
    Spec("exynos8895_clock", "donor-4.4.302", "port-data-and-glue-only", ("drivers/clk/samsung/**/*8895*",), True),
    Spec("exynos8895_cal", "donor-4.4.302", "port-minimum-boot-closure", ("drivers/soc/samsung/cal-if/**/*", "drivers/soc/samsung/**/*cal*8895*")),
    Spec(
        "exynos8895_pinctrl",
        "donor-4.4.302",
        "extract-8895-bank-tables-from-shared-pinctrl-exynos.c",
        (
            "drivers/pinctrl/samsung/pinctrl-exynos.c",
            "drivers/pinctrl/samsung/pinctrl-samsung.c",
            "drivers/pinctrl/samsung/pinctrl-samsung.h",
        ),
        True,
    ),
    Spec("exynos8895_power_domains", "donor-4.4.302", "port-domain-list-boot-safe-always-on", ("arch/arm64/boot/dts/**/*pm-domain*", "drivers/soc/samsung/**/*pd*", "drivers/pmdomain/**/*8895*")),
    Spec("exynos8895_ufs_host", "donor-4.4.302", "reference-registers-resources-calibration-not-core", ("drivers/scsi/ufs/**/*exynos*", "drivers/ufs/**/*exynos*"), True),
    Spec("exynos8895_ufs_phy", "donor-4.4.302", "reference-calibration-only", ("drivers/phy/**/*ufs*",), True),
    Spec("dream2lte_defconfig", "donor-4.4.302", "translate-to-5.15-fragment-not-copy", ("arch/arm64/configs/**/*dream2lte*", "arch/arm64/configs/**/*alice*")),
)


FORBIDDEN_DONOR_CORE = (
    "drivers/scsi/ufs/ufshcd.c",
    "drivers/scsi/ufs/ufshcd.h",
    "kernel/irq/",
    "drivers/clk/clk.c",
    "drivers/pinctrl/core.c",
    "mm/",
    "fs/",
)


def kernel_version(root: Path) -> str:
    values: dict[str, str] = {}
    for line in (root / "Makefile").read_text(errors="replace").splitlines():
        for key in ("VERSION", "PATCHLEVEL", "SUBLEVEL"):
            if line.startswith(f"{key} ="):
                values[key] = line.split("=", 1)[1].strip()
    return ".".join(values.get(key, "?") for key in ("VERSION", "PATCHLEVEL", "SUBLEVEL"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve(root: Path, patterns: tuple[str, ...]) -> list[Path]:
    found: set[Path] = set()
    for pattern in patterns:
        candidate = root / pattern
        if not any(token in pattern for token in "*?[") and candidate.exists():
            found.add(candidate)
            continue
        found.update(root.glob(pattern))
    return sorted(found, key=lambda path: str(path.relative_to(root)))


def describe(root: Path, path: Path) -> tuple[str, str, str]:
    relative = str(path.relative_to(root))
    if path.is_symlink():
        return relative, "symlink", os.readlink(path)
    if path.is_dir():
        count = sum(1 for item in path.rglob("*") if item.is_file())
        return relative, "directory", f"files={count}"
    return relative, "file", f"bytes={path.stat().st_size};sha256={sha256(path)}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination_5_15", type=Path)
    parser.add_argument("donor_4_4_302", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    destination = args.destination_5_15.resolve()
    donor = args.donor_4_4_302.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    dest_version = kernel_version(destination)
    donor_version = kernel_version(donor)
    if not dest_version.startswith("5.15."):
        raise SystemExit(f"destination is not Linux 5.15: {dest_version}")
    if donor_version != "4.4.302":
        raise SystemExit(f"donor is not locked Linux 4.4.302: {donor_version}")

    rows: list[tuple[str, str, str, str, str, str]] = []
    missing: list[str] = []

    for spec in SPECS:
        root = destination if spec.side == "destination-5.15" else donor
        matches = resolve(root, spec.patterns)
        if spec.required and not matches:
            missing.append(f"{spec.side}:{spec.group}")
        if not matches:
            rows.append((spec.side, spec.group, spec.strategy, "missing", "", ""))
            continue
        for match in matches:
            relative, kind, detail = describe(root, match)
            rows.append((spec.side, spec.group, spec.strategy, kind, relative, detail))

    tsv = output / "DIRECT_KERNEL_PATH_MAP.tsv"
    with tsv.open("w") as handle:
        handle.write("side\tgroup\tstrategy\tkind\tpath\tdetail\n")
        for row in rows:
            handle.write("\t".join(row) + "\n")

    report = output / "DIRECT_KERNEL_PATH_MAP.md"
    with report.open("w") as handle:
        handle.write("# Direct dream2lte Linux 4.4.302 to 5.15 path map\n\n")
        handle.write(f"- Destination version: `{dest_version}`\n")
        handle.write(f"- Device donor version: `{donor_version}`\n")
        handle.write("- Linux 4.19 dependency: `none`\n")
        handle.write("- Scope: read-only source and build-path discovery\n\n")
        handle.write("## Path inventory\n\n")
        handle.write("| Side | Group | Strategy | Kind | Path | Detail |\n")
        handle.write("|---|---|---|---|---|---|\n")
        for row in rows:
            escaped = tuple(value.replace("|", "\\|") for value in row)
            handle.write("| " + " | ".join(escaped) + " |\n")

        handle.write("\n## Canonical build outputs\n\n")
        handle.write("```text\n")
        handle.write("out/dream2lte-5.15/arch/arm64/boot/Image\n")
        handle.write("out/dream2lte-5.15/arch/arm64/boot/dts/exynos/exynos8895-dream2lte*.dtb\n")
        handle.write("out/dream2lte-5.15/arch/arm64/boot/dts/exynos/*.dtbo\n")
        handle.write("out/dream2lte-5.15/**/*.ko\n")
        handle.write("out/dream2lte-5.15/modules.order\n")
        handle.write("out/dream2lte-5.15/modules.builtin*\n")
        handle.write("```\n\n")

        handle.write("## Firmware replacement target\n\n")
        handle.write("The kernel replacement target must be discovered from the actual ROM package. ")
        handle.write("For the locked legacy dream2lte baseline the expected component is `boot.img::kernel`, ")
        handle.write("but One UI 8 ports must also be scanned for `vendor_boot.img`, `init_boot.img` and `dtbo.img`.\n\n")

        handle.write("## Forbidden direct copies from Linux 4.4\n\n")
        for path in FORBIDDEN_DONOR_CORE:
            handle.write(f"- `{path}`\n")
        handle.write("\nOnly Exynos8895-specific data and glue may be adapted to Linux 5.15 APIs.\n")

    status = output / "DIRECT_KERNEL_PATH_STATUS.txt"
    status.write_text(
        f"destination_version={dest_version}\n"
        f"donor_version={donor_version}\n"
        "migration=direct-4.4.302-to-5.15\n"
        "linux_4_19_dependency=none\n"
        f"required_missing={len(missing)}\n"
        + "".join(f"missing={item}\n" for item in missing)
    )

    if missing:
        raise SystemExit("required path groups missing: " + ", ".join(missing))

    print(report)
    print(tsv)
    print(status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
