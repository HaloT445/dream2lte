#!/usr/bin/env python3
"""Apply source-local build flags for the Exynos8895 clock/CAL port."""

from pathlib import Path

CLOCK_FLAGS = (
    "-DCONFIG_CAL_IF -DCONFIG_PMUCAL -DCONFIG_CMUCAL "
    "-DCONFIG_SOC_EXYNOS8895 -DCLK_IS_ROOT=0"
)
CAL_FLAGS = (
    "-DCONFIG_CAL_IF -DCONFIG_PMUCAL -DCONFIG_CMUCAL "
    "-DCONFIG_SOC_EXYNOS8895"
)


def append_once(path: Path, marker: str, block: str) -> None:
    text = path.read_text()
    if marker not in text:
        if not text.endswith("\n"):
            text += "\n"
        text += block
        path.write_text(text)


clock_makefile = Path("drivers/clk/samsung/Makefile")
append_once(
    clock_makefile,
    "CFLAGS_clk-exynos8895.o += -DCONFIG_CAL_IF",
    (
        "\n# Exynos8895 vendor clock/CAL compatibility flags\n"
        f"CFLAGS_clk-exynos8895.o += {CLOCK_FLAGS}\n"
        f"CFLAGS_composite.o += {CLOCK_FLAGS}\n"
    ),
)

cal_makefile = Path("drivers/soc/samsung/cal-if/Makefile")
text = cal_makefile.read_text()
marker = "subdir-ccflags-y += -DCONFIG_CAL_IF"
if marker not in text:
    if not text.endswith("\n"):
        text += "\n"
    text += (
        "# Exynos8895 CAL compatibility flags\n"
        f"subdir-ccflags-y += {CAL_FLAGS}\n"
    )
    cal_makefile.write_text(text)

print("Exynos8895 source-local clock/CAL build flags applied")
