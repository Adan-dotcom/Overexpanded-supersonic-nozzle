#!/usr/bin/env bash
# Eilmer 5.0.0 environment for the local WSL2 installation.

export DGD="$HOME/gdtkinst"
export DGD_REPO="$HOME/gdtk"
export LDC_HOME="$HOME/opt/ldc2-1.42.0-linux-x86_64"
export PATH="$LDC_HOME/bin:$DGD/bin:$PATH"
export DGD_LUA_PATH="$DGD/lib/?.lua"
export DGD_LUA_CPATH="$DGD/lib/?.so"
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$DGD/lib"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}$DGD/lib"
