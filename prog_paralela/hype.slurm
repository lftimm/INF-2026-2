#!/usr/bin/bash

#SBATCH --job-name=ncorpo
#SBATCH --partition=hype
#SBATCH --nodes=1
#SBATCH --time=15:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err

rm -f results.csv
./run_experiment.sh ./nbody universes/*
