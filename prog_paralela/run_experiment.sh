#!/usr/bin/bash

#SBATCH --job-name=ncorpo_prog_paralela
#SBATCH --partition=draco
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --time=15:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err

set -e 

if [ $# -lt 2 ]; then
    echo "[info] usage: $0 ./simulation [files to run]"
    exit 1
fi

run_experiment() {
  echo "[running] running serial experiment..."
  $1 -s $2 >> results.csv

  for t in $(seq 2 2 $MAX_CORES)
  do
    export OMP_NUM_THREADS=$t
    echo "[running] using $OMP_NUM_THREADS threads"
    echo "[running] running parallel experiment..."
    $1 -p $2 >> results.csv
  done
}

touch results.csv
MAX_CORES=$(LC_ALL=C lscpu | grep 'Core' | awk '{print $4}')
echo "[info] machine with max $MAX_CORES cores per socket"

curr=0
total=$(($#-1))
for file in "${@:2}"
do
  curr=$((curr+1))
  echo "[start] running file $file ($curr/$total)"
  run_experiment "$1" "$file"
  echo "[finished] finished file $file"
done
