#!/usr/bin/env python3
"""Backport the upstream Exynos UFS host and Samsung PHY to Linux 4.19.

The Linux 4.19 UFS core is preserved. Only the Exynos host extension and
Samsung generic PHY closure are imported from the pinned Linux 5.15 source.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

EXPECTED_UPSTREAM_COMMIT = "8bb7eca972ad531c9b149c0a51ab43a417385813"

COMPAT_HEADER = r'''/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef _UFS_EXYNOS_4_19_COMPAT_H_
#define _UFS_EXYNOS_4_19_COMPAT_H_

/* UniPro attributes used by the upstream Exynos host but absent in 4.19. */
#ifndef RX_HS_G1_SYNC_LENGTH_CAP
#define RX_HS_G1_SYNC_LENGTH_CAP        0x008B
#define RX_HS_G1_PREP_LENGTH_CAP        0x008C
#define RX_HS_G2_SYNC_LENGTH_CAP        0x0094
#define RX_HS_G3_SYNC_LENGTH_CAP        0x0095
#define RX_HS_G2_PREP_LENGTH_CAP        0x0096
#define RX_HS_G3_PREP_LENGTH_CAP        0x0097
#define RX_ADV_GRANULARITY_CAP          0x0098
#define RX_MIN_ACTIVATETIME_CAP         0x008F
#define RX_HIBERN8TIME_CAP              0x0092
#define RX_ADV_HIBERN8TIME_CAP          0x0099
#define RX_ADV_MIN_ACTIVATETIME_CAP     0x009A
#define RX_ADV_FINE_GRAN_STEP(x)        ((((x) & 0x3) << 1) | 0x1)
#define SYNC_LEN_FINE(x)                ((x) & 0x3F)
#define SYNC_LEN_COARSE(x)              ((1 << 6) | ((x) & 0x3F))
#define PREP_LEN(x)                     ((x) & 0xF)
#endif

#ifndef CPORT_DEF_FLAGS
#define E2EFC_OFF                       (0 << 0)
#define CSD_N_OFF                       (1 << 1)
#define CSV_N_OFF                       (1 << 2)
#define CPORT_DEF_FLAGS                 (CSV_N_OFF | CSD_N_OFF | E2EFC_OFF)
#define CPORT_IDLE                      0
#define CPORT_CONNECTED                 1
#endif

/* Newer core quirks have no 4.19 implementation; keep them compile-time no-op. */
#ifndef UFSHCD_QUIRK_BROKEN_OCS_FATAL_ERROR
#define UFSHCD_QUIRK_BROKEN_OCS_FATAL_ERROR             0
#endif
#ifndef UFSHCI_QUIRK_SKIP_MANUAL_WB_FLUSH_CTRL
#define UFSHCI_QUIRK_SKIP_MANUAL_WB_FLUSH_CTRL           0
#endif
#ifndef UFSHCD_QUIRK_SKIP_DEF_UNIPRO_TIMEOUT_SETTING
#define UFSHCD_QUIRK_SKIP_DEF_UNIPRO_TIMEOUT_SETTING     0
#endif
#ifndef UFSHCD_QUIRK_ALIGN_SG_WITH_PAGE_SIZE
#define UFSHCD_QUIRK_ALIGN_SG_WITH_PAGE_SIZE             0
#endif

#endif /* _UFS_EXYNOS_4_19_COMPAT_H_ */
'''

HOST_IOREMAP_HELPER = r'''
static void __iomem *alice_devm_platform_ioremap_resource_byname(
        struct platform_device *pdev, const char *name)
{
    struct resource *res;

    res = platform_get_resource_byname(pdev, IORESOURCE_MEM, name);
    if (!res)
        return ERR_PTR(-EINVAL);
    return devm_ioremap_resource(&pdev->dev, res);
}
'''

PHY_IOREMAP_HELPER = r'''
static void __iomem *alice_devm_platform_ioremap_resource_byname(
        struct platform_device *pdev, const char *name)
{
    struct resource *res;

    res = platform_get_resource_byname(pdev, IORESOURCE_MEM, name);
    if (!res)
        return ERR_PTR(-EINVAL);
    return devm_ioremap_resource(&pdev->dev, res);
}
'''

PRE_PWR_MODE = r'''static int exynos_ufs_pre_pwr_mode(struct ufs_hba *hba,
                struct ufs_pa_layer_attr *dev_max_params,
                struct ufs_pa_layer_attr *dev_req_params)
{
    struct exynos_ufs *ufs = ufshcd_get_variant(hba);
    struct phy *generic_phy = ufs->phy;

    if (!dev_max_params || !dev_req_params)
        return -EINVAL;

    /*
     * BOOT_SAFE negotiation for first physical bring-up. Preserve the device
     * mode but cap link training to two lanes and Gear 2 until UART/pstore and
     * storage stress evidence exists.
     */
    *dev_req_params = *dev_max_params;
    dev_req_params->gear_rx = min_t(u32, dev_req_params->gear_rx, 2);
    dev_req_params->gear_tx = min_t(u32, dev_req_params->gear_tx, 2);
    dev_req_params->lane_rx = min_t(u32, dev_req_params->lane_rx, 2);
    dev_req_params->lane_tx = min_t(u32, dev_req_params->lane_tx, 2);

    if (ufshcd_is_hs_mode(dev_req_params) &&
        dev_req_params->hs_rate != PA_HS_MODE_A &&
        dev_req_params->hs_rate != PA_HS_MODE_B)
        dev_req_params->hs_rate = PA_HS_MODE_B;

    if (ufs->drv_data->pre_pwr_change)
        ufs->drv_data->pre_pwr_change(ufs, dev_req_params);

    if (ufshcd_is_hs_mode(dev_req_params)) {
        exynos_ufs_config_sync_pattern_mask(ufs, dev_req_params);
        phy_calibrate(generic_phy);
    }

    ufshcd_dme_set(hba, UIC_ARG_MIB(DL_FC0PROTTIMEOUTVAL), 8064);
    ufshcd_dme_set(hba, UIC_ARG_MIB(DL_TC0REPLAYTIMEOUTVAL), 28224);
    ufshcd_dme_set(hba, UIC_ARG_MIB(DL_AFC0REQTIMEOUTVAL), 20160);

    return 0;
}

#define PWR_MODE_STR_LEN'''

PM_OPS = r'''static const struct dev_pm_ops exynos_ufs_pm_ops = {
    SET_SYSTEM_SLEEP_PM_OPS(ufshcd_pltfrm_suspend, ufshcd_pltfrm_resume)
    SET_RUNTIME_PM_OPS(ufshcd_pltfrm_runtime_suspend,
                       ufshcd_pltfrm_runtime_resume,
                       ufshcd_pltfrm_runtime_idle)
};'''


def git_head(path: Path) -> str | None:
    if not (path / ".git").exists():
        return None
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
    ).strip()


def require_replace(text: str, old: str, new: str, description: str) -> str:
    if old not in text:
        raise SystemExit(f"patch marker missing: {description}")
    return text.replace(old, new)


def copy(upstream: Path, relative: str) -> Path:
    source = upstream / relative
    target = Path(relative)
    if not source.is_file():
        raise SystemExit(f"missing pinned upstream file: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def patch_host(path: Path) -> None:
    text = path.read_text()
    text = require_replace(
        text,
        '#include "ufs-exynos.h"',
        '#include "ufs-exynos.h"\n#include "ufs-exynos-4.19-compat.h"',
        "Exynos compatibility include",
    )
    text = text.replace(
        "devm_platform_ioremap_resource_byname(",
        "alice_devm_platform_ioremap_resource_byname(",
    )
    marker = "static void exynos_ufs_ctrl_clkstop(struct exynos_ufs *ufs, bool en);\n"
    text = require_replace(
        text, marker, marker + HOST_IOREMAP_HELPER, "host ioremap helper"
    )
    text = text.replace("samsung,exynos7-ufs", "samsung,exynos8895-ufs")

    pattern = re.compile(
        r"static int exynos_ufs_pre_pwr_mode\(.*?\n\}\n\n"
        r"#define PWR_MODE_STR_LEN",
        re.S,
    )
    text, count = pattern.subn(PRE_PWR_MODE, text, count=1)
    if count != 1:
        raise SystemExit("failed to replace Exynos UFS power negotiation")

    pm_pattern = re.compile(
        r"static const struct dev_pm_ops exynos_ufs_pm_ops = \{.*?\n\};",
        re.S,
    )
    text, count = pm_pattern.subn(PM_OPS, text, count=1)
    if count != 1:
        raise SystemExit("failed to replace Exynos UFS PM operations")

    path.write_text(text)


def patch_phy(path: Path) -> None:
    text = path.read_text()
    text = text.replace(
        "devm_platform_ioremap_resource_byname(",
        "alice_devm_platform_ioremap_resource_byname(",
    )
    marker = "#define PHY_DEF_LANE_CNT\t1\n"
    text = require_replace(
        text, marker, marker + PHY_IOREMAP_HELPER, "PHY ioremap helper"
    )
    old = (
        "static int samsung_ufs_phy_set_mode(struct phy *generic_phy,\n"
        "\t\t\t\t    enum phy_mode mode, int submode)"
    )
    new = (
        "static int samsung_ufs_phy_set_mode(struct phy *generic_phy,\n"
        "\t\t\t\t    enum phy_mode mode)"
    )
    text = require_replace(text, old, new, "Linux 4.19 PHY set_mode ABI")
    path.write_text(text)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "usage: apply_exynos8895_ufs_upstream.py <pinned-linux-v5.15-tree>"
        )

    upstream = Path(sys.argv[1])
    head = git_head(upstream)
    if head and head != EXPECTED_UPSTREAM_COMMIT:
        raise SystemExit(
            f"upstream commit mismatch: expected {EXPECTED_UPSTREAM_COMMIT}, got {head}"
        )

    files = [
        copy(upstream, "drivers/scsi/ufs/ufs-exynos.c"),
        copy(upstream, "drivers/scsi/ufs/ufs-exynos.h"),
        copy(upstream, "drivers/phy/samsung/phy-samsung-ufs.c"),
        copy(upstream, "drivers/phy/samsung/phy-samsung-ufs.h"),
        copy(upstream, "drivers/phy/samsung/phy-exynos7-ufs.c"),
    ]

    compat = Path("drivers/scsi/ufs/ufs-exynos-4.19-compat.h")
    compat.write_text(COMPAT_HEADER)
    files.append(compat)

    patch_host(Path("drivers/scsi/ufs/ufs-exynos.c"))
    patch_phy(Path("drivers/phy/samsung/phy-samsung-ufs.c"))

    Path("exynos8895-ufs-upstream-import.files").write_text(
        "".join(f"{path}\n" for path in files)
    )
    print("Exynos8895 upstream UFS host/PHY backport prepared")
    print("BOOT_SAFE link cap: Gear 2, two lanes")
    print("Linux 4.19 ufshcd core preserved")


if __name__ == "__main__":
    main()
