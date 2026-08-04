#!/usr/bin/env bash
set -euo pipefail

usage() {
    echo "Usage: bash $0 <pinned-exynos8895-4.4-tree> [manifest-output]" >&2
    exit 2
}

vendor_root=${1:-}
manifest=${2:-exynos8895-clock-cal-import.SHA256SUMS}
expected_vendor_commit=dcdaf6878e7f9497e1d90e25980decfa5d684f74

[[ -n "$vendor_root" ]] || usage
[[ -d "$vendor_root" ]] || { echo "Missing vendor tree: $vendor_root" >&2; exit 1; }
[[ -f Makefile && -d drivers && -d include ]] || {
    echo "Run from the Linux 4.19 source root" >&2
    exit 1
}

if [[ -d "$vendor_root/.git" ]]; then
    actual_commit=$(git -C "$vendor_root" rev-parse HEAD)
    [[ "$actual_commit" == "$expected_vendor_commit" ]] || {
        echo "Vendor commit mismatch: expected $expected_vendor_commit, got $actual_commit" >&2
        exit 1
    }
fi

copy_file() {
    local relative=$1
    mkdir -p "$(dirname "$relative")"
    cp -a "$vendor_root/$relative" "$relative"
}

copy_file drivers/clk/samsung/clk-exynos8895.c
copy_file drivers/clk/samsung/composite.c
copy_file drivers/clk/samsung/composite.h
copy_file include/linux/exynos-ss.h
copy_file include/soc/samsung/cal-if.h
copy_file include/soc/samsung/ect_parser.h
copy_file include/soc/samsung/exynos-pmu.h

rm -rf drivers/soc/samsung/cal-if
cp -a "$vendor_root/drivers/soc/samsung/cal-if" drivers/soc/samsung/

cat > drivers/soc/samsung/cal-if/exynos8895/Makefile <<'EOF'
obj-y += cal_data.o
EOF

python3 - <<'PY'
from pathlib import Path

snapshot = Path('include/linux/exynos-ss.h')
text = snapshot.read_text()
text = text.replace(
    '#define exynos_ss_clk(a,b,c)\t',
    '#define exynos_ss_clk(a,b,c,d)\t',
)
if '#define exynos_ss_pmu(a,b,c) do { } while (0)' not in text:
    text += '''\n#ifndef CONFIG_EXYNOS_SNAPSHOT
#ifndef exynos_ss_pmu
#define exynos_ss_pmu(a,b,c) do { } while (0)
#endif
#endif
'''
snapshot.write_text(text)

acpm = Path('drivers/soc/samsung/cal-if/acpm_dvfs.h')
text = acpm.read_text()
text = text.replace(
    'static inline int exynos_acpm_set_volt_margin(unsigned int id, int volt);\n{',
    'static inline int exynos_acpm_set_volt_margin(unsigned int id, int volt)\n{',
)
text = text.replace(
    'static inline int exynos_acpm_set_cold_temp(unsigned int id, bool is_cold_temp);\n{',
    'static inline int exynos_acpm_set_cold_temp(unsigned int id, bool is_cold_temp)\n{',
)
acpm.write_text(text)
PY

cat > drivers/soc/samsung/exynos8895-pmu-compat.c <<'EOF'
// SPDX-License-Identifier: GPL-2.0
#include <linux/err.h>
#include <linux/regmap.h>
#include <linux/soc/samsung/exynos-pmu.h>
#include <soc/samsung/exynos-pmu.h>

static struct regmap *alice_exynos8895_pmu_regmap(void)
{
    static struct regmap *map;

    if (!map)
        map = exynos_get_pmu_regmap();
    return map;
}

int exynos_pmu_read(unsigned int offset, unsigned int *val)
{
    struct regmap *map = alice_exynos8895_pmu_regmap();

    if (IS_ERR(map))
        return PTR_ERR(map);
    return regmap_read(map, offset, val);
}

int exynos_pmu_write(unsigned int offset, unsigned int val)
{
    struct regmap *map = alice_exynos8895_pmu_regmap();

    if (IS_ERR(map))
        return PTR_ERR(map);
    return regmap_write(map, offset, val);
}

int exynos_pmu_update(unsigned int offset, unsigned int mask,
                      unsigned int val)
{
    struct regmap *map = alice_exynos8895_pmu_regmap();

    if (IS_ERR(map))
        return PTR_ERR(map);
    return regmap_update_bits(map, offset, mask, val);
}
EOF

python3 - <<'PY'
from pathlib import Path

def append_once(path: str, marker: str, block: str) -> None:
    p = Path(path)
    text = p.read_text()
    if marker not in text:
        if not text.endswith('\n'):
            text += '\n'
        text += block
        p.write_text(text)

append_once(
    'drivers/clk/samsung/Makefile',
    'obj-y += composite.o clk-exynos8895.o',
    '\n# ALice Exynos8895 Linux 4.19 bring-up\nobj-y += composite.o clk-exynos8895.o\n',
)
append_once(
    'drivers/soc/samsung/Makefile',
    'obj-y += exynos8895-pmu-compat.o cal-if/',
    '\n# ALice Exynos8895 Linux 4.19 bring-up\nobj-y += exynos8895-pmu-compat.o cal-if/\n',
)
PY

cat > drivers/soc/samsung/cal-if/Makefile <<'EOF'
obj-y += cal-if.o
obj-y += pmucal_system.o pmucal_local.o pmucal_cpu.o pmucal_rae.o
obj-y += cmucal.o ra.o vclk.o pll_spec.o
obj-y += exynos8895/cal_data.o
subdir-ccflags-y += -Wno-sizeof-pointer-div
EOF

{
    echo drivers/clk/samsung/clk-exynos8895.c
    echo drivers/clk/samsung/composite.c
    echo drivers/clk/samsung/composite.h
    echo drivers/soc/samsung/exynos8895-pmu-compat.c
    echo include/linux/exynos-ss.h
    echo include/soc/samsung/cal-if.h
    echo include/soc/samsung/ect_parser.h
    echo include/soc/samsung/exynos-pmu.h
    find drivers/soc/samsung/cal-if -type f | sort
} | sort -u > exynos8895-clock-cal-import.files

sha256sum $(cat exynos8895-clock-cal-import.files) > "$manifest"

cat <<EOF
Exynos8895 clock/CAL import prepared.
Vendor commit: $expected_vendor_commit
Manifest: $manifest
Runtime status: unvalidated; physical boot not tested.
EOF
