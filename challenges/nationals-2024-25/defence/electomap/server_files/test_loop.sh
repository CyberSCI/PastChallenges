#!/bin/bash

set -euxo pipefail

export PYTHONPATH=../../siege/

ticks=$1

for i in $(seq 1 $ticks); do
  uv run ../../siege/siege/test_attacker.py \
    ./electomap_attacker.py \
    ElectomapAttacker \
    127.0.0.1:1337 \
    1,2,3,4,5,6,7,8,-1,-2,-3,-4,-5,-6,-7,-8 \
    $i
done
