#!/usr/bin/python
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.node import RemoteController

class SampleTopology(Topo):
    def __init__(self):
        Topo.__init__(self)

    def build(self):    

        # Add hosts and switches
        h1 = self.addHost('h1', ip='10.0.0.1', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', ip='10.0.0.2', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', ip='10.0.0.3', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', ip='10.0.0.4', mac='00:00:00:00:00:04')
        h5 = self.addHost('h5', ip='10.0.0.5', mac='00:00:00:00:00:05')
        h6 = self.addHost('h6', ip='10.0.0.6', mac='00:00:00:00:00:06')
        h7 = self.addHost('h7', ip='10.0.0.7', mac='00:00:00:00:00:07')
        h8 = self.addHost('h8', ip='10.0.0.8', mac='00:00:00:00:00:08')
        s1 = self.addSwitch('s1', dpid='00:00:00:00:01:01')



        # Add links
        self.addLink(h1,s1,port1=1, port2=1)
        self.addLink(h2, s1, port1=1, port2=2)
        self.addLink(h3, s1, port1=1, port2=3)
        self.addLink(h4, s1, port1=1, port2=4)
        self.addLink(h5, s1, port1=1, port2=5)
        self.addLink(h6, s1, port1=1, port2=6)
        self.addLink(h7, s1, port1=1, port2=7)
        self.addLink(h8, s1, port1=1, port2=8)


topo = SampleTopology()

net = Mininet(topo=topo, controller=lambda name: RemoteController(name, ip='127.0.0.1', protocol='tcp', port = 6633), link=TCLink)

net.start()
CLI(net)
net.stop()
