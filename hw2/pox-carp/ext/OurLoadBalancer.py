
#"Second Backup"
# from pox.core import core
# import pox.openflow.libopenflow_01 as of
# from pox.lib.revent import *
# from pox.lib.util import dpidToStr
# from pox.lib.packet.ethernet import ethernet
# from pox.lib.packet.arp import arp
# from pox.lib.addresses import IPAddr, EthAddr
# import random
#
# ARPTable=[["10.0.0.1","00:00:00:00:00:01",1],
#              ["10.0.0.2", "00:00:00:00:00:02",2],
#              ["10.0.0.3", "00:00:00:00:00:03",3],
#              ["10.0.0.4", "00:00:00:00:00:04",4]]
#
# serversList=[["10.0.0.5", "00:00:00:00:00:05",5],
#              ["10.0.0.6", "00:00:00:00:00:06",6],
#              ["10.0.0.7", "00:00:00:00:00:07",7],
#              ["10.0.0.8", "00:00:00:00:00:08",8]]
#
# from collections import deque
#
# clientIP=None
# clientMAC=None
# clientPort=0
#
# LB_IP = IPAddr('10.1.2.3')
# LB_MAC = EthAddr('00:00:00:00:00:FE')
#
#
# def getNextServerMAC():
#
#   randServer= random.choice(serversList)
#   for ip in ARPTable:
#     if ip[0]==randServer:
#       print "getNextServer %s" %ip
#       return EthAddr(ip[1])
#
# def makeSrcAndDst(arp_packet):
#   for ip in ARPTable:
#     if ip[0] == arp_packet.protodst :
#       _dst = EthAddr(ip[1])
#     if ip[0] == arp_packet.protosrc:
#       _src = EthAddr(ip[1])
#
#   # if arp_packet.protodst == LB_IP:
#   #   _dst = LB_MAC
#   #
#   # for server in serversList:
#   #   for client in ARPTable:
#   #     if arp_packet.protodst == client[0] and arp_packet.protosrc==server[0]:
#   #       _src = server[1]
#
#   return _dst, _src
#
#
# def handle_request(packet, event):
#
#   # Get the next server to handle the request
#   serverIP = random.choice(serversList)
#   for ip in ARPTable:
#     if ip[0] == serverIP:
#       serverMAC=ip[1]
#       serverPort=ip[2]
#
#
#   "First install the reverse rule from server to client"
#   msg = of.ofp_flow_mod()
#   msg.idle_timeout = 100
#   msg.hard_timeout = 30
#   msg.buffer_id = None
#
#   # Set packet matching
#   # Match (in_port, src MAC, dst MAC, src IP, dst IP)
#   msg.match.in_port = serverPort
#   msg.match.dl_src = serverMAC
#   msg.match.dl_dst = packet.src
#   msg.match.dl_type = ethernet.IP_TYPE
#   msg.match.nw_src = serverIP
#   msg.match.nw_dst = packet.next.srcip
#
#   # Append actions
#   # Set the src IP and MAC to load balancer's
#   # Forward the packet to client's port
#   msg.actions.append(of.ofp_action_nw_addr.set_src(LB_IP))
#   msg.actions.append(of.ofp_action_dl_addr.set_src(LB_MAC))
#   msg.actions.append(of.ofp_action_output(port=event.port))
#
#   event.connection.send(msg)
#
#   "Second install the forward rule from client to server"
#   msg = of.ofp_flow_mod()
#   msg.idle_timeout = 100
#   msg.hard_timeout = 300
#   msg.buffer_id = None
#   msg.data = event.ofp  # Forward the incoming packet
#
#   # Set packet matching
#   # Match (in_port, MAC src, MAC dst, IP src, IP dst)
#   msg.match.in_port = event.port
#   msg.match.dl_src = packet.src
#   msg.match.dl_dst = LB_MAC
#   msg.match.dl_type = ethernet.IP_TYPE
#   msg.match.nw_src = packet.next.srcip
#   msg.match.nw_dst = LB_IP
#
#   # Append actions
#   # Set the dst IP and MAC to load balancer's
#   # Forward the packet to server's port
#   msg.actions.append(of.ofp_action_nw_addr.set_dst(server.ip))
#   msg.actions.append(of.ofp_action_dl_addr.set_dst(server.mac))
#   msg.actions.append(of.ofp_action_output(port=server.port))
#
#   event.connection.send(msg)
#
#   print "Installing %s <-> %s" % (packet.next.srcip, server.ip)
#
#
# def cond(arp_packet, a, event):
#   a.hwsrc, a.hwdst = makeSrcAndDst(arp_packet)
#
#   # fake reply IP
#   a.protosrc = arp_packet.protodst
#   a.protodst = arp_packet.protosrc
#
#   a.hwlen = 6
#   a.protolen = 4
#   a.hwtype = arp.HW_TYPE_ETHERNET
#   a.prototype = arp.PROTO_TYPE_IP
#
#   # create ethernet packet
#   e = ethernet()
#   e.set_payload(a)
#
#   e.src, e.dst = makeSrcAndDst(arp_packet)
#
#   e.type = ethernet.ARP_TYPE
#
#   msg = of.ofp_packet_out()
#   msg.data = e.pack()
#   # send the packet back to the source
#   msg.actions.append(of.ofp_action_output(port=event.port))
#   event.connection.send(msg)
#
#
#
# def arpRequest(event):
#   packet = event.parsed
#   arp_packet = packet.find('arp')
#
#
#   if arp_packet is not None:
#
#     if arp_packet.opcode == arp.REQUEST:
#       if arp_packet.protodst == LB_IP:
#         global clientMAC,clientIP,clientPort
#         clientIP=arp_packet.protosrc
#         clientMAC=arp_packet.hwsrc
#         clientPort=event.port
#
#         a=arp()
#         a.opcode = arp.REPLY
#         a.hwsrc=LB_MAC
#         a.hwdst=arp_packet.hwsrc
#
#         # Load balance IP
#         a.protosrc = LB_IP
#         a.protodst = arp_packet.protosrc
#
#         a.hwlen = 6
#         a.protolen = 4
#         a.hwtype = arp.HW_TYPE_ETHERNET
#         a.prototype = arp.PROTO_TYPE_IP
#
#         # create ethernet packet
#         e = ethernet()
#         e.set_payload(a)
#
#         e.src=LB_MAC
#         e.dst=arp_packet.hwsrc
#         e.type = ethernet.ARP_TYPE
#
#         msg = of.ofp_packet_out()
#         msg.data = e.pack()
#         # send the packet back to the source
#         msg.actions.append(of.ofp_action_output(port=event.port))
#         event.connection.send(msg)
#         print "created responce : "+str(LB_MAC)+" : "+str(a.protosrc)
#         return
#
#
#
#
#
#
# def launch (ip, servers):
#   servers = servers.replace(","," ").split()
#   global serversList
#   # serversList = [IPAddr(x) for x in servers]
#   global  LB_IP
#   LB_IP = IPAddr(ip)
#
#   for server in serversList:
#       print "server : "+str(server)+" is up"
#   print "Load balancer IP : "+str(LB_IP)
#
#
#
#   def _handle_ConnectionUp (event):
#     print "switch : "+dpidToStr(event.dpid)+" connected"
#
#     for mac_src in ARPTable:
#         for mac_dst in ARPTable:
#           if mac_src!=mac_dst:
#             match = of.ofp_match()
#             match.dl_src = EthAddr(mac_src[1])
#             match.dl_dst = EthAddr(mac_dst[1])
#
#             fm = of.ofp_flow_mod()
#             fm.match = match
#             fm.hard_timeout = 300
#             fm.idle_timeout = 100
#
#             fm.actions.append(of.ofp_action_output(port=int(mac_dst[2])))
#             event.connection.send(fm)
#             print "forward rule: " + str(mac_src[1]) + " > " + str(mac_dst[1]) + " via port " + str(mac_dst[2])
#
#     match = of.ofp_match()
#     match.dl_src = EthAddr("00:00:00:00:00:01")
#     match.dl_dst = LB_MAC
#
#     fm = of.ofp_flow_mod()
#     fm.match = match
#     fm.hard_timeout = 300
#     fm.idle_timeout = 100
#
#     fm.actions.append(of.ofp_action_output(port=8))
#     event.connection.send(fm)
#
#     match = of.ofp_match()
#     match.dl_dst = EthAddr("00:00:00:00:00:01")
#     match.dl_src = LB_MAC
#
#     fm = of.ofp_flow_mod()
#     fm.match = match
#     fm.hard_timeout = 300
#     fm.idle_timeout = 100
#
#     fm.actions.append(of.ofp_action_output(port=1))
#     event.connection.send(fm)
#
#   def _handle_PacketIn(event):
#     packet = event.parsed
#
#     if packet.type == packet.LLDP_TYPE or packet.type == packet.IPV6_TYPE:
#       # print "ipv6 src - "+str(packet.src)+" : type - "+str(packet.type)
#       # Drop LLDP packets
#       # Drop IPv6 packets
#
#       msg = of.ofp_packet_out()
#       msg.buffer_id = event.ofp.buffer_id
#       msg.in_port = event.port
#       event.connection.send(msg)
#
#     elif packet.type == packet.ARP_TYPE:
#       arpRequest(event)
#
#     elif packet.type == packet.IP_TYPE:
#       # Handle client's request
#       ip_packet = packet.find('ipv4')
#       print "Receive an IPv4 packet from "+str(ip_packet.srcip) +" to %s" % ip_packet.dstip
#       if ip_packet.dstip == LB_IP:
#         # waitingClients.append([arp_packet.protosrc,arp_packet.hwsrc])
#
#         match = of.ofp_match()
#         match.dl_src = EthAddr("00:00:00:00:00:01")
#         match.dl_dst = EthAddr("00:00:00:00:00:FE")
#
#         fm = of.ofp_flow_mod()
#         fm.match = match
#         fm.hard_timeout = 300
#         fm.idle_timeout = 100
#         fm.actions.append(of.ofp_action_output(port=8))
#         event.connection.send(fm)
#         print "forwarded to h8"
#         return
#
#       match = of.ofp_match()
#       match.dl_src = EthAddr("00:00:00:00:00:08")
#       match.dl_dst = EthAddr("00:00:00:00:00:01")
#
#       fm = of.ofp_flow_mod()
#       fm.match = match
#       fm.hard_timeout = 300
#       fm.idle_timeout = 100
#       fm.actions.append(of.ofp_action_output(port=1))
#       event.connection.send(fm)
#       print "forwarded to h1"
#         # a = arp()
#         # a.opcode = arp.REPLY
#         # a.protosrc = IPAddr(LB_IP)
#         # a.protodst = ip_packet.srcip
#         #
#         # a.hwlen = 6
#         # a.protolen = 4
#         # a.hwtype = arp.HW_TYPE_ETHERNET
#         # a.prototype = arp.PROTO_TYPE_IP
#         #
#         # # create ethernet packet
#         # e = ethernet()
#         # e.set_payload(a)
#         #
#         # e.src=EthAddr(LB_MAC)
#         # e.dst = clientMAC
#         #
#         # e.type = ethernet.ARP_TYPE
#         #
#         # msg = of.ofp_packet_out()
#         # msg.data = e.pack()
#         # # send the packet back to the source
#         # msg.actions.append(of.ofp_action_output(port=event.port))
#         # event.connection.send(msg)
#
#
#
#
#
#       # handle_request(packet, event)
#
#
#   core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
#   core.openflow.addListenerByName("PacketIn", _handle_PacketIn)



"BACKUP"
from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.arp import arp
from pox.lib.addresses import IPAddr, EthAddr
import random

clientList=[["10.0.0.1","00:00:00:00:00:01",1],
             ["10.0.0.2", "00:00:00:00:00:02",2],
             ["10.0.0.3", "00:00:00:00:00:03",3],
             ["10.0.0.4", "00:00:00:00:00:04",4]]

serversList=[["10.0.0.5", "00:00:00:00:00:05",5],
             ["10.0.0.6", "00:00:00:00:00:06",6],
             ["10.0.0.7", "00:00:00:00:00:07",7],
             ["10.0.0.8", "00:00:00:00:00:08",8]]

LB_IP = IPAddr('10.1.2.3')
LB_MAC = EthAddr('00:00:00:00:00:FE')
clientMAC=None
clientPort=None


def getNextServerMAC():

  randServer= random.choice(serversList)
  for ip in clientList:
    if ip[0]==randServer:
      return EthAddr(ip[1])

def makeSrcAndDst(arp_packet):
  for ip in clientList:
    if ip[0] == arp_packet.protodst :
      _dst = EthAddr(ip[1])
    if ip[0] == arp_packet.protosrc:
      _src = EthAddr(ip[1])

  for server in serversList:
    if arp_packet.protodst == LB_IP and arp_packet.protosrc == IPAddr(server[0]):
      _dst = LB_MAC
      _src = EthAddr(server[1])

  if arp_packet.protodst == LB_IP:
    _dst = LB_MAC

  if arp_packet.protosrc == LB_IP:
    _dst = clientMAC
  print "src: "+str(_src)+" > dst: "+str(_dst)
  return _dst, _src


def handle_request(packet, event):
  print "Handle request"


def cond(arp_packet, a, event):
  a.hwsrc, a.hwdst = makeSrcAndDst(arp_packet)

  # fake reply IP
  a.protosrc = arp_packet.protodst
  a.protodst = arp_packet.protosrc

  a.hwlen = 6
  a.protolen = 4
  a.hwtype = arp.HW_TYPE_ETHERNET
  a.prototype = arp.PROTO_TYPE_IP

  # create ethernet packet
  e = ethernet()
  e.set_payload(a)

  e.src, e.dst = makeSrcAndDst(arp_packet)

  e.type = ethernet.ARP_TYPE

  msg = of.ofp_packet_out()
  msg.data = e.pack()
  # send the packet back to the source
  msg.actions.append(of.ofp_action_output(port=event.port))
  event.connection.send(msg)



def arpRequest(event):
  packet = event.parsed
  arp_packet = packet.find('arp')


  if arp_packet is not None:
    if arp_packet.opcode == arp.REQUEST:
      print "Received arp request from %s" % arp_packet.hwsrc
      global clientMAC,clientPort
      clientMAC = arp_packet.hwsrc
      clientPort = event.port
      print "Creating arp reply"
      a = arp()
      a.opcode = arp.REPLY
      cond(arp_packet, a, event)

  if packet.type == packet.IP_TYPE:
    # Handle client's request

    # Only accept ARP request for load balancer
    if packet.next.dstip == LB_IP:
      return

    print "Receive an IPv4 packet from %s" % packet.next.srcip
    # self.handle_request(packet, event)



def _handle_ConnectionUp(event):
  print "switch : "+dpidToStr(event.dpid)+" connected"
  #
  # for mac_src in clientList:
  #     for mac_dst in clientList:
  #       if mac_src!=mac_dst:
  #
  #         match = of.ofp_match()
  #         match.dl_src = EthAddr(mac_src[1])
  #         match.dl_dst = EthAddr(mac_dst[1])
  #
  #         fm = of.ofp_flow_mod()
  #         fm.match = match
  #         fm.hard_timeout = 300
  #         fm.idle_timeout = 100
  #
  #         fm.actions.append(of.ofp_action_output(port=int(mac_dst[2])))
  #         event.connection.send(fm)
  #         print "forward rule: " + str(mac_src[1]) + " > " + str(mac_dst[1]) + " via port " + str(mac_dst[2])


def handle_arp(event, in_port):
  # Get the ARP request from packet
  packet = event.parse()
  arp_req = packet.next

  # Create ARP reply
  arp_rep = arp()
  arp_rep.opcode = arp.REPLY
  arp_rep.hwsrc = LB_MAC
  arp_rep.hwdst = arp_req.hwsrc
  arp_rep.protosrc = LB_IP
  arp_rep.protodst = arp_req.protosrc
  arp_rep.hwlen = 6
  arp_rep.protolen = 4
  arp_rep.hwtype = arp.HW_TYPE_ETHERNET
  arp_rep.prototype = arp.PROTO_TYPE_IP


  # Create the Ethernet packet
  eth = ethernet()
  eth.type = ethernet.ARP_TYPE
  eth.dst = packet.src
  eth.src = LB_MAC
  eth.set_payload(arp_rep)

  # Send the ARP reply to client
  msg = of.ofp_packet_out()
  msg.data = eth.pack()
  msg.actions.append(of.ofp_action_output(port=event.port))
  msg.in_port = in_port
  event.connection.send(msg)

def handle_request ( packet, event):

  server = random.choice(serversList)

  "First install the reverse rule from server to client"
  msg = of.ofp_flow_mod()
  msg.idle_timeout = 100
  msg.hard_timeout = 300
  msg.buffer_id = None

  # Set packet matching
  # Match (in_port, src MAC, dst MAC, src IP, dst IP)
  msg.match.in_port = int(server[2])
  msg.match.dl_src = EthAddr(server[1])
  msg.match.dl_dst = packet.src
  msg.match.dl_type = ethernet.IP_TYPE
  msg.match.nw_src = IPAddr(server[0])
  msg.match.nw_dst = packet.next.srcip

  # Append actions
  # Set the src IP and MAC to load balancer's
  # Forward the packet to client's port
  msg.actions.append(of.ofp_action_nw_addr.set_src(LB_IP))
  msg.actions.append(of.ofp_action_dl_addr.set_src(LB_MAC))
  msg.actions.append(of.ofp_action_output(port = event.port))

  event.connection.send(msg)

  "Second install the forward rule from client to server"
  msg = of.ofp_flow_mod()
  msg.idle_timeout = 100
  msg.hard_timeout = 300
  msg.buffer_id = None
  msg.data = event.ofp # Forward the incoming packet

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
  msg.actions.append(of.ofp_action_nw_addr.set_dst(IPAddr(server[0])))
  msg.actions.append(of.ofp_action_dl_addr.set_dst(EthAddr(server[1])))
  msg.actions.append(of.ofp_action_output(port = int(server[2])))

  event.connection.send(msg)

  print "Installing %s <-> %s" % (packet.next.srcip, server[1])

def _handle_PacketIn(event):
  packet = event.parse()

  if packet.type == packet.LLDP_TYPE or packet.type == packet.IPV6_TYPE:
    msg = of.ofp_packet_out()
    msg.buffer_id = event.ofp.buffer_id
    msg.in_port = event.port
    event.connection.send(msg)

  elif packet.type == packet.ARP_TYPE:
    # # Handle ARP request for load balancer
    # # Only accept ARP request for load balancer
    # if packet.next.protodst != LB_IP:
    #   return

    print "ARP request"
    handle_arp(event, event.port)


  elif packet.type == packet.IP_TYPE:

    # Handle client's request

    # Only accept ARP request for load balancer

    # if packet.next.dstip != LB_IP:
    #   return

    print "Receive an IPv4 packet from %s" % packet.next.srcip

    handle_request(packet, event)



def launch ():


  for server in serversList:
      print "server : "+str(server)+" is up"
  print "Load balancer IP : "+str(LB_IP)


  # core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
  core.openflow.addListenerByName("PacketIn", _handle_PacketIn)