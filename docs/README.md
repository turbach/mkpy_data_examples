To rebuild the docs and in this directory and the sample data in
../data check conf.py and make sure `nbsphinx="always"` then run

```
make clean
make html
```

To update `eeg-workshops.github.io/mkpy_data_examples` navigate to 
local directory `../gh-pages` then 

```
git checkout stub
git branch -d gh-pages
rm -rf *
cp -R ../docs/build/html/* .
git checkout --orphan gh-pages
git add -A
git commit -a -m 'manual update'
git push --force origin gh-pages
```


