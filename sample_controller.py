from pox.core import core
from pox.lib.util import dpidToStr
from pox.openflow import *
from pox.lib.addresses import IPAddr, EthAddr
from pox.lib.packet import *

host1 = ('10.0.0.1','00:00:00:00:00:01')
host2 = ('10.0.0.2','00:00:00:00:00:02')
host3 = ('10.0.0.3','00:00:00:00:00:03')
host4 = ('10.0.0.4','00:00:00:00:00:04')


hostArr = [host1,host2,host3,host4]

def _handle_PacketIn(event):
  packet = event.parsed
  arp_packet = packet.find('arp')

  if arp_packet is not None:      
      if arp_packet.opcode == arp.REQUEST:
          print "Received arp request from %s" % arp_packet.hwsrc
          print "Dest - %s"% arp_packet.protodst
          #print "Dest - %s"% arp_packet.pdst
          


          for i in hostArr:
            if i[0] == arp_packet.protodst:
              print "Creating fake arp reply"
              #create arp packet
              a = arp()
              a.opcode = arp.REPLY
              a.hwsrc = EthAddr(arp_packet.hwsrc)
              a.hwdst = EthAddr(i[1])

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
              e.src = EthAddr(i[1])#insert src MAC address to packet
              e.dst = EthAddr(arp_packet.hwsrc)          
              e.type = ethernet.ARP_TYPE

              msg = of.ofp_packet_out()
              msg.data = e.pack()
          
              #send the packet back to the source
              msg.actions.append( of.ofp_action_output( port = event.port ) )
              event.connection.send( msg )
  

def _handle_ConnectionUp (event):
  print "Switch with dpid=%s connected" % dpidToStr(event.dpid)

  # #create flow match rule
  match = of.ofp_match()
  match.dl_src = EthAddr('00:00:00:00:00:01')
  match.dl_dst = EthAddr('00:00:00:00:00:02')

  fm = of.ofp_flow_mod()
  fm.match = match
  fm.hard_timeout = 300
  fm.idle_timeout = 100
  fm.actions.append(of.ofp_action_output(port=4))

  event.connection.send(fm)

  match = of.ofp_match()
  match.dl_src = EthAddr('00:00:00:00:00:02')
  match.dl_dst = EthAddr('00:00:00:00:00:01')

  fm = of.ofp_flow_mod()
  fm.match = match
  fm.hard_timeout = 300
  fm.idle_timeout = 100
  fm.actions.append(of.ofp_action_output(port=3))

  event.connection.send(fm)


def _handle_ConnectionDown(event):
  print "Switch %s disconnected" % dpidToStr(event.dpid)


def launch ():
  core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
  core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
  core.openflow.addListenerByName("ConnectionDown", _handle_ConnectionDown)
