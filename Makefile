# for a new release, run make all before uploading to zenodo
.PHONY: data docs

data: 
	make -C scripts zenodo_files

docs:
	make -C docs clean && make -C docs html

clean:
	make -C docs clean
	rm -f data/sub000*.*
	rm -f docs/_data/sub000*.*

all: clean data docs
