#!/usr/bin/bash

set -e 

if [ $# -lt 2 ]; then
    echo "[info] usage: $0 ./simulation [files to run]"
    exit 1
fi

CORES_PER_SOCKET=$(LC_ALL=C lscpu | grep -i 'Core(s) per socket' | awk '{print $4}')
SOCKETS=$(LC_ALL=C lscpu | grep -i 'Socket(s):' | awk '{print $2}')
THREADS_PER_CORE=$(LC_ALL=C lscpu | grep -i 'Thread(s) per core' | awk '{print $4}')
MAX_CORES=$((CORES_PER_SOCKET * SOCKETS))
MAX_THREADS=$((MAX_CORES * THREADS_PER_CORE))  

run_experiment() {
  echo "[running] running serial experiment..."
  $1 -s $2 >> results.csv

  for t in $(seq 2 2 $MAX_THREADS)
  do
    export OMP_NUM_THREADS=$t
    echo "[running] using $OMP_NUM_THREADS threads"
    echo "[running] running parallel experiment..."
    $1 -p $2 >> results.csv
  done
}

touch results.csv

echo "[info] machine has $MAX_CORES cores per socket"
echo "[info] machine has $THREADS_CORE threads per core"
echo "[info] machine with a max of $MAX_THREADS threads"

curr=0
total=$(($#-1))
for file in "${@:2}"
do
  curr=$((curr+1))
  echo "[start] running file $file ($curr/$total)"
  run_experiment "$1" "$file"
  echo "[finished] finished file $file"
done
