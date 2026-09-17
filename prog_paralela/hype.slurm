#!/usr/bin/bash

#SBATCH --job-name=ncorpo
#SBATCH --partition=hype
#SBATCH --nodes=1
#SBATCH --time=10:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err

rm results.csv
make
./run_experiment ./nbody universes/*
