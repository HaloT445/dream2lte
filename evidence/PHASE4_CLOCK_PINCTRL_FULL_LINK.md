# Phase 4 Exynos8895 clock/CAL and pinctrl full-link evidence

## Scope

Host-build and full-link evidence for the Exynos8895 clock/CAL/PMUCAL and pinctrl data ports on Linux 4.19.325. This is not physical boot evidence.

## Result

- GitHub Actions run: `30868291781`
- Job: `phase4-link`
- Result: PASS
- Artifact: `dream2lte-linux-4.19-phase4-clock-pinctrl-link`
- Artifact ID: `8877166152`
- Artifact digest: `sha256:e7d92fee817f2e754b710062550f1945daee4093355068a1ff02cf78d70b01eb`

## Included subsystems

- Exynos8895 clock provider.
- Samsung CAL, CMUCAL and PMUCAL closure.
- Linux 4.19 core Samsung clock and PLL implementations preserved.
- Exynos8895 pinctrl data: 8 controllers and 36 banks.
- Linux 4.19 Samsung EINT implementation preserved.
- Source-local build flags; no global `KCFLAGS` dependency.

## Outputs

### Kernel Image

- File: `Image-dream2lte-4.19-phase4`
- Size: `21,436,928` bytes
- SHA-256: `42b2144cefbfd022c208e952e497aae3b66f255a045e67d49bec361dce43a73c`

### Device tree

- File: `exynos8895-dream2lte_eur_open_10-phase4.dtb`
- Size: `221,744` bytes
- SHA-256: `f6957179deff928af58f550b59fadc0bd29baf33fa1201e32041c03e3c7ec98e`

### Configuration

- Final `.config` SHA-256: `6d84ad3b93192031df0adb24a0aa9f9d2bbec8cccac2096dd16d1a874a75cb6a`

## Limitations

The build has not booted on physical hardware. GPIO/EINT operation, wake interrupts, clock rates, suspend/resume, power domains, UFS, mounted Android partitions, display, input, modem, Wi-Fi, Bluetooth, audio, camera, GPU, TEE, Keymaster, banking applications, charging, thermal behavior and stress stability remain unvalidated.
