# Phase 4 Exynos8895 pinctrl object evidence

## Scope

Object-level compile evidence for the Exynos8895 pin-bank data port on the Linux 4.19 Samsung pinctrl and EINT core. This does not prove full kernel linkage or physical GPIO/interrupt operation.

## Result

- GitHub Actions run: `30868044151`
- Job: `pinctrl-probe`
- Result: PASS
- Artifact: `dream2lte-linux-4.19-phase4-pinctrl-probe`
- Artifact ID: `8876864435`
- Artifact digest: `sha256:859220e259a7d539f3ef3b9505b6fc8a9d41453aa1e8c69fa7e2de3728d6edad`

## Port design

- Eight Exynos8895 pin-controller instances are represented.
- Thirty-six pin banks were checked against pinned vendor commit `dcdaf6878e7f9497e1d90e25980decfa5d684f74` before compilation.
- The Linux 4.19 Samsung pinctrl and EINT implementation remains the active core.
- The Linux 4.4 vendor IRQ driver was not copied wholesale.
- FSYS0 banks retain their three-bit drive-strength field layout.
- Device-tree compatible: `samsung,exynos8895-pinctrl`.

## Objects

- `pinctrl-exynos8895.o`
  - SHA-256: `e8e7bae1cf5b0e3b4361f83c2c53f8666f5070a49403b4db9359a51a3c6dd96d`
- `pinctrl-samsung.o`
  - SHA-256: `698ed639b6c4a23c785e417864954172bee3dbf11cb6729930abd10862cd7049`
- `pinctrl-exynos.o`
  - SHA-256: `31741bed0b56e0201e565833436b83a9da8a4ddd9e52087d5850aa3696f14ac3`

## Limitations

No physical GPIO, wake interrupt, peripheral pinmux, suspend/resume or boot testing has been performed. A combined clock/CAL/pinctrl full Image link must pass before the port is materialized into the source tree.
