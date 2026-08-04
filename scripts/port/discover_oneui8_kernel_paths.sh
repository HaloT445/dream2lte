#!/usr/bin/env bash
set -euo pipefail

INPUT_ROOT="${1:-.}"
REPORT_ROOT="${2:-kernel-path-report}"
WORK_ROOT="$(mktemp -d)"
trap 'rm -rf "$WORK_ROOT"' EXIT

mkdir -p "$REPORT_ROOT"
REPORT="$REPORT_ROOT/KERNEL_PATH_REPORT.md"
TSV="$REPORT_ROOT/KERNEL_PATH_REPORT.tsv"
: > "$REPORT"
: > "$TSV"

have() { command -v "$1" >/dev/null 2>&1; }
record() {
  local kind="$1" path="$2" detail="$3"
  printf '%s\t%s\t%s\n' "$kind" "$path" "$detail" >> "$TSV"
  printf -- '- **%s**: `%s` — %s\n' "$kind" "$path" "$detail" >> "$REPORT"
}

printf '# One UI 8 / dream2lte kernel path report\n\n' >> "$REPORT"
printf 'Input root: `%s`\n\n' "$(realpath "$INPUT_ROOT")" >> "$REPORT"
printf 'This scan is read-only. It does not repack or modify any image.\n\n' >> "$REPORT"

CANDIDATES="$WORK_ROOT/candidates.txt"
find "$INPUT_ROOT" -type f \
  \( -iname 'boot.img' -o -iname 'boot.img.lz4' \
     -o -iname 'vendor_boot.img' -o -iname 'vendor_boot.img.lz4' \
     -o -iname 'init_boot.img' -o -iname 'init_boot.img.lz4' \
     -o -iname 'dtbo.img' -o -iname 'dtbo.img.lz4' \
     -o -iname 'recovery.img' -o -iname 'recovery.img.lz4' \
     -o -iname 'AP_*.tar' -o -iname 'AP_*.tar.md5' \) \
  -print | sort -u > "$CANDIDATES"

printf '## Located firmware containers\n\n' >> "$REPORT"
if ! test -s "$CANDIDATES"; then
  record warning "$INPUT_ROOT" 'No boot/AP firmware container found'
fi

EXPANDED="$WORK_ROOT/expanded"
mkdir -p "$EXPANDED"

while IFS= read -r item; do
  test -n "$item" || continue
  case "$item" in
    *.tar|*.tar.md5)
      record ap_archive "$item" "$(sha256sum "$item" | awk '{print $1}')"
      archive_dir="$EXPANDED/$(basename "$item" | tr '/ ' '__')"
      mkdir -p "$archive_dir"
      # Samsung tar.md5 normally contains a valid tar stream followed by an MD5 trailer.
      tar -xf "$item" -C "$archive_dir" \
        --wildcards --no-anchored \
        'boot.img*' 'vendor_boot.img*' 'init_boot.img*' 'dtbo.img*' 'recovery.img*' \
        2>"$archive_dir/tar-extract.log" || true
      find "$archive_dir" -type f -print >> "$CANDIDATES.expanded"
      ;;
    *)
      printf '%s\n' "$item" >> "$CANDIDATES.expanded"
      ;;
  esac
done < "$CANDIDATES"

sort -u "$CANDIDATES.expanded" 2>/dev/null > "$WORK_ROOT/images.all" || true

NORMALIZED="$WORK_ROOT/normalized"
mkdir -p "$NORMALIZED"

while IFS= read -r image; do
  test -f "$image" || continue
  base="$(basename "$image")"
  normalized="$image"
  if [[ "$base" == *.lz4 ]]; then
    if have lz4; then
      normalized="$NORMALIZED/${base%.lz4}.$(printf '%s' "$image" | sha256sum | cut -c1-12)"
      lz4 -d -f "$image" "$normalized" >/dev/null
      record compressed_image "$image" "decompressed to $normalized"
    else
      record warning "$image" 'lz4 command missing; compressed image not inspected'
      continue
    fi
  fi

  kind="$(basename "$normalized")"
  digest="$(sha256sum "$normalized" | awk '{print $1}')"
  description="$(file -b "$normalized" 2>/dev/null || echo unknown)"
  record firmware_image "$normalized" "sha256=$digest; $description"

  case "$kind" in
    boot.img*|vendor_boot.img*|init_boot.img*|recovery.img*)
      unpack_dir="$WORK_ROOT/unpack/$(printf '%s' "$normalized" | sha256sum | cut -c1-16)"
      mkdir -p "$unpack_dir"
      if have magiskboot; then
        (
          cd "$unpack_dir"
          magiskboot unpack "$normalized" > magiskboot.log 2>&1 || true
        )
        record unpack_log "$unpack_dir/magiskboot.log" "magiskboot output for $normalized"

        for component in kernel kernel_dtb dtb dtbo ramdisk.cpio vendor_ramdisk.cpio header; do
          if test -e "$unpack_dir/$component"; then
            comp_sha="$(sha256sum "$unpack_dir/$component" 2>/dev/null | awk '{print $1}')"
            record "${kind%%.*}_component" "$normalized::$component" "sha256=${comp_sha:-n/a}"
          fi
        done

        if test -s "$unpack_dir/kernel"; then
          record replacement_target "$normalized::kernel" 'Replace only after Image+DTB boot-critical gates PASS'
        fi
        if test -s "$unpack_dir/dtb"; then
          record dtb_target "$normalized::dtb" 'DTB is embedded in this boot container'
        fi
      elif have unpack_bootimg; then
        out="$unpack_dir/unpack_bootimg"
        mkdir -p "$out"
        unpack_bootimg --boot_img "$normalized" --out "$out" > "$unpack_dir/unpack_bootimg.log" 2>&1 || true
        record unpack_log "$unpack_dir/unpack_bootimg.log" "unpack_bootimg output for $normalized"
      else
        record warning "$normalized" 'Install magiskboot or unpack_bootimg to inspect boot components'
      fi
      ;;
  esac
done < "$WORK_ROOT/images.all"

printf '\n## Linux 5.15 source/build path contract\n\n' >> "$REPORT"
cat >> "$REPORT" <<'EOF'
- Kernel source root: repository root of branch `port/linux-5.15-source`
- GKI defconfig: `arch/arm64/configs/gki_defconfig`
- Android build config: `build.config.gki.aarch64`
- Planned dream2lte fragment: `arch/arm64/configs/dream2lte_gki.fragment`
- Build output root: `out/dream2lte-5.15/`
- Kernel Image: `out/dream2lte-5.15/arch/arm64/boot/Image`
- Device trees: `arch/arm64/boot/dts/exynos/`
- Expected DTB output: `out/dream2lte-5.15/arch/arm64/boot/dts/exynos/exynos8895-dream2lte*.dtb`
- Expected DTBO output: `out/dream2lte-5.15/arch/arm64/boot/dts/exynos/*.dtbo`
- Kernel modules: `out/dream2lte-5.15/**/*.ko`
- Module manifests: `out/dream2lte-5.15/modules.order` and `modules.builtin*`

For the locked S8 Plus baseline, the original boot image uses a legacy header and the safe expectation is that the kernel payload is inside `boot.img`. The scanner still checks `vendor_boot.img` because a One UI 8 port package may reorganize ramdisk or DTB content.
EOF

printf '\n## Safety status\n\n' >> "$REPORT"
printf -- '- No image was modified.\n- No flashable package was generated.\n- KernelSU, SUSFS and overclocking are outside this path-discovery scope.\n' >> "$REPORT"

printf 'Report written to %s\n' "$REPORT"
printf 'Machine-readable path list written to %s\n' "$TSV"
