#!/bin/bash -e

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    echo "[!] Please clean up the repo first"
    git status
    exit 1
fi

echo "[!] Applying patch.diff"
(cd source/src; patch < ../patch.diff)

function restore() {
    echo "[!] Reverting patch.diff"
    (cd source/src; patch -R < ../patch.diff)
}

trap restore EXIT

./test-all.sh
