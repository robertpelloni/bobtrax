#!/bin/bash
set -e

# Default settings
BUILD_BOBUI_WASM=true
BUILD_LMMS_WASM=true
# Zrythm and MusE will need more complex setup, starting with LMMS/BobUI

# Parse arguments
for arg in "$@"; do
  case $arg in
    --only-bobui)
      BUILD_BOBUI_WASM=true
      BUILD_LMMS_WASM=false
      ;;
    --only-lmms)
      BUILD_LMMS_WASM=true
      BUILD_BOBUI_WASM=false
      ;;
    --help)
      echo "Usage: ./build_wasm.sh [OPTIONS]"
      echo "Build script for bobtrax submodules to WebAssembly."
      echo "Options:"
      echo "  --only-bobui   Build only BobUI (Emscripten)"
      echo "  --only-lmms    Build only LMMS (Emscripten)"
      echo "  --help         Show this help message"
      ;;
  esac
done

if [[ "$*" == *"--help"* ]]; then
  echo ""
else
  echo "Starting WebAssembly port build process..."

  # Check for emscripten
  if [ -z "$EMSDK" ]; then
      echo "EMSDK environment variable not set. Attempting to clone and set up emsdk locally..."
      if [ ! -d "emsdk" ]; then
          git clone https://github.com/emscripten-core/emsdk.git
      fi
      cd emsdk
      ./emsdk install latest
      ./emsdk activate latest
      source ./emsdk_env.sh
      cd ..
  else
      echo "EMSDK found at $EMSDK"
  fi

  if [ "$BUILD_BOBUI_WASM" = true ]; then
      echo ">>> Building BobUI for WebAssembly..."
      cd bobui
      mkdir -p build_wasm && cd build_wasm
      emcmake cmake .. -DBOBUI_BUILD_WASM=ON || echo "CMake for BobUI (WASM) failed. Continuing..."
      emmake make -j$(nproc) || echo "Make for BobUI (WASM) failed. Continuing..."
      cd ../..
      echo "<<< BobUI WASM build attempt finished."
  fi

  if [ "$BUILD_LMMS_WASM" = true ]; then
      echo ">>> Building LMMS for WebAssembly..."
      cd lmms
      mkdir -p build_wasm && cd build_wasm
      emcmake cmake .. -DWANT_QT5=OFF -DWANT_GUI=OFF || echo "CMake for LMMS (WASM) failed. Continuing..."
      emmake make -j$(nproc) || echo "Make for LMMS (WASM) failed. Continuing..."
      cd ../..
      echo "<<< LMMS WASM build attempt finished."
  fi

  echo "WebAssembly builds finished!"
fi
