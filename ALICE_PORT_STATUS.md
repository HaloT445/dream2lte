# dream2lte Linux 4.19.325 bring-up source

This branch is an isolated, non-bootable bring-up tree. It must not replace the locked Linux 4.4.302 baseline.

## Pinned sources

- Android common base: `a8bf86a0e0fa05070897a210d706d5c4d83c26ac`
- Exynos8895 DTS source: `dcdaf6878e7f9497e1d90e25980decfa5d684f74`

## Verified host-build evidence

- Generic ARM64 Image build with GCC AArch64: PASS
- Generic Image size: 19,347,968 bytes
- Generic Image SHA-256: `cde5ec2416031951d6fdbbee8c0af1a5641b33d0fb0fdbfd15bf97219b4343a9`
- Generic defconfig SHA-256: `8d467d0af749c16f4fc04de14e75b8c52f315a9242b9e60807fb5ae43c1bdd47`
- dream2lte DTS dependency closure: 26 files, SHA-256 verified
- dream2lte DTB host compile: PASS
- DTB size: 221,744 bytes
- DTB SHA-256: `f6957179deff928af58f550b59fadc0bd29baf33fa1201e32041c03e3c7ec98e`

The generic ARM64 Image is not a dream2lte device kernel. It only proves the pinned 4.19 base and cross-toolchain can produce an ARM64 kernel image.

Not validated: physical boot, UART/pstore, storage, display, input, modem, Wi-Fi, Bluetooth, audio, camera, GPU, TEE, Keymaster, banking apps, charging, thermal or stress testing. KernelSU/SUSFS and OC are intentionally excluded from initial bring-up.
