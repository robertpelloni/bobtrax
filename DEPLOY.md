# Deployment Instructions

Currently, the project is a collection of submodules. Deployment involves cloning the repository and initializing all submodules.

## Steps
1. `git clone --recursive <repository_url>`
2. `git submodule update --init --recursive`
3. Build each submodule according to its respective build instructions (usually CMake or Waf depending on the DAW).
4. Run `bobui` to launch the unified interface (pending full implementation).
