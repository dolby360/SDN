#!/usr/bin/python
from pox.core import core
from pox.lib.util import dpidToStr
from pox.openflow import *
from pox.lib.addresses import IPAddr, EthAddr
from pox.lib.packet import *

import networkx as nx
import matplotlib.pyplot as plt
import random

def _handle_PacketIn(event):
  #print "packet in to = %s" % dpidToStr(event.dpid)
  x = 1

def _handle_ConnectionUp (event):
  print "Switch with dpid=%s connected" % dpidToStr(event.dpid)

def _handle_ConnectionDown(event):
  print "Switch %s disconnected" % dpidToStr(event.dpid)

def launch ():
  core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
  core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
  core.openflow.addListenerByName("ConnectionDown", _handle_ConnectionDown)