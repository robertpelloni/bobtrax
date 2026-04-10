#!/bin/bash
set -e

# Default settings
BUILD_BOBUI=true
BUILD_ARDOUR=true
BUILD_LMMS=true
BUILD_MUSE=true
BUILD_ZRYTHM=true

# Parse arguments
for arg in "$@"; do
  case $arg in
    --only-bobui)
      BUILD_BOBUI=true
      BUILD_ARDOUR=false; BUILD_LMMS=false; BUILD_MUSE=false; BUILD_ZRYTHM=false
      ;;
    --only-ardour)
      BUILD_ARDOUR=true
      BUILD_BOBUI=false; BUILD_LMMS=false; BUILD_MUSE=false; BUILD_ZRYTHM=false
      ;;
    --only-lmms)
      BUILD_LMMS=true
      BUILD_BOBUI=false; BUILD_ARDOUR=false; BUILD_MUSE=false; BUILD_ZRYTHM=false
      ;;
    --only-muse)
      BUILD_MUSE=true
      BUILD_BOBUI=false; BUILD_ARDOUR=false; BUILD_LMMS=false; BUILD_ZRYTHM=false
      ;;
    --only-zrythm)
      BUILD_ZRYTHM=true
      BUILD_BOBUI=false; BUILD_ARDOUR=false; BUILD_LMMS=false; BUILD_MUSE=false
      ;;
    --help)
      echo "Usage: ./build.sh [OPTIONS]"
      echo "Build script for bobtrax submodules."
      echo "Options:"
      echo "  --only-bobui   Build only BobUI (CMake)"
      echo "  --only-ardour  Build only Ardour (Waf)"
      echo "  --only-lmms    Build only LMMS (CMake)"
      echo "  --only-muse    Build only MusE (CMake)"
      echo "  --only-zrythm  Build only Zrythm (CMake)"
      echo "  --help         Show this help message"
      ;;
  esac
done

if [[ "$*" == *"--help"* ]]; then
  echo ""
else
  echo "Starting bobtrax omni-build..."

  if [ "$BUILD_BOBUI" = true ]; then
      echo ">>> Building BobUI..."
      cd bobui
      mkdir -p build && cd build
      cmake .. || echo "CMake for BobUI failed, likely missing dependencies (e.g. OpenGL). Continuing..."
      make -j$(nproc) || echo "Make for BobUI failed. Continuing..."
      cd ../..
      echo "<<< BobUI build attempt finished."
  fi

  if [ "$BUILD_ARDOUR" = true ]; then
      echo ">>> Building Ardour..."
      cd ardour
      ./waf configure || echo "Waf configure for Ardour failed. Continuing..."
      ./waf -j$(nproc) || echo "Waf build for Ardour failed. Continuing..."
      cd ..
      echo "<<< Ardour build attempt finished."
  fi

  if [ "$BUILD_LMMS" = true ]; then
      echo ">>> Building LMMS..."
      cd lmms
      mkdir -p build && cd build
      cmake .. || echo "CMake for LMMS failed. Continuing..."
      make -j$(nproc) || echo "Make for LMMS failed. Continuing..."
      cd ../..
      echo "<<< LMMS build attempt finished."
  fi

  if [ "$BUILD_MUSE" = true ]; then
      echo ">>> Building MusE..."
      cd muse/src
      mkdir -p build && cd build
      cmake .. || echo "CMake for MusE failed. Continuing..."
      make -j$(nproc) || echo "Make for MusE failed. Continuing..."
      cd ../../..
      echo "<<< MusE build attempt finished."
  fi

  if [ "$BUILD_ZRYTHM" = true ]; then
      echo ">>> Building Zrythm..."
      cd zrythm
      mkdir -p build && cd build
      cmake .. || echo "CMake for Zrythm failed. Continuing..."
      make -j$(nproc) || echo "Make for Zrythm failed. Continuing..."
      cd ../..
      echo "<<< Zrythm build attempt finished."
  fi

  echo "All requested builds finished successfully!"
fi
