# dream2lte Linux 5.15 direct bring-up

## Decision

The only active porting path is a direct migration from the locked Linux
4.4.302 dream2lte baseline to Android Common Linux 5.15.

Linux 4.19 is not a parent, patch donor, ABI bridge, build input or runtime
dependency. Its old branches and artifacts are retained as archived audit
evidence only and must never be merged into the active 5.15 path.

## Locked baselines

- Device/vendor donor: Linux 4.4.302
- Donor repository: `boloaimer/exynos-8895`
- Donor commit: `dcdaf6878e7f9497e1d90e25980decfa5d684f74`
- Destination family: official Android Common Kernel 5.15
- Destination branch: `android14-5.15`
- Destination commit: `b10e5e5b5c5e01d49829aec34b65a0d717d6f2f5`
- Destination tree: `7c3cd26c765b741df608a8b81cc6b93f1240fa36`
- Coordination branch: `port/linux-5.15-bringup`
- Full source target: `port/linux-5.15-source`
- Rollback baseline branch: `main`

## Direct donor paths already identified

```text
arch/arm64/boot/dts/exynos/exynos8895-dream2lte_eur_open_10.dts
arch/arm64/boot/dts/exynos/exynos8895-dream2lte_common.dtsi
arch/arm64/boot/dts/exynos/exynos8895.dtsi
arch/arm64/boot/dts/exynos/exynos8895-pinctrl.dtsi
arch/arm64/boot/dts/exynos/exynos8895-pm-domains.dtsi
include/dt-bindings/clock/exynos8895.h
drivers/clk/samsung/clk-exynos8895.c
drivers/pinctrl/samsung/pinctrl-exynos.c
drivers/soc/samsung/cal-if/exynos8895/
drivers/scsi/ufs/ufs-exynos.c
drivers/scsi/ufs/ufs-exynos.h
arch/arm64/configs/exynos8895-dream2lte_defconfig
arch/arm64/configs/alice_dream2lte_susfs_defconfig
```

The Linux 4.4 defconfigs are translation references only. They must not be
copied over `gki_defconfig` as-is.

## Linux 5.15 destination and output paths

```text
arch/arm64/configs/gki_defconfig
build.config.gki.aarch64
arch/arm64/boot/dts/exynos/
drivers/clk/samsung/
drivers/pinctrl/samsung/
drivers/pmdomain/samsung/
drivers/soc/samsung/
drivers/scsi/ufs/ufs-exynos.c
drivers/phy/samsung/
drivers/android/
fs/erofs/
fs/incfs/

out/dream2lte-5.15/arch/arm64/boot/Image
out/dream2lte-5.15/arch/arm64/boot/dts/exynos/exynos8895-dream2lte*.dtb
out/dream2lte-5.15/arch/arm64/boot/dts/exynos/*.dtbo
out/dream2lte-5.15/**/*.ko
out/dream2lte-5.15/modules.order
out/dream2lte-5.15/modules.builtin*
```

For the locked legacy S8 Plus boot layout, the expected kernel replacement
component is `boot.img::kernel`. The actual One UI 8 package must still be
scanned for `vendor_boot.img`, `init_boot.img` and `dtbo.img` before repacking.

## Non-negotiable constraints

1. Do not modify or force-update `main`.
2. Preserve the original 4.4 boot image, ramdisk, DT/DTBO and rollback path.
3. Do not copy generic Linux 4.4 core implementations into Linux 5.15.
4. Keep KernelSU, SUSFS, overclocking and voltage changes disabled during first-boot bring-up.
5. Use BOOT_SAFE policy first: domains always-on, conservative UFS link, no runtime suspend until physical logs exist.
6. Never claim physical boot, storage integrity, TEE/Keymaster, banking compatibility or One UI 8 readiness from compile evidence alone.
7. Every boot-critical phase requires a pinned source commit, checksum manifest, CI log and explicit rollback note.

## Bring-up order

1. Pin and compile a clean Android Common 5.15 arm64/GKI baseline.
2. Import the exact 26-file dream2lte DTS dependency closure directly from 4.4.302 and compile the DTB.
3. Port interrupt controller, timer, PSCI, PMU and early-console prerequisites.
4. Port Exynos8895 clock/CAL/PMUCAL without replacing the Linux 5.15 common-clock core.
5. Extract Exynos8895 bank tables from the shared 4.4 `pinctrl-exynos.c` and adapt them to the Linux 5.15 Samsung pinctrl framework.
6. Register BOOT_SAFE generic power domains with runtime power-off blocked.
7. Use the Linux 5.15 Exynos UFS host/PHY as the API baseline; transfer only Exynos8895 resource data and calibration from 4.4.302.
8. Produce an `Image + DTB` host-link artifact.
9. Repack a separate BOOT_SAFE test image with the original ramdisk and complete rollback package.
10. Only after physical boot/storage evidence: display, input, GPU, modem, Wi-Fi/Bluetooth, audio, camera, charging, thermal and suspend.
11. KernelSU/SUSFS are considered only after stock-voltage boot stability and banking/TEE validation.

## Current validation state

- Direct 4.4.302 -> 5.15 policy gate: PASS
- Linux 4.19 dependency: none
- Donor inventory and checksum gate: PASS
- Official Android Common 5.15 branch/commit: pinned
- Clean 5.15 arm64 Image compile: running
- Direct path map: pinctrl path corrected to shared `pinctrl-exynos.c`
- Direct 26-file dream2lte DTB compile probe: created
- Exynos8895 runtime driver port: not yet validated
- Physical boot: not tested
- One UI 8 boot: not tested
