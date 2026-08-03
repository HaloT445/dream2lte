# Phase 2 Android host-build evidence

## Scope

This record covers host compilation only for the isolated `dream2lte` Linux 4.19.325 bring-up tree. It is not physical-device boot evidence and does not authorize flashing as a release kernel.

## Result

- GitHub Actions run: `30862729308`
- Job: `phase2-android`
- Result: PASS
- Artifact: `dream2lte-linux-4.19-phase2-android`
- Artifact ID: `8875274428`
- Artifact digest: `sha256:ab1b6661ccd7665a803c9f38bc7891e200af5f662dba68182a3276d4c5fa020c`

## Configuration gate

Strict requested-symbol attestation passed for the Phase-2 fragment. Key enabled interfaces include:

- Android Binder IPC with `binder,hwbinder,vndbinder`
- ASHMEM
- SELinux
- cgroups, namespaces and seccomp
- ext4 and F2FS encryption/security support
- device mapper, dm-crypt and dm-verity/FEC
- generic UFS and MMC block support
- Samsung serial console
- pstore, pmsg and RAM backend support

KernelSU, SUSFS and overclocking are disabled.

## Outputs

### Kernel Image

- File: `Image-dream2lte-4.19-phase2`
- Size: `20,527,616` bytes
- Identification: Linux kernel ARM64 boot executable Image, little-endian, 4K pages
- SHA-256: `80a62dbf19ab4c96c3ed10211b9354da2d8606059db4f3536c2c6dec8ef5b76e`

### Device tree

- File: `exynos8895-dream2lte_eur_open_10-phase2.dtb`
- Size: `221,744` bytes
- SHA-256: `f6957179deff928af58f550b59fadc0bd29baf33fa1201e32041c03e3c7ec98e`

### Configuration

- Final `.config` SHA-256: `6d84ad3b93192031df0adb24a0aa9f9d2bbec8cccac2096dd16d1a874a75cb6a`
- Phase-2 fragment SHA-256: `9ced056a542515e6a8f78fb63a074d62f1fb5f81071f5ca5ef0374f52822b775`

## Limitations

The Image is not yet linked with a validated Exynos8895 vendor clock/CAL, UFS PHY, PMU/power-domain, PMIC/regulator, display, GPU, modem, camera or TEE stack. No physical boot, UART/pstore capture, partition mount, banking-app, thermal, charging or stress-test evidence exists.
