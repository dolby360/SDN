
from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.arp import arp
from pox.lib.addresses import IPAddr, EthAddr
import random
# import numpy as np
import matplotlib.pyplot as plt

clientList=[[IPAddr("10.0.0.1"),EthAddr("00:00:00:00:00:01"),1],
             [IPAddr("10.0.0.2"), EthAddr("00:00:00:00:00:02"),2],
             [IPAddr("10.0.0.3"), EthAddr("00:00:00:00:00:03"),3],
             [IPAddr("10.0.0.4"), EthAddr("00:00:00:00:00:04"),4]]

serversList=[[IPAddr("10.0.0.5"), EthAddr("00:00:00:00:00:05"),5],
             [IPAddr("10.0.0.6"), EthAddr("00:00:00:00:00:06"),6],
             [IPAddr("10.0.0.7"), EthAddr("00:00:00:00:00:07"),7],
             [IPAddr("10.0.0.8"), EthAddr("00:00:00:00:00:08"),8]]

LB_IP = IPAddr('10.1.2.3')
LB_MAC = EthAddr('00:00:00:00:00:33')

IDLE_TIMEOUT=1
HARD_TIMEOUT=1

clientMAC=None
clientPort=None

serverCounter = [0,0,0,0]
requestsCounter = 0 
chartFlag = False

def handle_arp(event, in_port):
  arp_req = event.parsed.next

  # Create ARP reply
  arp_rep = arp()
  arp_rep.opcode = arp.REPLY
  arp_rep.hwsrc = LB_MAC
  arp_rep.hwdst = arp_req.hwsrc
  arp_rep.protosrc = LB_IP
  arp_rep.protodst = arp_req.protosrc

  # Create the Ethernet packet
  eth = ethernet()
  eth.type = ethernet.ARP_TYPE
  eth.dst = event.parsed.src
  eth.src = LB_MAC
  eth.set_payload(arp_rep)

  # Send the ARP reply to client
  msg = of.ofp_packet_out()
  msg.data = eth.pack()
  msg.actions.append(of.ofp_action_output(port=of.OFPP_IN_PORT))
  msg.in_port = in_port
  event.connection.send(msg)

  print "%s:%s asks who is %s and get answer %s" % (arp_req.protosrc,arp_req.hwsrc,LB_IP,LB_MAC)

def handle_request ( packet, event):
  global requestsCounter
  global serverCounter

  server = random.choice(serversList)
  print "Incrementing server number: {0}".format(serversList.index(server))
  serverCounter[serversList.index(server)] += 1
  requestsCounter += 1
  "First install the reverse rule from server to client"

  msg = of.ofp_flow_mod(command=of.OFPFC_MODIFY)
  msg.idle_timeout = IDLE_TIMEOUT
  msg.hard_timeout = HARD_TIMEOUT
  msg.buffer_id = None

  # Set packet matching
  # Match (in_port, src MAC, dst MAC, src IP, dst IP)
  msg.match.in_port = server[2]
  msg.match.dl_src = server[1]
  msg.match.dl_dst = packet.src
  msg.match.dl_type = ethernet.IP_TYPE
  msg.match.nw_src = server[0]
  msg.match.nw_dst = packet.next.srcip

  # Append actions
  # Set the src IP and MAC to load balancer's
  # Forward the packet to client's port
  msg.actions.append(of.ofp_action_nw_addr.set_src(LB_IP))
  msg.actions.append(of.ofp_action_dl_addr.set_src(LB_MAC))
  msg.actions.append(of.ofp_action_output(port=event.port))

  event.connection.send(msg)

  "Second install the forward rule from client to server"

  msg = of.ofp_flow_mod(command=of.OFPFC_MODIFY)
  msg.idle_timeout = IDLE_TIMEOUT
  msg.hard_timeout = HARD_TIMEOUT
  msg.buffer_id = None
  msg.data = event.ofp  # Forward the incoming packet

  # Set packet matching
  # Match (in_port, MAC src, MAC dst, IP src, IP dst)
  msg.match.in_port = event.port
  msg.match.dl_src = packet.src
  msg.match.dl_dst = LB_MAC
  msg.match.dl_type = ethernet.IP_TYPE
  msg.match.nw_src = packet.next.srcip
  msg.match.nw_dst = LB_IP

  # Append actions
  # Set the dst IP and MAC to load balancer's
  # Forward the packet to server's port
  msg.actions.append(of.ofp_action_nw_addr.set_dst(server[0]))
  msg.actions.append(of.ofp_action_dl_addr.set_dst(server[1]))
  msg.actions.append(of.ofp_action_output(port=server[2]))

  event.connection.send(msg)
  # msg = of.ofp_flow_mod(command=of.OFPFC_DELETE)
  # event.connection.send(msg)
  print "Installing %s <-> %s" % (packet.next.srcip, server[0])

def getMacByIp(i):
  if i == '10.0.0.1': 
    return '00:00:00:00:00:01'
  if i == '10.0.0.2': 
    return '00:00:00:00:00:02'
  if i == '10.0.0.3': 
    return '00:00:00:00:00:03'
  if i == '10.0.0.4': 
    return '00:00:00:00:00:04'

def makeSrcAndDst(arp_packet):
  if arp_packet.protodst == '10.0.0.1':
    _dst = EthAddr('00:00:00:00:00:01')
  if arp_packet.protodst == '10.0.0.2':
    _dst = EthAddr('00:00:00:00:00:02')
  if arp_packet.protodst == '10.0.0.3':
    _dst = EthAddr('00:00:00:00:00:03')
  if arp_packet.protodst == '10.0.0.4':
    _dst = EthAddr('00:00:00:00:00:04')
  return _dst, EthAddr(getMacByIp(arp_packet.protosrc))

def cond(arp_packet,a,event):
  a.hwsrc,a.hwdst = makeSrcAndDst(arp_packet)

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
  e.src, e.dst = makeSrcAndDst(arp_packet)
  e.type = ethernet.ARP_TYPE

  msg = of.ofp_packet_out()
  msg.data = e.pack()
  #send the packet back to the source

  msg.actions.append( of.ofp_action_output( port = event.port ) )
  event.connection.send( msg )

def _handle_PacketIn(event):
  clientsIPs = [IPAddr("10.0.0.1"),IPAddr("10.0.0.2"),IPAddr("10.0.0.3"),IPAddr("10.0.0.4")]
  packet = event.parse()

  if packet.type == packet.LLDP_TYPE or packet.type == packet.IPV6_TYPE:
    msg = of.ofp_packet_out()
    msg.buffer_id = event.ofp.buffer_id
    msg.in_port = event.port
    event.connection.send(msg)

  elif packet.type == packet.ARP_TYPE and packet.find('arp').protodst in clientsIPs and packet.find('arp').protosrc in clientsIPs:
    packet = event.parsed
    arp_packet = packet.find('arp')
    if arp_packet is not None:      
      if arp_packet.opcode == arp.REQUEST:
        print "Received arp request from %s" % arp_packet.hwsrc
        print "Creating fake arp reply"
        #create arp packet
        a = arp()
        a.opcode = arp.REPLY
        #This function decide what answer to return
        cond(arp_packet,a,event)

  #If ARP for the load balancer, then we replay a general answer for all the hosts.
  elif packet.type == packet.ARP_TYPE:
    arp_pack = packet.find('arp')

    if packet.next.protodst != LB_IP:
      for client in clientList:
        if client[0]==packet.next.protodst:
          a = arp()
          a.opcode = arp.REPLY
          a.hwsrc, a.hwdst = client[1],arp_pack.hwsrc

          # fake reply IP
          a.protosrc = arp_pack.protodst
          a.protodst = arp_pack.protosrc
          a.hwlen = 6
          a.protolen = 4
          a.hwtype = arp.HW_TYPE_ETHERNET
          a.prototype = arp.PROTO_TYPE_IP

          # create ethernet packet
          e = ethernet()
          e.set_payload(a)

          e.src, e.dst = client[1],arp_pack.hwsrc

          e.type = ethernet.ARP_TYPE

          msg = of.ofp_packet_out()
          msg.data = e.pack()
          # send the packet back to the source
          msg.actions.append(of.ofp_action_output(port=event.port))
          event.connection.send(msg)

    print "ARP request from %s : %s to %s : %s" % (arp_pack.hwsrc,arp_pack.protosrc, arp_pack.hwdst,arp_pack.protodst)
    handle_arp(event, event.port)

  #If the destination is not for the load balancer, kill the packet.
  elif packet.type == packet.IP_TYPE:
    if packet.next.dstip != LB_IP:
      return

    print "Receive an IPv4 packet from %s" % packet.next.srcip

    handle_request(packet, event)

def _handle_ConnectionDown(event):
  #print "Switch %s disconnected" % dpidToStr(event.dpid)
  global chartFlag
  global serverCounter
  if chartFlag == False:
    chartFlag = True
    hostsNames = ['H5','H6','H7','H8']
    plt.bar(hostsNames,serverCounter,label = 'Hosts distribution')
    plt.xlabel('Hosts')
    plt.ylabel('Requests')
    plt.title('Distribution of flows\nserviced by servers')
    plt.legend()
    plt.show()

def _handle_ConnectionUp(event):
  print "Switch with dpid=%s connected " % dpidToStr(event.dpid)
  global chartFlag
  global clientList
  chartFlag = False

  for cli1 in clientList:
    for cli2 in clientList:
      if cli1[1] != cli2[1] and dpidToStr(event.dpid) == '00-00-00-00-01-01':
        match = of.ofp_match()
        match.dl_src = cli1[1]
        match.dl_dst = cli2[1]
        
        fm = of.ofp_flow_mod()
        fm.match = match
        fm.hard_timeout = of.OFP_FLOW_PERMANENT
        fm.idle_timeout = of.OFP_FLOW_PERMANENT
        fm.actions.append(of.ofp_action_output(port=cli2[2]))
        event.connection.send(fm)



def launch ():
  # for server in serversList:
  #     print "server : "+str(server)+" is up"
  # print "Load balancer IP : "+str(LB_IP)

  # core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
  core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
  core.openflow.addListenerByName("ConnectionDown", _handle_ConnectionDown)
  core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
