# dream2lte Linux 5.15 direct bring-up

## Decision

The active porting path is now a direct migration from the locked Linux 4.4.302 dream2lte baseline to Linux 5.15.

The experimental Linux 4.19 branches and their build evidence are retained for audit and rollback, but they are no longer the active development path.

## Baselines

- Device/vendor baseline: `main` (Linux 4.4.302, dream2lte)
- New coordination branch: `port/linux-5.15-bringup`
- Planned materialized source branch: `port/linux-5.15-source`
- Upstream candidate family: official Android Common Kernel 5.15
- Exact Android Common branch and commit must be discovered and pinned by CI before source materialization.

## Non-negotiable constraints

1. Do not modify or force-update `main`.
2. Preserve the original 4.4 boot image, ramdisk, DT/DTBO and rollback path.
3. Keep KernelSU, SUSFS, overclocking and voltage changes disabled during first-boot bring-up.
4. Use BOOT_SAFE policy first: domains always-on, conservative UFS link, no runtime suspend until physical logs exist.
5. Never claim physical boot, storage integrity, TEE/Keymaster, banking compatibility or One UI 8 readiness from compile evidence alone.
6. Every boot-critical phase requires a pinned source commit, checksum manifest, CI log and explicit rollback note.

## Bring-up order

1. Pin and compile a clean Android Common 5.15 arm64/GKI baseline.
2. Import the Exynos8895 DTS and dt-bindings with a strict compatibility audit.
3. Port interrupt controller, timer, PSCI, PMU and early console prerequisites.
4. Port clock/CAL/PMUCAL without replacing the Linux 5.15 common-clock core.
5. Port pinctrl/EINT onto the Linux 5.15 Samsung framework.
6. Register BOOT_SAFE generic power domains with runtime power-off blocked.
7. Port Exynos UFS host and Samsung PHY while preserving the Linux 5.15 UFS core.
8. Produce an `Image + DTB` host-link artifact.
9. Repack a separate BOOT_SAFE test image with the original ramdisk and complete rollback package.
10. Only after physical boot/storage evidence: Android binder/vendor hooks, display, input, GPU, modem, Wi-Fi/Bluetooth, audio, camera, charging, thermal and suspend.

## Current validation state

- Linux 5.15 branch created: yes
- Official Android Common 5.15 branch pinned: pending CI discovery
- Clean 5.15 arm64 Image compile: pending
- Exynos8895 device port: not started on 5.15
- Physical boot: not tested
- One UI 8 boot: not tested
