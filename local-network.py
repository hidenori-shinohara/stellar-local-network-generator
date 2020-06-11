import sys
import os
import shutil
import subprocess

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

if os.path.dirname(os.path.realpath(__file__)) != os.getcwd():
    raise Exception("Must be run from the directory where local-network.py lives")

stellar_core_git_path = "https://github.com/stellar/stellar-core"
max_number_of_nodes = 10
nodes_directory_name = "nodes"

if sys.argv[1] == "clone":
    number_of_nodes = int(sys.argv[2])
    if number_of_nodes >= max_number_of_nodes:
        raise Exception("there are too many nodes")
    shutil.rmtree(nodes_directory_name, True)
    os.mkdir(nodes_directory_name)
    os.chdir(nodes_directory_name)
    print("cloning %d copies of stellar-core" % number_of_nodes)
    for node_number in range(number_of_nodes):
        subprocess.call(["git", "clone", stellar_core_git_path, "node-%d" % (node_number + 1)])
elif sys.argv[1] == "build":
    os.chdir(nodes_directory_name)
    for node_number in range(max_number_of_nodes):
        directory_name = "node-%d" % (node_number + 1)
        if os.path.isdir(directory_name):
            print("Building node %d" % (node_number + 1))
            os.chdir(directory_name)
            subprocess.call(["./autogen.sh"])
            subprocess.call(["./configure", "--enable-ccache"])
            subprocess.call(["make", "-j3"])
            os.chdir("..")
elif sys.argv[1] == "config":
    print("not implemented yet")
