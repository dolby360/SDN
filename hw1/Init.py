from mininet.topo import Topo
from mininet.cli import CLI

class MyTopo( Topo ):



    def __init__( self ):
        # Initialize topology
        Topo.__init__( self )


        # Add hosts and switches
        h1 = self.addHost('h1', ip='10.0.0.1', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', ip='10.0.0.2', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', ip='10.0.0.3', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', ip='10.0.0.4', mac='00:00:00:00:00:04')
        s1 = self.addSwitch('s1', dpid='00:00:00:00:00:11')
        s2 = self.addSwitch('s2', dpid='00:00:00:00:00:12')
        s3 = self.addSwitch('s3', dpid='00:00:00:00:00:13')
        s4 = self.addSwitch('s4', dpid='00:00:00:00:00:14')

        # Add links
        self.addLink(h1,s1,port1=1, port2=3)
        self.addLink(h2,s1,port1=1, port2=4)
        self.addLink(s1,s2,port1=1, port2=1)
        self.addLink(s1,s3,port1=2, port2=1)
        self.addLink(s3,s4,port1=2, port2=2)
        self.addLink(s2,s4,port1=2, port2=1)
        self.addLink(s4,h3,port1=3, port2=1)
        self.addLink(s4,h4,port1=4, port2=1)



topos = { 'mytopo': ( lambda: MyTopo() ) }
