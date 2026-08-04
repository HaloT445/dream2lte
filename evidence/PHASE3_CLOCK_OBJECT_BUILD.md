# Phase 3 Exynos8895 clock object evidence

## Scope

Object-level compile probe for the Exynos8895 clock provider and Samsung composite clock layer against Linux 4.19.325. This does not prove full kernel linkage, runtime clock initialization or device boot.

## Result

- GitHub Actions run: `30863797156`
- Job: `clock-probe`
- Result: PASS
- Artifact ID: `8875352800`
- Artifact digest: `sha256:54b5c9cc47e7b9a3d9fbc40d616655d7ba34ae8a9d1f16e942b364963b8250ef`

## Compatibility applied in isolated probe

- Linux CAL path selected with `CONFIG_CAL_IF`, `CONFIG_CMUCAL` and `CONFIG_SOC_EXYNOS8895` compile definitions.
- Samsung composite clock implementation imported from the pinned 4.4 source.
- Exynos snapshot framework remained disabled; only its no-op interface header was used.
- Disabled snapshot macro arity was corrected for the four-argument clock call.
- Removed common-clock flag `CLK_IS_ROOT` was mapped to zero for Linux 4.19.

## Objects

- `composite-phase3.o`
  - Size: `228,976` bytes
  - SHA-256: `c3c27af5deeae30499fc233e114526b82b2c7d081316dfdce454f9cd6d5c79e3`
- `clk-exynos8895-phase3.o`
  - Size: `303,208` bytes
  - SHA-256: `672a0708f04d16c5018b8db11a06aad4c990451d8129f53712fb33e60d23279a`

## Remaining gate

The complete CAL, PMUCAL and clock dependency closure must link into a full ARM64 Image. Object compilation alone does not detect unresolved symbols or prove correct runtime clock topology/rates.
