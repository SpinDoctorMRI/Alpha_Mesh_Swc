#!/bin/bash

# Unzip source code
unzip src/tetgen/source/tetgen1.5.1-beta1.zip;

# Build source code
cd tetgen1.5.1-beta1;
mkdir build
cd build
cmake ..
make

# Move executable to the src file.
mv tetgen1.5.1-beta1/build/tetgen src/tetgen/lin64/tetgen;
# Remove build files.
rm -rf tetgen1.5.1-beta1;