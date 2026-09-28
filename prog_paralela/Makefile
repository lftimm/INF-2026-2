#!/usr/bin/bash

nbody:
	g++ -O3 -std=c++23 -march=native  -ffast-math -fopenmp nbody.cpp -o nbody

ssh:
	rsync --verbose --progress --recursive . lftimm@gppd-hpc.inf.ufrgs.br:$(shell basename $(CURDIR))
