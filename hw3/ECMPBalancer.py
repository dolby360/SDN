#!/usr/bin/python
from pox.core import core
from pox.lib.util import dpidToStr
from pox.openflow import *
from pox.lib.addresses import IPAddr, EthAddr
from pox.lib.packet import *
from networkx.readwrite import json_graph
from threading import Thread
from time import sleep
from multiprocessing import Process


import json
import networkx as nx
import matplotlib.pyplot as plt
import random

flag = True
G = None 
allShortestPath = []
direction = {}
SPgraphShowHolder = []
SPgraphShowHolder_secoundTime = []

def read_json_file(filename):
    with open(filename, 'r') as f:
      js_graph = json.load(f)
    return json_graph.node_link_graph(js_graph)

def showShortestPath(event):
  global G
  packet = event.parsed
  arp_packet = packet.find('arp')
  print '----------------------------------------------------------'
  hostDst = int(str(arp_packet.protodst).split('.')[3])
  hostSrc = int(str(arp_packet.protosrc).split('.')[3])
  listOfTheShortestPath = nx.shortest_path(G,source=hostSrc,target=hostDst)
  print listOfTheShortestPath
  drowGraph(G,listOfTheShortestPath)
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
      
      print 'Response {0} to port {1}'.format(a.hwsrc, event.port) 
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
      global SPgraphShowHolder
      if (a.protosrc,a.protodst) not in SPgraphShowHolder and (a.protodst,a.protosrc) not in SPgraphShowHolder:
        SPgraphShowHolder.append((a.protosrc,a.protodst))
      elif (a.protosrc,a.protodst) not in SPgraphShowHolder_secoundTime and (a.protodst,a.protosrc) not in SPgraphShowHolder_secoundTime:
        SPgraphShowHolder_secoundTime.append((a.protosrc,a.protodst))
        showShortestPath(event)

def _handle_PacketIn(event):
  #print "packet in to = %s" % dpidToStr(event.dpid)
  arpRequest(event)

def drowGraph(G,edgesToPaint = None):
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

    if edgesToPaint:
      tuplesOfSpecialEdges = []
      for i in range(0,edgesToPaint.__len__()-1):
        tuplesOfSpecialEdges.append((edgesToPaint[i],edgesToPaint[i+1]))
      # outherEdges = list(set(G.edges)-set(tuplesOfSpecialEdges)) + list(set(tuplesOfSpecialEdges)-set(G.edges))      
      nx.draw_networkx_edges(G,pos, width=2.0,edge_color='k')
      nx.draw_networkx_edges(G,pos,edgelist=tuplesOfSpecialEdges, width=2.3,edge_color='r')
    else:
      nx.draw_networkx_edges(G,pos)
    nx.draw_networkx_labels(G,pos)
    plt.show()

def createTheRule(event,h1,h2,outPort):
  match = of.ofp_match()
  match.dl_src = EthAddr(h1)
  match.dl_dst = EthAddr(h2)

  fm = of.ofp_flow_mod()
  fm.match = match
  fm.hard_timeout = 300
  fm.idle_timeout = 100

  fm.actions.append(of.ofp_action_output(port=int(outPort)))
  event.connection.send(fm)

def makeRules(event):
  global G
  global direction
  hostList = []
  switchesList = []
  for i in range(0,G.nodes.__len__()):
    if G.nodes[i]['data'] == 'host':
      hostList.append(i)
    if G.nodes[i]['data'] == 'switch':
      switchesList.append(i)
  for i in hostList:
    for j in hostList:
      if i != j:
        SPbetweenToHosts = nx.shortest_path(G,source=i,target=j)
        try:
          numberOfThisSwitch = int(dpidToStr(event.dpid).split('-')[5])
          if int(dpidToStr(event.dpid).split('-')[0]) != 0 or int(dpidToStr(event.dpid).split('-')[1]) != 0:
            numberOfThisSwitch = 0
        except:
          numberOfThisSwitch = 0
        if numberOfThisSwitch in SPbetweenToHosts:
          indexOfThisSwitch = SPbetweenToHosts.index(numberOfThisSwitch)
          if i < 10:
            h1 = '00:00:00:00:00:0' + str(i)
          if i >= 10:
            h1 = '00:00:00:00:00:' + str(i)
          if j < 10:
            h2 = '00:00:00:00:00:0' + str(j)
          if j >= 10:
            h2 = '00:00:00:00:00:' + str(j)
          outPort = direction[(SPbetweenToHosts[indexOfThisSwitch + 1],numberOfThisSwitch)]
          # if numberOfThisSwitch == 0:
            # print '*/*/*/*/*/*/*/*/*/*/*/*/*/* /*/ */ */ */*/ */ * /*/ */ * /* /*/ */* /* *  '
            # print 'Out port'
            # print outPort
            # print '*/*/*/*/*/*/*/*/*/*/*/*/*/* /*/ */ */ */*/ */ * /*/ */ * /* /*/ */* /* *  '
            # print '*/*/*/*/*/*/*/*/*/*/*/*/*/* /*/ */ */ */*/ */ * /*/ */ * /* /*/ */* /* *  '
            # print 'Host1  host2'
            # print str(i) + '  ' + str(j)
            # print str(numberOfThisSwitch) + '   ' + str(SPbetweenToHosts[indexOfThisSwitch + 1])
            # print '*/*/*/*/*/*/*/*/*/*/*/*/*/* /*/ */ */ */*/ */ * /*/ */ * /* /*/ */* /* *  '
            # print '*/*/*/*/*/*/*/*/*/*/*/*/*/* /*/ */ */ */*/ */ * /*/ */ * /* /*/ */* /* *  '
            # print 'Dict'
            # print direction
            # print '*/*/*/*/*/*/*/*/*/*/*/*/*/* /*/ */ */ */*/ */ * /*/ */ * /* /*/ */* /* *  '
          createTheRule(event,h1,h2,outPort)
       

def makeInitialRules(event):
  global G
  global allShortestPath
  hostList = []
  switchesList = []
  global direction
  for i in range(0,G.nodes.__len__()):
    if G.nodes[i]['data'] == 'host':
      hostList.append(i)
    if G.nodes[i]['data'] == 'switch':
      switchesList.append(i)

  for i in hostList:
    for j in hostList:
      if i != j:
        SPbetweenToHosts = nx.shortest_path(G,source=i,target=j)
        allShortestPath.append(SPbetweenToHosts)
        edgesDict = eval(open('ext/allEdgesDict.txt', 'r').read())
        for i in edgesDict:
          keysOfRouting = (int(i.replace('(','').replace(')','').replace('\'','').replace(',','').split(' ')[0]),int(i.replace('(','').replace(')','').replace('\'','').replace(',','').split(' ')[1]))
          direction[keysOfRouting] = edgesDict[i] 
        
        break

def _handle_ConnectionUp (event):
  global flag
  global G
  print "Switch with dpid=%s connected" % dpidToStr(event.dpid)
  if flag:
    G = read_json_file("ext/data.txt")
    drowGraph(G)
    flag = False
    makeInitialRules(event)
  makeRules(event)

def _handle_ConnectionDown(event):
  print "Switch %s disconnected" % dpidToStr(event.dpid)
  global flag
  flag = True

def launch ():
  core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
  core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
  core.openflow.addListenerByName("ConnectionDown", _handle_ConnectionDown)