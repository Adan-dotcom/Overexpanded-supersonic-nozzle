#!/usr/bin/env bash
set -euo pipefail

EILMER_TAG=v5.0.0
EILMER_COMMIT=f53f4609a0331d48efee69a4e4f3c3598378cc03
LDC_VERSION=1.42.0
LDC_ARCHIVE="ldc2-${LDC_VERSION}-linux-x86_64.tar.xz"
LDC_SHA256=a7bc9c956138f558cadf9c962352f59d41c80df6eb3ae3f8039f25be14a69303
LDC_URL="https://github.com/ldc-developers/ldc/releases/download/v${LDC_VERSION}/${LDC_ARCHIVE}"

if [[ ${EUID} -eq 0 ]]; then
    echo "Run this script as the normal WSL user; it invokes sudo only for apt." >&2
    exit 2
fi

sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential gfortran gfortran-multilib ruby tcl \
    python3-sympy python3-pandas python3-matplotlib \
    libreadline-dev libncurses-dev libopenmpi-dev openmpi-bin \
    libfftw3-dev liblapack-dev zlib1g-dev xz-utils wget ca-certificates

mkdir -p "$HOME/opt"
if [[ ! -f "$HOME/opt/$LDC_ARCHIVE" ]]; then
    wget -O "$HOME/opt/$LDC_ARCHIVE" "$LDC_URL"
fi
printf '%s  %s\n' "$LDC_SHA256" "$HOME/opt/$LDC_ARCHIVE" | sha256sum -c -
if [[ ! -x "$HOME/opt/ldc2-${LDC_VERSION}-linux-x86_64/bin/ldc2" ]]; then
    tar -C "$HOME/opt" -xf "$HOME/opt/$LDC_ARCHIVE"
fi

if [[ ! -d "$HOME/gdtk/.git" ]]; then
    git clone --branch "$EILMER_TAG" --depth 1 \
        https://github.com/gdtk-uq/gdtk.git "$HOME/gdtk"
fi

actual_commit=$(git -C "$HOME/gdtk" rev-parse HEAD)
if [[ $actual_commit != "$EILMER_COMMIT" ]]; then
    printf 'Expected GDTk commit %s, found %s. Refusing to overwrite it.\n' \
        "$EILMER_COMMIT" "$actual_commit" >&2
    exit 3
fi

export PATH="$HOME/opt/ldc2-${LDC_VERSION}-linux-x86_64/bin:$PATH"
make -C "$HOME/gdtk/src/lmr" DMD=ldc2 FLAVOUR=fast WITH_MPI=1 install
# Python validation and post-processing import gdtk.gas, which dynamically
# loads libgas.so.  The LMR target installs the Python wrapper but not that
# shared library, so install the official gas-library target as well.
make -C "$HOME/gdtk/src/gas" DMD=ldc2 FLAVOUR=fast install

cat <<EOF
Installed Eilmer $EILMER_TAG at $HOME/gdtkinst
Source is at $HOME/gdtk
Source raptor_like_study/eilmer/eilmer5-env.sh before use.
EOF
