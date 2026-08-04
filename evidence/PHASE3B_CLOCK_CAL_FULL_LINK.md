# Phase 3B Exynos8895 clock/CAL full-link evidence

## Scope

Host-build and full-link evidence for the isolated Linux 4.19.325 `dream2lte` bring-up tree. This is not physical boot evidence and does not authorize flashing as a release kernel.

## Result

- GitHub Actions run: `30867154376`
- Job: `clock-link-v5`
- Result: PASS
- Artifact: `dream2lte-linux-4.19-phase3b-clock-link-v5`
- Artifact ID: `8876844728`
- Artifact digest: `sha256:9581f368e9b3fe0d4319fa82f7d53f7be234a2c9ebb56a175a4690edf847d46b`

## Compatibility closure

- Exynos8895 clock provider linked with Samsung CAL, CMUCAL and PMUCAL.
- Linux 4.19 Samsung common clock and PLL implementations remained intact.
- Eight vendor symbols colliding with the Linux 4.19 core were isolated under the `exynos8895_vendor_*` namespace.
- Exynos Snapshot remained disabled; only no-op interfaces were supplied.
- ECT and ACPM DVFS remained disabled/stubbed.
- `CLK_IS_ROOT` compatibility was mapped to zero.
- No KernelSU, SUSFS or overclocking was enabled.

## Outputs

### Kernel Image

- File: `Image-dream2lte-4.19-phase3b-clock-link`
- Size: `21,436,928` bytes
- Identification: Linux kernel ARM64 boot executable Image, little-endian, 4K pages
- SHA-256: `d059e070ae34f7d5e89de2527d540d925b6eb43bdcf5cd5af67103897dd09ea1`

### Device tree

- File: `exynos8895-dream2lte_eur_open_10-phase3b-clock-link.dtb`
- Size: `221,744` bytes
- SHA-256: `f6957179deff928af58f550b59fadc0bd29baf33fa1201e32041c03e3c7ec98e`

### Configuration

- Final `.config` SHA-256: `6d84ad3b93192031df0adb24a0aa9f9d2bbec8cccac2096dd16d1a874a75cb6a`

## Limitations

This evidence proves compilation and linkage only. Physical boot, early console, pstore, clock rate correctness, DVFS, suspend/resume, UFS initialization, Android partition mount, display, input, modem, Wi-Fi, Bluetooth, audio, camera, GPU, TEE, Keymaster, banking applications, charging, thermal behavior and stress stability remain unvalidated.
