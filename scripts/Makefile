.PHONY: xlogs pm_codemaps zenodo_files  

all: zenodo_files

# rebuild all HDF5 recordings and epochs files for upload to zenodo
# mkpy_data_examples
# https://doi.org/10.5281/zenodo.3960356
zenodo_files: xlogs pm_codemaps
	python ./make_zenodo_files.py

# set log_flags for garv artifacts in .x.log files
xlogs:
	./make_xlog_sub000_p50_p3_wr_pm.sh

# script to build separate study and test phase code maps for picture memory 
pm_codemaps:
	python ./make_pm_codemaps.py

