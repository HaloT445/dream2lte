#!/usr/bin/env python3
"""Port Exynos8895 pin-bank data onto the Linux 4.19 Samsung pinctrl core."""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

EXPECTED_VENDOR_COMMIT = "dcdaf6878e7f9497e1d90e25980decfa5d684f74"

EXPECTED_BANKS = [
    ("W", "alive", 6, 0x000, "etc1", 0x20),
    ("W", "alive", 8, 0x020, "gpa0", 0x00),
    ("W", "alive", 8, 0x040, "gpa1", 0x04),
    ("W", "alive", 8, 0x060, "gpa2", 0x08),
    ("W", "alive", 8, 0x080, "gpa3", 0x0C),
    ("W", "alive", 7, 0x0A0, "gpa4", 0x24),
    ("G", "off", 8, 0x000, "gph0", 0x00),
    ("G", "off", 7, 0x020, "gph1", 0x04),
    ("G", "off", 4, 0x040, "gph3", 0x08),
    ("G", "off", 3, 0x000, "gph2", 0x00),
    ("G", "4", 3, 0x000, "gpi0", 0x00),
    ("G", "4", 8, 0x020, "gpi1", 0x04),
    ("G", "off", 8, 0x000, "gpj1", 0x00),
    ("G", "off", 7, 0x020, "gpj0", 0x04),
    ("G", "off", 2, 0x000, "gpb2", 0x00),
    ("G", "off", 8, 0x000, "gpd0", 0x00),
    ("G", "off", 8, 0x020, "gpd1", 0x04),
    ("G", "off", 4, 0x040, "gpd2", 0x08),
    ("G", "off", 5, 0x060, "gpd3", 0x0C),
    ("G", "off", 4, 0x080, "gpb1", 0x10),
    ("G", "off", 8, 0x0A0, "gpe7", 0x14),
    ("G", "off", 8, 0x0C0, "gpf1", 0x18),
    ("G", "off", 3, 0x000, "gpb0", 0x00),
    ("G", "off", 5, 0x020, "gpc0", 0x04),
    ("G", "off", 5, 0x040, "gpc1", 0x08),
    ("G", "off", 8, 0x060, "gpc2", 0x0C),
    ("G", "off", 8, 0x080, "gpc3", 0x10),
    ("G", "off", 4, 0x0A0, "gpk0", 0x14),
    ("G", "off", 8, 0x0C0, "gpe5", 0x18),
    ("G", "off", 8, 0x0E0, "gpe6", 0x1C),
    ("G", "off", 8, 0x100, "gpe2", 0x20),
    ("G", "off", 8, 0x120, "gpe3", 0x24),
    ("G", "off", 8, 0x140, "gpe4", 0x28),
    ("G", "off", 4, 0x160, "gpf0", 0x2C),
    ("G", "off", 8, 0x180, "gpe1", 0x30),
    ("G", "off", 2, 0x1A0, "gpg0", 0x34),
]

PINCTRL_C = r'''// SPDX-License-Identifier: GPL-2.0+
/* Exynos8895 pin-bank data ported onto the Linux 4.19 Samsung core. */
#include "pinctrl-samsung.h"
#include "pinctrl-exynos.h"

static const struct samsung_pin_bank_type bank_type_off = {
    .fld_width = { 4, 1, 2, 2, 2, 2, },
    .reg_offset = { 0x00, 0x04, 0x08, 0x0c, 0x10, 0x14, },
};

static const struct samsung_pin_bank_type bank_type_alive = {
    .fld_width = { 4, 1, 2, 2, },
    .reg_offset = { 0x00, 0x04, 0x08, 0x0c, },
};

static const struct samsung_pin_bank_type exynos8895_bank_type_fsys0 = {
    .fld_width = { 4, 1, 2, 3, 2, 2, },
    .reg_offset = { 0x00, 0x04, 0x08, 0x0c, 0x10, 0x14, },
};

#define EXYNOS8895_PIN_BANK_EINTG_FSYS0(pins, reg, id, offs) \
    { .type = &exynos8895_bank_type_fsys0, .pctl_offset = reg, \
      .nr_pins = pins, .eint_type = EINT_TYPE_GPIO, \
      .eint_offset = offs, .name = id }

static const struct samsung_pin_bank_data exynos8895_pin_banks0[] __initconst = {
    EXYNOS_PIN_BANK_EINTW(6, 0x000, "etc1", 0x20),
    EXYNOS_PIN_BANK_EINTW(8, 0x020, "gpa0", 0x00),
    EXYNOS_PIN_BANK_EINTW(8, 0x040, "gpa1", 0x04),
    EXYNOS_PIN_BANK_EINTW(8, 0x060, "gpa2", 0x08),
    EXYNOS_PIN_BANK_EINTW(8, 0x080, "gpa3", 0x0c),
    EXYNOS_PIN_BANK_EINTW(7, 0x0a0, "gpa4", 0x24),
};

static const struct samsung_pin_bank_data exynos8895_pin_banks1[] __initconst = {
    EXYNOS_PIN_BANK_EINTG(8, 0x000, "gph0", 0x00),
    EXYNOS_PIN_BANK_EINTG(7, 0x020, "gph1", 0x04),
    EXYNOS_PIN_BANK_EINTG(4, 0x040, "gph3", 0x08),
};

static const struct samsung_pin_bank_data exynos8895_pin_banks2[] __initconst = {
    EXYNOS_PIN_BANK_EINTG(3, 0x000, "gph2", 0x00),
};

static const struct samsung_pin_bank_data exynos8895_pin_banks3[] __initconst = {
    EXYNOS8895_PIN_BANK_EINTG_FSYS0(3, 0x000, "gpi0", 0x00),
    EXYNOS8895_PIN_BANK_EINTG_FSYS0(8, 0x020, "gpi1", 0x04),
};

static const struct samsung_pin_bank_data exynos8895_pin_banks4[] __initconst = {
    EXYNOS_PIN_BANK_EINTG(8, 0x000, "gpj1", 0x00),
    EXYNOS_PIN_BANK_EINTG(7, 0x020, "gpj0", 0x04),
};

static const struct samsung_pin_bank_data exynos8895_pin_banks5[] __initconst = {
    EXYNOS_PIN_BANK_EINTG(2, 0x000, "gpb2", 0x00),
};

static const struct samsung_pin_bank_data exynos8895_pin_banks6[] __initconst = {
    EXYNOS_PIN_BANK_EINTG(8, 0x000, "gpd0", 0x00),
    EXYNOS_PIN_BANK_EINTG(8, 0x020, "gpd1", 0x04),
    EXYNOS_PIN_BANK_EINTG(4, 0x040, "gpd2", 0x08),
    EXYNOS_PIN_BANK_EINTG(5, 0x060, "gpd3", 0x0c),
    EXYNOS_PIN_BANK_EINTG(4, 0x080, "gpb1", 0x10),
    EXYNOS_PIN_BANK_EINTG(8, 0x0a0, "gpe7", 0x14),
    EXYNOS_PIN_BANK_EINTG(8, 0x0c0, "gpf1", 0x18),
};

static const struct samsung_pin_bank_data exynos8895_pin_banks7[] __initconst = {
    EXYNOS_PIN_BANK_EINTG(3, 0x000, "gpb0", 0x00),
    EXYNOS_PIN_BANK_EINTG(5, 0x020, "gpc0", 0x04),
    EXYNOS_PIN_BANK_EINTG(5, 0x040, "gpc1", 0x08),
    EXYNOS_PIN_BANK_EINTG(8, 0x060, "gpc2", 0x0c),
    EXYNOS_PIN_BANK_EINTG(8, 0x080, "gpc3", 0x10),
    EXYNOS_PIN_BANK_EINTG(4, 0x0a0, "gpk0", 0x14),
    EXYNOS_PIN_BANK_EINTG(8, 0x0c0, "gpe5", 0x18),
    EXYNOS_PIN_BANK_EINTG(8, 0x0e0, "gpe6", 0x1c),
    EXYNOS_PIN_BANK_EINTG(8, 0x100, "gpe2", 0x20),
    EXYNOS_PIN_BANK_EINTG(8, 0x120, "gpe3", 0x24),
    EXYNOS_PIN_BANK_EINTG(8, 0x140, "gpe4", 0x28),
    EXYNOS_PIN_BANK_EINTG(4, 0x160, "gpf0", 0x2c),
    EXYNOS_PIN_BANK_EINTG(8, 0x180, "gpe1", 0x30),
    EXYNOS_PIN_BANK_EINTG(2, 0x1a0, "gpg0", 0x34),
};

static const struct samsung_pin_ctrl exynos8895_pin_ctrl[] __initconst = {
    { .pin_banks = exynos8895_pin_banks0,
      .nr_banks = ARRAY_SIZE(exynos8895_pin_banks0),
      .eint_wkup_init = exynos_eint_wkup_init,
      .suspend = exynos_pinctrl_suspend,
      .resume = exynos_pinctrl_resume },
    { .pin_banks = exynos8895_pin_banks1,
      .nr_banks = ARRAY_SIZE(exynos8895_pin_banks1) },
    { .pin_banks = exynos8895_pin_banks2,
      .nr_banks = ARRAY_SIZE(exynos8895_pin_banks2),
      .eint_gpio_init = exynos_eint_gpio_init },
    { .pin_banks = exynos8895_pin_banks3,
      .nr_banks = ARRAY_SIZE(exynos8895_pin_banks3),
      .eint_gpio_init = exynos_eint_gpio_init,
      .suspend = exynos_pinctrl_suspend,
      .resume = exynos_pinctrl_resume },
    { .pin_banks = exynos8895_pin_banks4,
      .nr_banks = ARRAY_SIZE(exynos8895_pin_banks4),
      .eint_gpio_init = exynos_eint_gpio_init,
      .suspend = exynos_pinctrl_suspend,
      .resume = exynos_pinctrl_resume },
    { .pin_banks = exynos8895_pin_banks5,
      .nr_banks = ARRAY_SIZE(exynos8895_pin_banks5),
      .eint_gpio_init = exynos_eint_gpio_init,
      .suspend = exynos_pinctrl_suspend,
      .resume = exynos_pinctrl_resume },
    { .pin_banks = exynos8895_pin_banks6,
      .nr_banks = ARRAY_SIZE(exynos8895_pin_banks6),
      .eint_gpio_init = exynos_eint_gpio_init,
      .suspend = exynos_pinctrl_suspend,
      .resume = exynos_pinctrl_resume },
    { .pin_banks = exynos8895_pin_banks7,
      .nr_banks = ARRAY_SIZE(exynos8895_pin_banks7),
      .eint_gpio_init = exynos_eint_gpio_init,
      .suspend = exynos_pinctrl_suspend,
      .resume = exynos_pinctrl_resume },
};

const struct samsung_pinctrl_of_match_data exynos8895_of_data __initconst = {
    .ctrl = exynos8895_pin_ctrl,
    .num_ctrl = ARRAY_SIZE(exynos8895_pin_ctrl),
};
'''


def git_head(path: Path) -> str | None:
    if not (path / ".git").exists():
        return None
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
    ).strip()


def verify_vendor(vendor_root: Path) -> None:
    head = git_head(vendor_root)
    if head and head != EXPECTED_VENDOR_COMMIT:
        raise SystemExit(
            f"vendor commit mismatch: expected {EXPECTED_VENDOR_COMMIT}, got {head}"
        )

    source = vendor_root / "drivers/pinctrl/samsung/pinctrl-exynos.c"
    text = source.read_text()
    start = text.index("/* pin banks of exynos8895 pin-controller 0")
    end = text.index("#ifdef CONFIG_SEC_GPIO_DVS", start)
    block = text[start:end]
    found = []
    pattern = re.compile(
        r"EXYNOS8_PIN_BANK_EINT([WG])\(bank_type_(alive|off|4),\s*"
        r"(\d+),\s*(0x[0-9A-Fa-f]+),\s*\"([^\"]+)\",\s*"
        r"(0x[0-9A-Fa-f]+)\)"
    )
    for match in pattern.finditer(block):
        found.append(
            (
                match.group(1),
                match.group(2),
                int(match.group(3)),
                int(match.group(4), 16),
                match.group(5),
                int(match.group(6), 16),
            )
        )
    if found != EXPECTED_BANKS:
        raise SystemExit(f"pinned Exynos8895 bank table mismatch: {found!r}")


def patch_once(path: Path, marker: str, replacement: str) -> None:
    text = path.read_text()
    if replacement in text:
        return
    if marker not in text:
        raise SystemExit(f"patch marker not found in {path}: {marker}")
    path.write_text(text.replace(marker, replacement, 1))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if len(sys.argv) not in (2, 3):
        raise SystemExit(
            "usage: apply_exynos8895_pinctrl.py <pinned-vendor-tree> [manifest]"
        )
    vendor_root = Path(sys.argv[1])
    manifest = Path(sys.argv[2]) if len(sys.argv) == 3 else Path(
        "exynos8895-pinctrl-import.SHA256SUMS"
    )

    verify_vendor(vendor_root)

    generated = Path("drivers/pinctrl/samsung/pinctrl-exynos8895.c")
    generated.write_text(PINCTRL_C)

    header = Path("drivers/pinctrl/samsung/pinctrl-samsung.h")
    patch_once(
        header,
        "extern const struct samsung_pinctrl_of_match_data exynos7_of_data;",
        "extern const struct samsung_pinctrl_of_match_data exynos8895_of_data;\n"
        "extern const struct samsung_pinctrl_of_match_data exynos7_of_data;",
    )

    core = Path("drivers/pinctrl/samsung/pinctrl-samsung.c")
    marker = (
        '{ .compatible = "samsung,exynos7-pinctrl",\n'
        "\t\t.data = &exynos7_of_data },"
    )
    replacement = (
        '{ .compatible = "samsung,exynos8895-pinctrl",\n'
        "\t\t.data = &exynos8895_of_data },\n\t"
        + marker
    )
    patch_once(core, marker, replacement)

    makefile = Path("drivers/pinctrl/samsung/Makefile")
    text = makefile.read_text()
    if "pinctrl-exynos8895.o" not in text:
        if not text.endswith("\n"):
            text += "\n"
        text += (
            "\n# ALice Exynos8895 Linux 4.19 bring-up\n"
            "obj-y += pinctrl-exynos8895.o\n"
        )
        makefile.write_text(text)

    files = [generated, header, core, makefile]
    manifest.write_text("".join(f"{sha256(path)}  {path}\n" for path in files))
    Path("exynos8895-pinctrl-import.files").write_text(
        "".join(f"{path}\n" for path in files)
    )
    print("Exynos8895 pinctrl import prepared: 8 controllers, 36 banks")


if __name__ == "__main__":
    main()
