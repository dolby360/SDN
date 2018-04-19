#!/usr/bin/python
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.node import RemoteController

import networkx as nx
import matplotlib.pyplot as plt
import random
import json
from networkx.readwrite import json_graph

#n, i.e. total number of nodes
#p, i.e. the value of the probability
def BuildSwitchs(n,p):
    l = [] 
    #Create an empty graph add n nodes to it
    G = nx.Graph()
    for i in range(0,n):
        G.add_node(i,data='switch')
    for t1 in range(0,n):
        for t2 in range(0,n):
            if t1 != t2 and random.random() < p:
                G.add_edge(t1,t2)
                l.append((t1,t2))
    G.add_edges_from(l)
    switchesList = [i for i in range(n)]
    G.add_path(switchesList)
    return G

#G - graph
def BuildHosts(hostsNumber,G,switchesNumber):
    for i in range(switchesNumber, (switchesNumber - 1) + hostsNumber):
        G.add_node(i,data='host')
    #Adding edge between hosts to random switch.
    for i in range(switchesNumber, (switchesNumber - 1) + hostsNumber):
        nodeToAttach = random.randint(0,switchesNumber-1)
        G.add_edge(i,nodeToAttach)
    return G

def exportJson(G):
    data = json_graph.node_link_data(G)
    with open('../pox/ext/data.txt', 'w') as outfile:
        json.dump(data, outfile)

class SampleTopology(Topo):
    def __init__(self):
        Topo.__init__(self)
    def build(self):   
        switchesNumber = 10
        G = BuildSwitchs(switchesNumber,0.1)
        G = BuildHosts(5,G,switchesNumber)
        exportJson(G)

        # Add hosts and switches
        h1 = self.addHost('h1', ip='10.0.0.1', mac='00:00:00:00:00:01')
        s1 = self.addSwitch('s1', dpid='00:00:00:00:00:11')

        # Add links
        self.addLink(h1,s1,port1=1, port2=3)


topo = SampleTopology()

net = Mininet(topo=topo, controller=lambda name: RemoteController(name, ip='127.0.0.1', protocol='tcp', port = 6633), link=TCLink)

net.start()
CLI(net)
net.stop()
