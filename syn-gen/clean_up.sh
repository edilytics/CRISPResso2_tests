#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

output_dir="CRISPResso_on_long_read_big_del_analysis"

if [[ -d "$output_dir" ]]; then
  rm -rf -- "$output_dir"
  echo "Removed $output_dir"
else
  echo "$output_dir does not exist; nothing to clean"
fi
