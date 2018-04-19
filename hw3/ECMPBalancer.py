#!/usr/bin/python
from pox.core import core
from pox.lib.util import dpidToStr
from pox.openflow import *
from pox.lib.addresses import IPAddr, EthAddr
from pox.lib.packet import *
from networkx.readwrite import json_graph

import json
import networkx as nx
import matplotlib.pyplot as plt
import random

flag = True

def read_json_file(filename):
    with open(filename, 'r') as f:
      js_graph = json.load(f)
    return json_graph.node_link_graph(js_graph)

def _handle_PacketIn(event):
  #print "packet in to = %s" % dpidToStr(event.dpid)
  x = 1

def drowGraph(G):
    hostList = []
    switchesList = []
    pos = nx.networkx.spring_layout(G)

    for i in range(0,G.nodes.__len__()):
      if G.nodes[i]['data'] == 'host':
        hostList.append(i)
      if G.nodes[i]['data'] == 'switch':
        switchesList.append(i)
    nx.draw_networkx_nodes(G, pos, switchesList, node_size=500, node_color='b')
    nx.draw_networkx_nodes(G, pos, hostList, node_size=500, node_color='r')

    nx.draw_networkx_edges(G,pos)
    nx.draw_networkx_labels(G,pos)
    plt.show()


def _handle_ConnectionUp (event):
  global flag
  print "Switch with dpid=%s connected" % dpidToStr(event.dpid)
  if flag:
    G = read_json_file("ext/data.txt")
    drowGraph(G)
    flag = False
    

def _handle_ConnectionDown(event):
  print "Switch %s disconnected" % dpidToStr(event.dpid)

def launch ():
  core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
  core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
  core.openflow.addListenerByName("ConnectionDown", _handle_ConnectionDown)