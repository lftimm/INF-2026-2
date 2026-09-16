#!/usr/bin/bash

set -e

for i in $(seq 100 100 1000); do
  ./GenerateUniverse $i"universe.csv" $i
done

for i in $(seq 2000 1000 10000); do
  ./GenerateUniverse $i"universe.csv" $i
done

for i in $(seq 15000 5000 25000); do
  ./GenerateUniverse $i"universe.csv" $i
done

for i in $(seq 25000 25000 100000); do
  ./GenerateUniverse $i"universe.csv" $i
done

mkdir universes
mv *universe.csv universes
