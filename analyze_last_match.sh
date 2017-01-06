echo $(ls -tr sm/ | tail -n1 | xargs basename)

./bganalysis.py  sm/$(ls -tr sm/ | tail -n1 | xargs basename)
