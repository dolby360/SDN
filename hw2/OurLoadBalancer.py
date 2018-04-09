
from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.arp import arp
from pox.lib.addresses import IPAddr, EthAddr
import random

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
clientMAC=None
clientPort=None



def _handle_ConnectionUp(event):
  print "switch : "+dpidToStr(event.dpid)+" connected"


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

IDLE_TIMEOUT=100
HARD_TIMEOUT=300

def handle_request ( packet, event):

  server = random.choice(serversList)

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

def _handle_PacketIn(event):
  packet = event.parse()

  if packet.type == packet.LLDP_TYPE or packet.type == packet.IPV6_TYPE:
    msg = of.ofp_packet_out()
    msg.buffer_id = event.ofp.buffer_id
    msg.in_port = event.port
    event.connection.send(msg)

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


  elif packet.type == packet.IP_TYPE:

    if packet.next.dstip != LB_IP:
      return

    print "Receive an IPv4 packet from %s" % packet.next.srcip

    handle_request(packet, event)



def launch ():


  for server in serversList:
      print "server : "+str(server)+" is up"
  print "Load balancer IP : "+str(LB_IP)


  # core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
  core.openflow.addListenerByName("PacketIn", _handle_PacketIn)