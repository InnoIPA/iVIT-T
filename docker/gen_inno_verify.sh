#!/bin/bash
FILE_PATH=$(realpath "$0")
FILE_DIR=$(dirname "${FILE_PATH}" )
OUT="./inno_verify"
cd "${FILE_DIR}" || exit

# --------------------------------------------------------
# Package verify.py
pyinstaller -F ../common/verify.py

# --------------------------------------------------------
# Remove other generate file
mv dist/verify $OUT
rm -rf dist build verify.spec
chown 1000:1000 $OUT

echo "Done"