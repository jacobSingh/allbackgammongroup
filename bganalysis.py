#!/usr/bin/env python
from tempfile import NamedTemporaryFile, mkdtemp
import sys
from subprocess import call
import os
import requests
import shlex, subprocess
import shutil
import logging
import configparser

def remove_dir(path):
    if os.path.isdir(path):
        shutil.rmtree(path)



config=configparser.ConfigParser()
config.read('./abg.ini')
ghpages=config.get("abg_eval","ghpages")
gnubg=config.get("abg_eval","gnubg")
filename = os.path.expanduser(sys.argv[1])

if not (ghpages and gnubg):
    raise Exception("ghpages and gnubg not set.  Make an abg.ini file")

f = NamedTemporaryFile(delete=False, mode="w")

output = mkdtemp()

f.write("import auto \"{}\"\n".format(filename))
f.write("analyse match\n")
f.write("export match html {}/index.html\n".format(output))
f.close()
print(f.name)

call([gnubg, "-t", "-c", f.name])
match_name = os.path.splitext(os.path.basename(filename))[0]
new_dir = ghpages + "/" + match_name
## In case it exists, remove it
remove_dir(new_dir)
os.rename(output, new_dir)

subprocess.Popen(["./_makeindex.sh"], cwd=ghpages).wait()
subprocess.Popen(["git", "add", "index.html", os.path.basename(match_name)], cwd=ghpages).wait()
subprocess.Popen(["git", "commit", "-m", "Added {}".format(match_name)], cwd=ghpages).wait()
subprocess.Popen(["git", "push"], cwd=ghpages).wait()


print("exported to " + output)
print("http://jacobsingh.github.io/bg-stat-export/"
        + os.path.basename(match_name))
#`cat {}`.format(f)
