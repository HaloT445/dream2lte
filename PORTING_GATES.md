# dream2lte Linux 4.19.325 porting gates

This document defines the required progression for the isolated Linux 4.19 bring-up. A later gate must not be treated as complete when an earlier gate is unresolved.

## Locked baseline

- Linux 4.4.302 baseline remains on `main`.
- Linux 4.19 work remains on isolated branches.
- KernelSU, SUSFS, overclocking and power tuning remain disabled during platform bring-up.

## Gate order

### Gate 0 — Android common ARM64 base

Status: PASS.

Requirements: pinned 4.19.325 source, reproducible generic ARM64 Image, build log and checksums.

### Gate 1 — dream2lte device tree

Status: PASS for host compilation only.

Requirements: exact DTS dependency closure, byte-for-byte verification, DTB build and checksum.

### Gate 2 — Android ABI and diagnostics configuration

Status: PASS for host compilation only.

Requirements: Binder, ASHMEM, SELinux, cgroups, namespaces, seccomp, Android filesystems/encryption, dm-verity, generic storage, Samsung UART and pstore configuration attestation; Image and DTB build.

### Gate 3 — Exynos8895 clock, CAL and PMUCAL

Status: object closure PASS; full Image linkage in progress.

Requirements before materialization:

- Samsung composite clock and Exynos8895 clock provider compile.
- CAL, CMUCAL, PMUCAL and platform data closure compile.
- Complete Phase-2 Image and DTB link without unresolved symbols.
- Compatibility changes recorded and checksumed.

Runtime clock rate, topology, PLL lock and power transition behavior remain unvalidated until physical boot logs exist.

### Gate 4 — pinctrl, PMU and power domains

Status: not started.

Required work:

- Convert eight Exynos8895 pin-controller instances into the Linux 4.19 `samsung_pinctrl_of_match_data` model.
- Register `samsung,exynos8895-pinctrl` without replacing newer common Samsung pinctrl code.
- Validate GPIO and wakeup-EINT bank ordering.
- Port `samsung,exynos-pd` integration against the verified CAL/PMUCAL layer.
- Keep debug-only secgpio and vendor PM tracing disabled initially.

### Gate 5 — boot storage

Status: not started.

Required work:

- Port Exynos UFS host and PHY/tuning support.
- Resolve PMU, clock, pinctrl, regulator and sysreg dependencies.
- Produce UFS initialization evidence and mount Android partitions read-only before enabling write-path validation.

### Gate 6 — minimum interactive boot

Status: not started.

Required work: display, framebuffer/DRM path, touchscreen/input, USB and essential userspace services without System UI or system_server instability.

### Gate 7 — connectivity and multimedia

Status: not started.

Required work: Wi-Fi, Bluetooth, audio, modem, camera and codec stacks, each behind separate compile/runtime gates.

### Gate 8 — security and integrity

Status: not started.

Required work: TEE, Keymaster, hardware-backed keystore, banking-app compatibility and data-integrity validation.

### Gate 9 — thermal, charging and performance

Status: not started.

Thermal and charging behavior must be validated at stock voltage and stock-safe clocks before any performance tuning. KernelSU/SUSFS and OC remain last-stage optional integrations with independent rollback.

## Physical-device release gate

No 4.19 image is release-flashable until all of the following exist:

- successful boot and reboot cycles;
- UART or pstore boot logs;
- UFS and filesystem integrity evidence;
- display/input/System UI stability;
- modem/connectivity validation;
- TEE/Keymaster/banking validation;
- thermal, charging and sustained-load tests;
- rollback image, checksums and changelog.
