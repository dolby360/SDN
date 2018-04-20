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

def exportNetworkxJson(G):
    data = json_graph.node_link_data(G)
    with open('../pox/ext/data.txt', 'w') as outfile:
        json.dump(data, outfile)



class SampleTopology(Topo):
    def __init__(self):
        Topo.__init__(self)

    def makeTopoFromNX(self,G):
        allHosts = []
        allSwitches = []

        hostList = []
        switchesList = []
        for i in range(0,G.nodes.__len__()):
            if G.nodes[i]['data'] == 'host':
                hostList.append(i)
            if G.nodes[i]['data'] == 'switch':
                switchesList.append(i)

        for i in hostList:
            _ip = '10.0.0.' + str(i)
            if i < 10:
                _mac = '00:00:00:00:00:0' + str(i)
            if i >= 10:
                _mac = '00:00:00:00:00:' + str(i)
            _name = 'h' + str(i)
            allHosts.append(self.addHost(_name,ip=_ip,mac=_mac))
        for i in switchesList:
            if i < 10:
                _dpid = '00:00:00:00:00:0' + str(i)
            if i >= 10:
                _dpid = '00:00:00:00:00:' + str(i)
            _name = 's' + str(i)
            allSwitches.append(self.addSwitch(_name,dpid=_dpid))
        print ''
        print 'HOSTS'
        print allHosts
        print ''
        print 'SITCHES'
        print allSwitches
        print ''
        port = 0
        allEdgesDict = {}
        for i in switchesList:
            #Make link between every edge
            for j in list(G.adj[i]):
                if not allEdgesDict.has_key(str((str(j),str(i)))): #and not allEdgesDict.has_key(str((str(i),str(j)))):
                    if j in hostList:
                        h1 = 'h' + str(j)
                    if j in switchesList:
                        h1 = 's' + str(j)
                    if i in switchesList:
                        h2 = 's' + str(i)
                    if i in hostList:
                        h2 = 'h' + str(i)
                    # print '{0}  {1}  {2}'.format(j,i,port)
                    self.addLink(h1,h2,port1=port, port2=(port+1))
                    allEdgesDict[str((str(i),str(j)))] = port
                    allEdgesDict[str((str(j),str(i)))] = port+1
                    port+=2
        # j = json.dumps(allEdgesDict)
        # f = open('../pox/ext/allEdgesDict.txt', 'w')
        # print >> f, j
        # f.close()
        with open('../pox/ext/allEdgesDict.txt', 'w') as fp:
            json.dump(allEdgesDict, fp)
    def build(self):   
        switchesNumber = 10
        G = BuildSwitchs(switchesNumber,0.1)
        G = BuildHosts(5,G,switchesNumber)
        exportNetworkxJson(G)
        self.makeTopoFromNX(G)

topo = SampleTopology()

net = Mininet(topo=topo, controller=lambda name: RemoteController(name, ip='127.0.0.1', protocol='tcp', port = 6633), link=TCLink)

net.start()
CLI(net)
net.stop()
