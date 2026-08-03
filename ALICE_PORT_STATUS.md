# dream2lte Linux 4.19.325 bring-up source

This branch is an isolated, non-bootable bring-up tree. It must not replace the locked Linux 4.4.302 baseline.

## Pinned sources

- Android common base: `a8bf86a0e0fa05070897a210d706d5c4d83c26ac`
- Exynos8895 DTS source: `dcdaf6878e7f9497e1d90e25980decfa5d684f74`

## Verified host-build evidence

### Phase 0 — generic ARM64 base

- Generic ARM64 Image build with GCC AArch64: PASS
- Generic Image size: 19,347,968 bytes
- Generic Image SHA-256: `cde5ec2416031951d6fdbbee8c0af1a5641b33d0fb0fdbfd15bf97219b4343a9`
- Generic defconfig SHA-256: `8d467d0af749c16f4fc04de14e75b8c52f315a9242b9e60807fb5ae43c1bdd47`

### Phase 1 — dream2lte device tree

- dream2lte DTS dependency closure: 26 files, SHA-256 verified
- dream2lte DTB host compile: PASS
- DTB size: 221,744 bytes
- DTB SHA-256: `f6957179deff928af58f550b59fadc0bd29baf33fa1201e32041c03e3c7ec98e`

### Phase 2 — Android ABI and boot-diagnostics configuration

- Strict requested-symbol attestation: PASS
- ARM64 Image and dream2lte DTB combined host build: PASS
- Image identification: Linux ARM64 boot executable, little-endian, 4K pages
- Phase-2 Image size: 20,527,616 bytes
- Phase-2 Image SHA-256: `80a62dbf19ab4c96c3ed10211b9354da2d8606059db4f3536c2c6dec8ef5b76e`
- Phase-2 DTB size: 221,744 bytes
- Phase-2 DTB SHA-256: `f6957179deff928af58f550b59fadc0bd29baf33fa1201e32041c03e3c7ec98e`
- Final configuration SHA-256: `6d84ad3b93192031df0adb24a0aa9f9d2bbec8cccac2096dd16d1a874a75cb6a`
- Locked fragment SHA-256: `9ced056a542515e6a8f78fb63a074d62f1fb5f81071f5ca5ef0374f52822b775`
- GitHub Actions artifact digest: `sha256:ab1b6661ccd7665a803c9f38bc7891e200af5f662dba68182a3276d4c5fa020c`
- Detailed record: `evidence/PHASE2_ANDROID_HOST_BUILD.md`

The Phase-2 configuration enables Binder devices, ASHMEM, SELinux, cgroups, namespaces, seccomp, ext4/F2FS encryption, dm-verity, generic UFS/MMC, Samsung UART and pstore. KernelSU, SUSFS and overclocking remain disabled.

The generated Image still uses generic/common platform support. It is not a proven dream2lte device kernel and must not be flashed as a release build.

## Current next gate

Phase 3 is compiling the Exynos8895 clock provider and Samsung CAL/composite dependency closure against Linux 4.19. The probe is isolated from this source branch until its object-level compile gate passes.

## Not validated

Physical boot, UART/pstore capture, UFS initialization, mounted Android partitions, display, input, modem, Wi-Fi, Bluetooth, audio, camera, GPU, TEE, Keymaster, banking apps, charging, thermal and stress testing remain unvalidated.
