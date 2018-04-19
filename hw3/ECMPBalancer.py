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
G = None 

def read_json_file(filename):
    with open(filename, 'r') as f:
      js_graph = json.load(f)
    return json_graph.node_link_graph(js_graph)

def makeRules(event):
  global G
  packet = event.parsed
  arp_packet = packet.find('arp')
  print '----------------------------------------------------------'
  hostDst = int(str(arp_packet.protodst).split('.')[3])
  hostSrc = int(str(arp_packet.protosrc).split('.')[3])
  print(nx.shortest_path(G,source=hostSrc,target=hostDst))
  drowGraph(G)
  print '-----------------------------------------------------------'

def arpRequest(event):
  packet = event.parsed
  arp_packet = packet.find('arp')
  if arp_packet is not None:      
    if arp_packet.opcode == arp.REQUEST:
      print "Received arp request from %s" % arp_packet.hwsrc
      print "Creating fake arp reply"
      #create arp packet
      a = arp()
      a.opcode = arp.REPLY
      a.hwdst = arp_packet.hwsrc
      #FIXME: Maybe in the future we can use cleverer logic here to response ARP request.
      #Now I just assume that if ip ends with 10 for example 10.0.0.10 then the mac address is 00:00:00:00:00:10
      #One way I that can think of is to save mac addresses in JSON file and make more cleverers rules.
      hostNumber = int(str(arp_packet.protodst).split('.')[3])
      if hostNumber < 10:
        a.hwsrc = EthAddr('00:00:00:00:00:0' + str(hostNumber))
      else:
        a.hwsrc = EthAddr('00:00:00:00:00:' + str(hostNumber))
      #fake reply IP
      a.protosrc = arp_packet.protodst
      a.protodst = arp_packet.protosrc
      a.hwlen = 6
      a.protolen = 4
      a.hwtype = arp.HW_TYPE_ETHERNET
      a.prototype = arp.PROTO_TYPE_IP            
      #create ethernet packet
      e = ethernet()
      e.set_payload(a)
      e.src, e.dst = a.hwsrc, a.hwdst
      e.type = ethernet.ARP_TYPE
      msg = of.ofp_packet_out()
      msg.data = e.pack()
      #send the packet back to the source
      msg.actions.append( of.ofp_action_output( port = event.port ) )
      event.connection.send( msg )
      makeRules(event)

def _handle_PacketIn(event):
  #print "packet in to = %s" % dpidToStr(event.dpid)
  arpRequest(event)

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
  global G
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