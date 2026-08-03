# dream2lte Linux 4.19.325 bring-up source

This branch is an isolated, non-bootable bring-up tree. It must not replace the locked Linux 4.4.302 baseline.

- Android common base: `a8bf86a0e0fa05070897a210d706d5c4d83c26ac`
- Exynos8895 DTS source: `dcdaf6878e7f9497e1d90e25980decfa5d684f74`
- dream2lte DTS dependency closure: 26 files, SHA-256 verified
- DTB host compile: PASS
- DTB SHA-256: `f6957179deff928af58f550b59fadc0bd29baf33fa1201e32041c03e3c7ec98e`

Not validated: physical boot, UART/pstore, storage, display, input, modem, Wi-Fi, Bluetooth, audio, camera, GPU, TEE, Keymaster, banking apps, charging, thermal or stress testing. KernelSU/SUSFS and OC are intentionally excluded from initial bring-up.
