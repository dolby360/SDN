
ARPTable=[["10.0.0.1","00:00:00:00:00:01",1],
             ["10.0.0.2", "00:00:00:00:00:02",2],
             ["10.0.0.3", "00:00:00:00:00:03",3],
             ["10.0.0.4", "00:00:00:00:00:04",4],
             ["10.0.0.5", "00:00:00:00:00:05",5],
             ["10.0.0.6", "00:00:00:00:00:06",6],
             ["10.0.0.7", "00:00:00:00:00:07",7],
             ["10.0.0.8", "00:00:00:00:00:08",8]]
ipToMAC=[["10.0.0.1","00:00:00:00:00:01"],
             ["10.0.0.2", "00:00:00:00:00:02"],
             ["10.0.0.3", "00:00:00:00:00:03"],
             ["10.0.0.4", "00:00:00:00:00:04"],
             ["10.0.0.5", "00:00:00:00:00:05"],
             ["10.0.0.6", "00:00:00:00:00:06"],
             ["10.0.0.7", "00:00:00:00:00:07"],
             ["10.0.0.8", "00:00:00:00:00:08"]]

macToPort=[["00:00:00:00:00:01",1],
             ["00:00:00:00:00:02",2],
             [ "00:00:00:00:00:03",3],
             [ "00:00:00:00:00:04",4],
             [ "00:00:00:00:00:05",5],
             [ "00:00:00:00:00:06",6],
             [ "00:00:00:00:00:07",7],
             [ "00:00:00:00:00:08",8]




]

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.arp import arp
from pox.lib.addresses import IPAddr, EthAddr


def getMacByIp(ip_tofind):
  for ip in ipToMAC:
      if ip[0] == ip_tofind:
          return EthAddr(ip[1])
  # if ip_tofind==CDNIP:
  #   return EthAddr(currentServerMAC)

def makeSrcAndDst(arp_packet):
  for ip in ipToMAC:
    if ip[0] == arp_packet.protodst :
      _dst = EthAddr(ip[1])

  # if CDNIP==arp_packet.protodst:
  #   _dst=EthAddr(currentServerMAC)


  src = EthAddr(getMacByIp(arp_packet.protosrc))
  return _dst, src

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
      print "Creating fake arp reply"
      a = arp()
      a.opcode = arp.REPLY
      # if arp_packet.protodst == CDNIP:
      #   arp_packet.protodst=IPAddr(currentServerIP)

        # This function decide what answer to return
      cond(arp_packet, a, event)

def BalanceLoad(event):
  # arp_packet = event.parsed.find('arp')

  import random
  randomServer = random.choice(serversList)

  for ip in ipToMAC:
    if ip[0]== str(randomServer):

      global currentServerMAC,currentServerIP,CDNPORT
      currentServerMAC=str(ip[1])
      print "currentServerMAC : "+currentServerMAC
      currentServerIP=str(ip[0])
      for mac2P in macToPort:
        if mac2P[0]==currentServerMAC:
          CDNPORT = mac2P[1]
          print "serverPort :"+str(CDNPORT)

      print "currentServerIP : " + currentServerIP







def launch (ip, servers):
  servers = servers.replace(","," ").split()
  global serversList
  serversList = [IPAddr(x) for x in servers]
  ip = IPAddr(ip)

  for server in serversList:
      print "server : "+str(server)+" is up"
  print "Load balancer IP : "+str(ip)



  def _handle_ConnectionUp (event):
    print "switch : "+dpidToStr(event.dpid)+" connected"
    # BalanceLoad(event)
    #
    for mac_src in macToPort:
        for mac_dst in macToPort:
          if mac_src!=mac_dst:
            match = of.ofp_match()

            match = of.ofp_match()
            match.dl_src = EthAddr(mac_src[0])
            match.dl_dst = EthAddr(mac_dst[0])

            fm = of.ofp_flow_mod()
            fm.match = match
            fm.hard_timeout = 300
            fm.idle_timeout = 100

            fm.actions.append(of.ofp_action_output(port=int(mac_dst[1])))
            event.connection.send(fm)
            print "forward rule: " + str(mac_src[0]) + " > " + str(mac_dst[0]) + " via port " + str(mac_dst[1])


          # match = of.ofp_match()
          # match.dl_src = EthAddr(mac_src[0])
          # match.dl_dst = EthAddr(mac_dst[0])
          #
          # match.dl_type = 0x0800
          # match.nw_proto = 6
          # match.nw_dst=IPAddr("10.1.2.3")
          # fm = of.ofp_flow_mod()
          # fm.match = match
          # fm.hard_timeout = 300
          # fm.idle_timeout = 100
          # fm.actions.append(of.ofp_action_output(port=CDNPORT))
          # event.connection.send(fm)
          #
          # print "forward rule: "+str(mac_src[0])+" > "+str(mac_dst[0])+" via port "+str(CDNPORT)

  def _handle_PacketIn(event):
    arpRequest(event)

  core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
  core.openflow.addListenerByName("PacketIn", _handle_PacketIn)