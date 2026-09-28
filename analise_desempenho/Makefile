create_build_dir:
	mkdir -p ./build

pdf: create_build_dir
	pdflatex ./src/apresentacao.tex && mv apresentacao.pdf ./build 
	rm apresentacao.aux apresentacao.log apresentacao.nav apresentacao.out apresentacao.snm apresentacao.toc

mesh: create_build_dir
	gmsh -3 ./src/cavidade.geo 
	mv ./src/cavidade.msh ./build/

run: create_build_dir
	nvfortran ./src/cuda_cfd.cuf -o ./build/cfd
	cd ./build
	./cfd

compress: create_build_dir
	tar -cvf ./build/entrega.tgz ./assets/* ./src/* ./Makefile ./submit.slurm 

clean: create_build_dir
	rm ./build/*
