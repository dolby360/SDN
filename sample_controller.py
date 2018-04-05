from pox.core import core
from pox.lib.util import dpidToStr
from pox.openflow import *
from pox.lib.addresses import IPAddr, EthAddr
from pox.lib.packet import *
import csv
import os

policies = []

#-------------------------------ARP--------------------------------------#
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
      
      #This function decide what answer to return
      cond(arp_packet,a,event)

#------------------------------------------------------------------------#
#--------------------------------Route-----------------------------------#
allMacs = ['00:00:00:00:00:01','00:00:00:00:00:02','00:00:00:00:00:03','00:00:00:00:00:04']

def siteA(event,vid):
  hosts = ['00:00:00:00:00:01','00:00:00:00:00:02']
  hosDict = {'00:00:00:00:00:01':3,'00:00:00:00:00:02':4}
  direction = [
    ['00:00:00:00:00:01','00:00:00:00:00:03',1,False],
    ['00:00:00:00:00:01','00:00:00:00:00:03',2,True],
    ['00:00:00:00:00:01','00:00:00:00:00:04',1,False],
    ['00:00:00:00:00:01','00:00:00:00:00:04',2,True],

    ['00:00:00:00:00:02','00:00:00:00:00:03',1,False],
    ['00:00:00:00:00:02','00:00:00:00:00:03',2,True],
    ['00:00:00:00:00:02','00:00:00:00:00:04',1,False],
    ['00:00:00:00:00:02','00:00:00:00:00:04',2,True],
  ]
  for item in direction:
    if vid == item[3]:
      #create flow match rule
      match = of.ofp_match()
      match.dl_src = EthAddr(item[0])
      match.dl_dst = EthAddr(item[1])

      fm = of.ofp_flow_mod()
      fm.match = match
      fm.hard_timeout = 300
      fm.idle_timeout = 100

      fm.actions.append(of.ofp_action_output(port=int(item[2])))
      event.connection.send(fm)
  for macs in allMacs:
    for hos in hosts:
      if macs != hos:
        #create flow match rule
        match = of.ofp_match()
        match.dl_src = EthAddr(macs)
        match.dl_dst = EthAddr(hos)
        
        fm = of.ofp_flow_mod()
        fm.match = match
        fm.hard_timeout = 300
        fm.idle_timeout = 100
        fm.actions.append(of.ofp_action_output(port=hosDict[hos]))
        event.connection.send(fm)

def siteB(event,vid):
  #All hosts in this site
  hosts = ['00:00:00:00:00:03','00:00:00:00:00:04']
  #If we want to reach a host, what is the port we need to go to.
  hosDict = {'00:00:00:00:00:03':3,'00:00:00:00:00:04':4}
  #If we want to get out, so to which "switch" do we need to go?
  direction = [
    ['00:00:00:00:00:03','00:00:00:00:00:01',1,False],
    ['00:00:00:00:00:03','00:00:00:00:00:01',2,True],
    ['00:00:00:00:00:03','00:00:00:00:00:02',1,False],
    ['00:00:00:00:00:03','00:00:00:00:00:02',2,True],

    ['00:00:00:00:00:04','00:00:00:00:00:01',1,False],
    ['00:00:00:00:00:04','00:00:00:00:00:01',2,True],
    ['00:00:00:00:00:04','00:00:00:00:00:02',1,False],
    ['00:00:00:00:00:04','00:00:00:00:00:02',2,True],
  ]
  for item in direction:
    if vid == item[3]:
      #create flow match rule
      match = of.ofp_match()
      match.dl_src = EthAddr(item[0])
      match.dl_dst = EthAddr(item[1])

      fm = of.ofp_flow_mod()
      fm.match = match
      fm.hard_timeout = 300
      fm.idle_timeout = 100
      fm.actions.append(of.ofp_action_output(port=int(item[2])))
      event.connection.send(fm)
  for macs in allMacs:
    for hos in hosts:
      if macs != hos:
        #create flow match rule
        match = of.ofp_match()
        match.dl_src = EthAddr(macs)
        match.dl_dst = EthAddr(hos)

        fm = of.ofp_flow_mod()
        fm.match = match
        fm.hard_timeout = 300
        fm.idle_timeout = 100
        fm.actions.append(of.ofp_action_output(port=hosDict[hos]))
        event.connection.send(fm)

#For s3 and s2
def noSite(event):
  fromSiteA = ['00:00:00:00:00:01','00:00:00:00:00:02']
  fromSiteB = ['00:00:00:00:00:03','00:00:00:00:00:04']
  for sA in fromSiteA:
    for sB in fromSiteB: 
      #create flow match rule
      match = of.ofp_match()
      match.dl_src = EthAddr(sA)
      match.dl_dst = EthAddr(sB)
      
      fm = of.ofp_flow_mod()
      fm.match = match
      fm.hard_timeout = 300
      fm.idle_timeout = 100
      fm.actions.append(of.ofp_action_output(port=2))
      event.connection.send(fm)
  for sB in fromSiteB:
    for sA in fromSiteA:
      #create flow match rule
      match = of.ofp_match()
      match.dl_src = EthAddr(sB)
      match.dl_dst = EthAddr(sA)

      fm = of.ofp_flow_mod()
      fm.match = match
      fm.hard_timeout = 300
      fm.idle_timeout = 100
      fm.actions.append(of.ofp_action_output(port=1))
      event.connection.send(fm)

def routeThisPacket(event,vid):
  if dpidToStr(event.dpid) == '00-00-00-00-00-11':
    siteA(event,vid)
  elif dpidToStr(event.dpid) == '00-00-00-00-00-14':
    siteB(event,vid)
  else:
    noSite(event)

#------------------------------------------------------------------------#

#---------------------------FIREWALL-------------------------------------#
def checkIfNeedToDrop(event):
  for pol in policies:
    #Forbid one way of sending by droping the packet
    match = of.ofp_match()
    match.dl_src = EthAddr(pol[1])
    match.dl_dst = EthAddr(pol[2])
    
    fm = of.ofp_flow_mod()
    fm.match = match
    fm.hard_timeout = 300
    fm.idle_timeout = 100
    event.connection.send(fm)

    #Forbid the other way by droping the packet
    match = of.ofp_match()
    match.dl_src = EthAddr(pol[2])
    match.dl_dst = EthAddr(pol[1])
    
    fm = of.ofp_flow_mod()
    fm.match = match
    fm.hard_timeout = 300
    fm.idle_timeout = 100
    event.connection.send(fm)

    # print 'Communication between {} and {} is forbidden'.format(pol[1],pol[2])

def getPolicies():
  filePath = os.getcwd() + '/ext/firewall-policies.csv'
  with open(filePath) as f:
    reader = csv.reader(f)
    for row in reader:
      if row[0] != 'id':
        policies.append(row)
#------------------------------------------------------------------------#


def routVid(event):
  msg.actions.append( of.ofp_action_output( port = event.port ) )
  event.connection.send( msg )

def _handle_PacketIn(event):
  #print "packet in to - %s" % dpidToStr(event.dpid)

  if dpidToStr(event.dpid) == '00-00-00-00-00-11':
    tcpp = event.parsed.find('tcp') 
    if tcpp is not None: 
      if tcpp.dstport == 10000:
        routVid(event)
    
def _handle_ConnectionUp (event):
  print "Switch with dpid=%s connected" % dpidToStr(event.dpid)
  routeThisPacket(event,True)
  checkIfNeedToDrop(event)
def _handle_ConnectionDown(event):
  print "Switch %s disconnected" % dpidToStr(event.dpid)


def launch ():
  getPolicies()
  core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
  core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
  core.openflow.addListenerByName("ConnectionDown", _handle_ConnectionDown)