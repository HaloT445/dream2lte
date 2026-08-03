# dream2lte — port Linux 4.4.302 lên Android kernel 4.19

Đây là nhánh bring-up kỹ thuật, chưa phải kernel 4.19 đã boot được. Không đổi số phiên bản trong Makefile 4.4 để giả thành 4.19.

## Baseline khóa

- Thiết bị: Samsung Galaxy S8 Plus `dream2lte`, Exynos 8895.
- Baseline hiện tại: Linux 4.4.302.
- Defconfig: `alice_dream2lte_susfs_defconfig`.
- Nhánh 4.4 không bị sửa hoặc merge.
- KernelSU/SUSFS chỉ được port lại sau khi core 4.19 boot ổn định.

## Target khóa

- Nguồn: Android common kernel `deprecated/android-4.19-stable`.
- Commit: `a8bf86a0e0fa05070897a210d706d5c4d83c26ac`.
- Phiên bản giải quyết: Linux 4.19.325.
- Nhánh: `port/linux-4.19-bringup`.
- Draft PR: #2; không merge vào `main` ở trạng thái hiện tại.

## Thứ tự bring-up

1. Build generic ARM64 Image trên 4.19.
2. Compile dependency closure DTS/dt-bindings của dream2lte.
3. Boot core: PSCI/SMC, GIC, timer, UART, reserved-memory.
4. Clock, pinctrl, PM domains, regulator, UFS/MMC và filesystem.
5. Android ABI: binder, ION/dma-buf/sync, SELinux.
6. Display và input.
7. USB, Wi-Fi, Bluetooth, audio.
8. GPU, modem, camera và codec.
9. KernelSU/SUSFS.
10. Thermal, charging và OC chỉ sau boot/stress.

## Trạng thái

- Phase 0 lần đầu: defconfig PASS; build fail do `LLVM=1` chọn compiler host x86. Workflow đã chuyển sang GCC AArch64 cross-compiler.
- Phase 1: 26 file DTS/dt-bindings khớp byte-for-byte với upstream Exynos8895 commit `dcdaf6878e7f9497e1d90e25980decfa5d684f74`; workflow đang thử compile DTB trên 4.19.
- Chưa có bằng chứng boot, UART, pstore, display, storage, modem, TEE, Keymaster, app ngân hàng hoặc stress test.
