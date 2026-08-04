# Phase 5 Exynos8895 BOOT_SAFE power-domain evidence

## Scope

Object-level compile evidence for a Linux 4.19 generic power-domain provider for Exynos8895. The provider is intentionally conservative for first boot: enabled domains are registered as always-on and runtime power-off is blocked.

## Result

- GitHub Actions run: `30868758839`
- Job: `pd-safe-probe`
- Result: PASS
- Artifact: `dream2lte-linux-4.19-phase5-pd-safe-probe`
- Artifact ID: `8877106965`
- Artifact digest: `sha256:fc34a6af6ebb59780cfac5152726f6fb63236dec6085ca60e108e16c6f082547`

## Design

- Expected device-tree domains: 15 enabled and 1 disabled.
- `GENPD_FLAG_ALWAYS_ON` is applied.
- Runtime power-off callback is a no-op.
- Power-on may use `cal_pd_status()` and `cal_pd_control()`.
- CAL private headers are not included by the provider.
- Parent relationships are represented through `pm_genpd_add_subdomain()`.
- KernelSU, SUSFS, overclocking and vendor DVFS remain disabled.

## Objects

- `exynos8895-pd-safe.o`
  - SHA-256: `f6b9e6dd74c36ff99b5044227345e065ed18472a17b9c8715edd34f8a6cc41bf`
- `cal-if.o`
  - SHA-256: `0bd55b3208c19458a875a169ac8418edc801f55b78aa760239f7f5a797cc3fd6`
- `pmucal_local.o`
  - SHA-256: `596d33d73576d2707c885989e4a2c9314dfa4dbbb411ec48eb140e72c33f2cee`
- `pmucal_rae.o`
  - SHA-256: `32f790693473ec32a51d5dac49e1aca066583b93020c4ff2e75397440846876c`

Generated provider source SHA-256:

- `6843aaacc4141f1d1f59ee153aefc655809ba0af1a6c1adb24ed2ce099571817`

Clock namespace audit also passed with five global and three static names isolated.

## Limitations

This evidence proves compilation only. It does not prove CAL power-domain IDs, current hardware state, runtime PM, suspend/resume or physical boot. The always-on mode is a temporary BOOT_SAFE policy and is not a final power-management implementation.
