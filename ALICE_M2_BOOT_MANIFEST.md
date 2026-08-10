# ALice S8+ dream2lte M2 schedutil boost

Target: Exynos 8895 / dream2lte / Linux 4.4.302.

## Runtime policy

- M2 normal maximum: 2.314 GHz
- M2 boost maximum: 2.704 GHz
- Boost permission only when A53 average load >= 85% and every A53 CPU reports >= 2.000 GHz
- The controller changes only `PM_QOS_CLUSTER1_FREQ_MAX`; it does not force an M2 minimum frequency. `schedutil` remains responsible for choosing the actual OPP.
- Burst: 180 ms inside a rolling 480 ms window (37.5%)
- Thermal guard: block at 65 C, re-arm at 62 C
- Battery guard: design >= 3200 mAh and remaining >= 1200 mAh when the platform exposes charge values
- M2 CPU hot-unplug is refused; idle states remain available

## Clang 17

`.github/workflows/build-alice-clang17.yml` pins Clang 17 and uses the Arm GNU 13.3 toolchain for the external assembler path required by this older 4.4.302 tree.

## Boot artifact

A boot image was repacked locally from the supplied boot image. Its kernel binary remains the supplied bootable kernel; the M2 controller is carried as `alice_m2_boost.ko` in the ramdisk and `lib/modules/modules.load` is provided for Android init's kernel-module loader.

Boot SHA-256:

`ad907b3a67cbd9381770254abae1954d553e1f6581d76cf3ed9645e86b900501`

Important: this boot image is **not** a full Clang-17-rebuilt kernel image. The full Image rebuild is delegated to the GitHub Actions workflow because Linux 4.4.302's old AArch64 assembly requires the Arm GNU external assembler path. Do not treat the boot artifact as proof that the entire kernel was rebuilt with Clang 17.
