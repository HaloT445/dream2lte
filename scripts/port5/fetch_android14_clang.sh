#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "usage: $0 DESTINATION [ENV_FILE]" >&2
  exit 2
fi

DESTINATION=$1
ENV_FILE=${2:-"$DESTINATION.env"}
REPOSITORY=https://android.googlesource.com/platform/prebuilts/clang/host/linux-x86
COMMIT=54e738636a76ff990c0a78dc3e0d9829222eb084
ROOT_TREE=019303535bd6debdd1a4a091dffaffa80189d854
CLANG_DIR=clang-r487747c
CLANG_TREE=f53c41d50b8c8884297d59be90dfec20de9f63a4

rm -rf "$DESTINATION"
mkdir -p "$DESTINATION"
git -C "$DESTINATION" init
git -C "$DESTINATION" remote add origin "$REPOSITORY"
git -C "$DESTINATION" sparse-checkout init --cone
git -C "$DESTINATION" sparse-checkout set "$CLANG_DIR"
git -C "$DESTINATION" fetch --depth=1 --filter=blob:none origin "$COMMIT"
git -C "$DESTINATION" checkout --detach FETCH_HEAD

test "$(git -C "$DESTINATION" rev-parse HEAD)" = "$COMMIT"
test "$(git -C "$DESTINATION" rev-parse HEAD^{tree})" = "$ROOT_TREE"
test "$(git -C "$DESTINATION" rev-parse HEAD:"$CLANG_DIR")" = "$CLANG_TREE"

BIN="$DESTINATION/$CLANG_DIR/bin"
test -x "$BIN/clang"
test -x "$BIN/ld.lld"
test -x "$BIN/llvm-ar"
test -x "$BIN/llvm-nm"
test -x "$BIN/llvm-objcopy"
test -x "$BIN/llvm-strip"

cat > "$ENV_FILE" <<EOF
ANDROID_CLANG_REPOSITORY=$REPOSITORY
ANDROID_CLANG_COMMIT=$COMMIT
ANDROID_CLANG_ROOT_TREE=$ROOT_TREE
ANDROID_CLANG_DIRECTORY=$CLANG_DIR
ANDROID_CLANG_TREE=$CLANG_TREE
ANDROID_CLANG_BIN=$BIN
EOF

"$BIN/clang" --version
"$BIN/ld.lld" --version
printf 'Pinned Android Clang environment: %s\n' "$ENV_FILE"
