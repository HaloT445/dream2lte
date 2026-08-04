#!/usr/bin/env python3
"""Verify that the Exynos8895 vendor clock implementation is isolated."""

from pathlib import Path
import re
import sys

VENDOR_C = Path("drivers/clk/samsung/composite.c")
VENDOR_H = Path("drivers/clk/samsung/composite.h")
PROVIDER = Path("drivers/clk/samsung/clk-exynos8895.c")
CORE_CLK = Path("drivers/clk/samsung/clk.c")
CORE_PLL = Path("drivers/clk/samsung/clk-pll.c")

GLOBAL_RENAMES = {
    "samsung_clk_save": "exynos8895_vendor_clk_save",
    "samsung_clk_restore": "exynos8895_vendor_clk_restore",
    "samsung_clk_alloc_reg_dump": "exynos8895_vendor_clk_alloc_reg_dump",
    "samsung_clk_init": "exynos8895_vendor_clk_init",
    "samsung_clk_of_add_provider": "exynos8895_vendor_clk_of_add_provider",
}

# These functions are file-local in both implementations. Renaming them is not
# required by the linker, but it makes the vendor implementation unambiguous
# during auditing and future maintenance.
STATIC_RENAMES = {
    "samsung_pll2650x_recalc_rate":
        "exynos8895_vendor_pll2650x_recalc_rate",
    "samsung_pll2650x_set_rate":
        "exynos8895_vendor_pll2650x_set_rate",
    "samsung_pll_round_rate": "exynos8895_vendor_pll_round_rate",
}

RENAMES = {**GLOBAL_RENAMES, **STATIC_RENAMES}


def require_file(path: Path) -> str:
    if not path.is_file():
        raise SystemExit(f"missing required file: {path}")
    return path.read_text()


def definition_present(text: str, symbol: str) -> bool:
    pattern = (
        rf"(?m)^[^;\n]*\b{re.escape(symbol)}\s*\([^;]*\)\s*\n\s*\{{"
    )
    return re.search(pattern, text) is not None


vendor_c = require_file(VENDOR_C)
vendor_h = require_file(VENDOR_H)
provider = require_file(PROVIDER)
core_clk = require_file(CORE_CLK)
core_pll = require_file(CORE_PLL)

errors: list[str] = []

for original, namespaced in RENAMES.items():
    if definition_present(vendor_c, original):
        errors.append(f"vendor collision remains: {original}")
    if not definition_present(vendor_c, namespaced):
        errors.append(f"missing namespaced vendor definition: {namespaced}")

for namespaced in GLOBAL_RENAMES.values():
    if namespaced not in vendor_h:
        errors.append(f"missing namespaced vendor declaration: {namespaced}")

for symbol in GLOBAL_RENAMES:
    if not definition_present(core_clk, symbol):
        errors.append(f"Linux 4.19 core clock symbol was removed: {symbol}")

for symbol in STATIC_RENAMES:
    if not definition_present(core_pll, symbol):
        errors.append(f"Linux 4.19 core PLL implementation was removed: {symbol}")

if "exynos8895_vendor_clk_init(" not in provider:
    errors.append("Exynos8895 provider does not call namespaced init")
if "exynos8895_vendor_clk_of_add_provider(" not in provider:
    errors.append("Exynos8895 provider does not call namespaced OF provider")
if "samsung_clk_init(" in provider:
    errors.append("Exynos8895 provider still calls shared samsung_clk_init")
if "samsung_clk_of_add_provider(" in provider:
    errors.append("Exynos8895 provider still calls shared OF provider")

if errors:
    print("Exynos8895 clock namespace audit: FAIL", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)

print(
    "Exynos8895 clock namespace audit: PASS "
    f"({len(GLOBAL_RENAMES)} global and {len(STATIC_RENAMES)} static names isolated)"
)
