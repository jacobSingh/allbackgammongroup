from tempfile import NamedTemporaryFile, mkdtemp
import sys
from subprocess import call
import os
import requests
import shlex, subprocess
import shutil

def remove_dir(path):
    if os.path.isdir(path):
        shutil.rmtree(path)


ghpages = "/Users/jacob/stuff/abg/bg-stat-export"
gnubg = "/Applications/gnubg.app/Contents/MacOS/local/bin/gnubg"

filename = os.path.expanduser(sys.argv[1])

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


subprocess.Popen(["git", "add", os.path.basename(match_name)], cwd=ghpages).wait()
subprocess.Popen(["git", "commit", "-m", "Added {}".format(match_name)], cwd=ghpages).wait()
subprocess.Popen(["./_makeindex.sh"], cwd=ghpages).wait()
subprocess.Popen(["git", "push"], cwd=ghpages).wait()


print("exported to " + output)
#`cat {}`.format(f)
