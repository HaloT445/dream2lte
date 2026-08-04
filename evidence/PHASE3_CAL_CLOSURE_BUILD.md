# Phase 3 Exynos8895 CAL closure evidence

## Scope

Object-level compile gate for the Exynos8895 clock provider, Samsung composite clock layer, CAL, PMUCAL, CMUCAL, platform clock data and the Linux 4.19 PMU compatibility wrapper. This is not full kernel linkage or physical boot evidence.

## Result

- GitHub Actions run: `30865663933`
- Job: `cal-closure`
- Result: PASS
- Artifact ID: `8876018605`
- Artifact digest: `sha256:3dd4fbb62d6886f5acab3313819bcd08220c1fa4684e4238a97bf317443a806d`

## Isolated compatibility conditions

- Android common Linux 4.19.325 base.
- Pinned Exynos8895 source commit `dcdaf6878e7f9497e1d90e25980decfa5d684f74`.
- ECT disabled through header stubs.
- ACPM DVFS disabled through no-op stubs.
- Exynos Snapshot disabled; only no-op clock and PMU interfaces are supplied.
- Removed `CLK_IS_ROOT` flag mapped to zero.
- Samsung PMU calls wrapped through the Linux 4.19 regmap-based PMU API.
- Exynos8895 CAL subdirectory Kbuild explicitly registers `cal_data.o`.

## Object SHA-256

- `clk-exynos8895.o`: `7866674aa1bbb5155a5591a17a0e5aa2b45bc14679ba24869c04c9e2217d5f33`
- `composite.o`: `c411ced27c484de97ea45e841658ec67983870cfe5d2c8ef910cf414d7244006`
- `cal-if.o`: `0ca31eb18259af3d3304c05bcac7534b9c662b2da9d312e77460042cb52711ba`
- `cmucal.o`: `bf4188fed87e3db157451049c76be04ef9da5caad0a733cb4e4b9ed25a7a78ff`
- `cal_data.o`: `8d39a9c6381cdec28d1464ccd297fc5e88d1dc53f79dedec6283d735b340edfc`
- `pll_spec.o`: `34d0461c546592648075200f1e9ce9c4f91c6d1a6dd436288de8175ddff21e72`
- `pmucal_cpu.o`: `08354475086e5c5f29f72801eb5d09264cb4bb07ff37f0cca6476c956873cf9a`
- `pmucal_local.o`: `e6452e230d938cddddc5690c5a22f8cb459b726a3c441457e1d8b07c964fffcc`
- `pmucal_rae.o`: `66b77fdfedc7fc786453b1200ce77bbdf6e69b066d0e314944ee210965d3c837`
- `pmucal_system.o`: `38dbf157e4e9eb56efa4d24a3f83c86e96f9e83726223344f76fdc28849660a7`
- `ra.o`: `c64627715809f79272fc027d6485bc4d160d011632d550abeebdda90d9998f84`
- `vclk.o`: `7e4715414ff34d343ce53258f4d5e542b1bab760758f5c8cd54bba6d6ec257bf`
- `exynos8895-pmu-compat.o`: `567bed261f6b340b801e0792a45d246e24a53bf3440fa5b923fb9c609da6b8e3`

## Remaining gate

The verified closure must link into the complete Phase-2 ARM64 Image and dream2lte DTB. A full-link PASS is required before materializing these vendor files into the source branch.
