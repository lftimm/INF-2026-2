#!/bin/bash

#SBATCH --job-name=cavidade_cfd

#SBATCH --partition=tupi
#SBATCH --nodes=1

#SBATCH --ntasks=1 --cpus-per-task=1
#SBATCH --mem-per-cpu=16G
#SBATCH --gres=gpu:1 

#SBTACH --time=01:00:00

#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err

guix shell make -- make run
