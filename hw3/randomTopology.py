#!/usr/bin/python
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.node import RemoteController
import sys
sys.path.append('../myGraph')

class SampleTopology(Topo):
    def __init__(self):
        Topo.__init__(self)

    def build(self):   
        print "f"
        # # Add hosts and switches
        # h1 = self.addHost('h1', ip='10.0.0.1', mac='00:00:00:00:00:01')
        # s1 = self.addSwitch('s1', dpid='00:00:00:00:00:11')

        # # Add links
        # self.addLink(h1,s1,port1=1, port2=3)


topo = SampleTopology()

net = Mininet(topo=topo, controller=lambda name: RemoteController(name, ip='127.0.0.1', protocol='tcp', port = 6633), link=TCLink)

net.start()
CLI(net)
net.stop()
