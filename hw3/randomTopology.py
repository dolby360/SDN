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

class SampleTopology(Topo):
    def __init__(self):
        Topo.__init__(self)


    def build(self):   
        l = [] 
        #n, i.e. total number of nodes
        n = 10
        #p, i.e. the value of the probability
        p = 0.1
        #Create an empty graph add n nodes to it
        G = nx.Graph()

        for i in range(0,n):
            G.add_node(i)
        for t1 in range(0,n):
            for t2 in range(0,n):
                if t1 != t2 and random.random() < p:
                    G.add_edge(t1,t2)
                    l.append((t1,t2))
        G.add_edges_from(l)
        switchesList = [i for i in range(n)]
        G.add_path(switchesList)
        # pos = nx.spring_layout(G)
        # drawing setup for switches
        # nx.draw_networkx_nodes(G,pos,nodelis=switchesList,node_color='b',node_size=500,alpha=0.8)
        # nx.draw_networkx_edges(G,pos,edgelist=l,width=8,alpha=0.5,edge_color='y')

        data = json_graph.node_link_data(G)
        with open('../pox/ext/data.txt', 'w') as outfile:
            json.dump(data, outfile)

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
