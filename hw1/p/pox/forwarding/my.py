from pox.core import core
from pox.lib.util import dpidToStr
from pox.openflow import *
from pox.lib.addresses import IPAddr, EthAddr
from pox.lib.packet import *

dl_src = '00:00:00:00:00:01'
dl_dst = '00:00:00:00:00:02'


def _handle_PacketIn(event):

  packet = event.parsed
  dl_src=packet.src
  dl_dst=packet.dst
  arp_packet = packet.find('arp')

  if arp_packet is not None:
    if arp_packet.opcode == arp.REQUEST:
      print "Received arp request from %s" % arp_packet.hwsrc
      print "Creating fake arp reply"

      # create arp packet
      a = arp()
      a.opcode = arp.REPLY

      # if request from h1, fake reply from h2
      if arp_packet.hwsrc == EthAddr(dl_src):
        a.hwsrc = EthAddr(dl_dst)
        a.hwdst = EthAddr(dl_src)

      # the opposite
      elif arp_packet.hwsrc == EthAddr(dl_dst):
        a.hwsrc = EthAddr(dl_src)
        a.hwdst = EthAddr(dl_dst)

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

      if arp_packet.hwsrc == EthAddr(dl_src):
        e.src = EthAddr(dl_dst)
        e.dst = EthAddr(dl_src)
      elif arp_packet.hwsrc == EthAddr(dl_dst):
        e.src = EthAddr(dl_src)
        e.dst = EthAddr(dl_dst)

      e.type = ethernet.ARP_TYPE

      msg = of.ofp_packet_out()
      msg.data = e.pack()

      # send the packet back to the source
      msg.actions.append(of.ofp_action_output(port=event.port))
      event.connection.send(msg)


def _handle_ConnectionUp(event):
  print "Switch with dpid=%s connected" % dpidToStr(event.dpid)

  # create flow match rule
  # for each packet from h1 to h2 forward via port 3
  match = of.ofp_match()
  match.dl_src = EthAddr(dl_src)
  match.dl_dst = EthAddr(dl_dst)

  fm = of.ofp_flow_mod()
  fm.match = match
  fm.hard_timeout = 300
  fm.idle_timeout = 100
  fm.actions.append(of.ofp_action_output(port=4))

  event.connection.send(fm)

  # create flow match rule
  # for each packet from h2 to h1 forward via port 2
  match = of.ofp_match()
  match.dl_src = EthAddr(dl_dst)
  match.dl_dst = EthAddr(dl_src)

  fm = of.ofp_flow_mod()
  fm.match = match
  fm.hard_timeout = 300
  fm.idle_timeout = 100
  fm.actions.append(of.ofp_action_output(port=3))

  event.connection.send(fm)


def _handle_ConnectionDown(event):
  print "Switch %s disconnected" % dpidToStr(event.dpid)


def launch():
  core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
  core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
  core.openflow.addListenerByName("ConnectionDown", _handle_ConnectionDown)
# from pox.core import core
# import pox.openflow.libopenflow_01 as of
# from pox.lib.util import dpidToStr
# from pox.openflow import *
# import csv
# firewallRules={}
# table = {}
#
#
# all_ports = of.OFPP_FLOOD
# log = core.getLogger()
#
# def _handle_PacketIn(event):
#   def drop(duration=None):
#     """
#     Drops this packet and optionally installs a flow to continue
#     dropping similar ones for a while
#     """
#     if duration is not None:
#       if not isinstance(duration, tuple):
#         duration = (duration, duration)
#       msg = of.ofp_flow_mod()
#       msg.match = of.ofp_match.from_packet(packet)
#       msg.idle_timeout = duration[0]
#       msg.hard_timeout = duration[1]
#       msg.buffer_id = event.ofp.buffer_id
#       event.connection.send(msg)
#     elif event.ofp.buffer_id is not None:
#       msg = of.ofp_packet_out()
#       msg.buffer_id = event.ofp.buffer_id
#       msg.in_port = event.port
#       msg.in_port = event.port
#       event.connection.send(msg)
#   packet = event.parsed
#
#
#
#   # Learn the source
#   table[(event.connection, packet.src)] = event.port
#
#   dst_port = table.get((event.connection, packet.dst))
#
#   if dst_port is None:
#     # We don't know where the destination is yet.  So, we'll just
#     # send the packet out all ports (except the one it came in on!)
#     # and hope the destination is out there somewhere. :)
#     msg = of.ofp_packet_out(data=event.ofp)
#     msg.actions.append(of.ofp_action_output(port=all_ports))
#     event.connection.send(msg)
#   else:
#     # Since we know the switch ports for both the source and dest
#     # MACs, we can install rules for both directions.
#     msg = of.ofp_flow_mod()
#     msg.match.dl_dst = packet.src
#
#     msg.match.dl_src = packet.dst
#
#
#     msg.actions.append(of.ofp_action_output(port=event.port))
#     event.connection.send(msg)
#
#     # This is the packet that just came in -- we want to
#     # install the rule and also resend the packet.
#     msg = of.ofp_flow_mod()
#     msg.data = event.ofp  # Forward the incoming packet
#     msg.match.dl_src = packet.src
#     msg.match.dl_dst = packet.dst
#     msg.actions.append(of.ofp_action_output(port=dst_port))
#     event.connection.send(msg)
#
#     log.debug("Installing %s <-> %s" % (packet.src, packet.dst))
#
#
# def _handle_ConnectionUp (event):
#   print "Switch with dpid=%s connected" % dpidToStr(event.dpid)
#   # destinationMAC = str(packet.dst)
#   # sourceMAC = str(packet.src)
#   #
#   # if (sourceMAC, destinationMAC) in firewallRules.values() or (destinationMAC, sourceMAC) in firewallRules.values():
#   #   print "DROP"
#
# def _handle_ConnectionDown(event):
#   print "Switch %s disconnected" % dpidToStr(event.dpid)
#
#
# def launch ():
#   with open('../firewall-policies.csv') as csvfile:
#     reader = csv.DictReader(csvfile)
#     for row in reader:
#       firewallRules[row['id']] = row['mac_0'], row['mac_1']
#
#   core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
#   core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
#   core.openflow.addListenerByName("ConnectionDown", _handle_ConnectionDown)