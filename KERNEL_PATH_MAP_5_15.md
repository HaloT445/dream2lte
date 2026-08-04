# dream2lte Linux 5.15 kernel path map

## Active migration path

- Coordination and CI: `port/linux-5.15-bringup`
- Full source target: `port/linux-5.15-source`
- Locked rollback baseline: `main` — Linux 4.4.302
- Linux 4.19 path: archived evidence only; not an active dependency

## Source paths

| Purpose | Path |
|---|---|
| Kernel source root | repository root of `port/linux-5.15-source` |
| Version | `Makefile` |
| GKI defconfig | `arch/arm64/configs/gki_defconfig` |
| Android GKI build config | `build.config.gki.aarch64` |
| Common Android config | `build.config.common` |
| Planned device fragment | `arch/arm64/configs/dream2lte_gki.fragment` |
| ARM64 architecture | `arch/arm64/` |
| Exynos device-tree source | `arch/arm64/boot/dts/exynos/` |
| Exynos clock | `drivers/clk/samsung/` |
| Exynos pinctrl | `drivers/pinctrl/samsung/` |
| Samsung PMU/genpd | `drivers/soc/samsung/` and `drivers/pmdomain/samsung/` |
| Exynos UFS host | `drivers/ufs/host/ufs-exynos.c` on newer layouts, or the source tree's equivalent discovered by audit |
| Samsung UFS PHY | `drivers/phy/samsung/` |
| Android Binder | `drivers/android/` |
| EROFS | `fs/erofs/` |
| Incremental FS | `fs/incfs/` |

Do not copy Linux 4.4 core implementations such as `ufshcd.c`, generic IRQ core, generic clock core or generic pinctrl core into Linux 5.15. Only Exynos8895-specific data and glue may be ported after API adaptation.

## Build paths

The canonical out-of-tree output directory is:

```text
out/dream2lte-5.15/
```

Expected outputs:

```text
out/dream2lte-5.15/arch/arm64/boot/Image
out/dream2lte-5.15/arch/arm64/boot/dts/exynos/exynos8895-dream2lte*.dtb
out/dream2lte-5.15/arch/arm64/boot/dts/exynos/*.dtbo
out/dream2lte-5.15/modules.order
out/dream2lte-5.15/modules.builtin
out/dream2lte-5.15/modules.builtin.modinfo
out/dream2lte-5.15/**/*.ko
```

The first clean baseline uses:

```bash
make O=out/dream2lte-5.15 ARCH=arm64 LLVM=1 LLVM_IAS=1 gki_defconfig
make O=out/dream2lte-5.15 ARCH=arm64 LLVM=1 LLVM_IAS=1 -j2 Image
```

This only proves the Android Common baseline. It does not prove dream2lte support.

## One UI 8 firmware paths

The kernel binary is not stored as a normal file inside Android system/vendor partitions. It is packaged in a boot container.

Potential containers:

```text
boot.img
vendor_boot.img
init_boot.img
dtbo.img
AP_*.tar.md5
```

For the locked S8 Plus baseline, the boot image uses the legacy layout; the expected replacement target after unpacking is:

```text
boot.img::kernel
```

Depending on the One UI 8 port package, DTB or ramdisk content may still be moved or split. Therefore the exact target must be detected from the actual ROM package instead of assuming a modern GKI layout.

Run the read-only scanner:

```bash
bash scripts/port/discover_oneui8_kernel_paths.sh /path/to/unpacked-rom kernel-path-report
```

Recommended tools available in `PATH`:

```text
magiskboot
lz4
tar
file
sha256sum
```

The scanner outputs:

```text
kernel-path-report/KERNEL_PATH_REPORT.md
kernel-path-report/KERNEL_PATH_REPORT.tsv
```

## Boot-safe gate order

1. Android Common 5.15 clean `Image`
2. Exynos8895 DTS/DTB and interrupt topology
3. Clock and PMU
4. Pinctrl
5. BOOT_SAFE always-on power domains
6. UFS host and PHY at conservative link settings
7. Initramfs/boot command line and verified partition mounting
8. Display and input
9. Android vendor modules and One UI 8 userspace compatibility
10. TEE/Keymaster/banking validation
11. Thermal, charging and performance tuning
12. KernelSU/SUSFS only after stock boot stability

## Current restrictions

- No flashable 5.15 kernel is approved yet.
- No physical boot evidence exists yet.
- KernelSU, SUSFS, OC and voltage changes are disabled for initial bring-up.
- `main` Linux 4.4.302 remains the rollback source and must not be overwritten.
