import sys
import os
import shutil
import subprocess
import json

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

if os.path.dirname(os.path.realpath(__file__)) != os.getcwd():
    raise Exception("Must be run from the directory where local-network.py lives")

stellar_core_git_path = "https://github.com/stellar/stellar-core"
max_number_of_nodes = 10
nodes_directory_name = "nodes"

config_tmpl = '''
HTTP_PORT={HTTP_PORT}
PUBLIC_HTTP_PORT=false
RUN_STANDALONE=false

NETWORK_PASSPHRASE="My local network"

PEER_PORT={PEER_PORT}

# public key = {PUBLIC_KEY}
NODE_SEED="{PRIVATE_KEY} self"
NODE_IS_VALIDATOR=true

DATABASE="sqlite3://stellar.db"

COMMANDS=["ll?level=info"]
ARTIFICIALLY_GENERATE_LOAD_FOR_TESTING=true

FAILURE_SAFETY=0
UNSAFE_QUORUM=true

KNOWN_PEERS = {KNOWN_PEERS}

[QUORUM_SET]
THRESHOLD_PERCENT=100
VALIDATORS={VALIDATORS}

[HISTORY.vs]
get="cp /tmp/stellar-core/history-{node_number}/vs/{{0}} {{1}}"
put="cp {{0}} /tmp/stellar-core/history-{node_number}/vs/{{1}}"
mkdir="mkdir -p /tmp/stellar-core/history-{node_number}/vs/{{0}}"
'''

number_of_nodes = int(sys.argv[2])
if number_of_nodes >= max_number_of_nodes:
    raise Exception("there are too many nodes")
if sys.argv[1] == "clone":
    shutil.rmtree(nodes_directory_name, True)
    os.mkdir(nodes_directory_name)
    os.chdir(nodes_directory_name)
    print("cloning %d copies of stellar-core" % number_of_nodes)
    for node_number in range(number_of_nodes):
        subprocess.call(["git", "clone", stellar_core_git_path, "node-%d" % node_number])
elif sys.argv[1] == "clean_build":
    os.chdir(nodes_directory_name)
    for node_number in range(number_of_nodes):
        directory_name = "node-%d" % node_number
        if os.path.isdir(directory_name):
            print("Building node %d" % node_number)
            os.chdir(directory_name)
            subprocess.call(["./autogen.sh"])
            subprocess.call(["./configure", "--enable-ccache"])
            subprocess.call(["make", "-j3"])
            os.chdir("..")
elif sys.argv[1] == "config":
    os.chdir(nodes_directory_name)
    public_keys = []
    private_keys = []
    for node_number in range(number_of_nodes):
        directory_name = "node-%d" % node_number
        if os.path.isdir(directory_name):
            os.chdir(directory_name)
            proc = subprocess.Popen(["stellar-core", "gen-seed"],stdout=subprocess.PIPE)
            private_keys.append(proc.stdout.readline().split()[-1].decode("utf-8"))
            public_keys.append(proc.stdout.readline().split()[-1].decode("utf-8"))
            os.chdir("..")
    for node_number in range(number_of_nodes):
        directory_name = "node-%d" % node_number
        if os.path.isdir(directory_name):
            os.chdir(directory_name)
            peers = []
            validators = ["$self"]
            for other_node_number in range(number_of_nodes):
                if node_number != other_node_number:
                    peers.append("127.0.0.1:%d" % (11625 + other_node_number))
                    validators.append(public_keys[other_node_number])
            config = config_tmpl.format(HTTP_PORT = 8080 + node_number,
                                        PEER_PORT = 11625 + node_number,
                                        PUBLIC_KEY = public_keys[node_number],
                                        PRIVATE_KEY = private_keys[node_number],
                                        KNOWN_PEERS = json.dumps(peers),
                                        VALIDATORS = json.dumps(validators),
                                        node_number = node_number)
            fobj = open("stellar-core.cfg", 'w')
            fobj.write(config)
            fobj.close()
            os.chdir("..")
