from mininet.topo import Topo
from mininet.cli import CLI

class MyTopo( Topo ):



    def __init__( self ):
        def int2dpid(dpid):
            try:
                dpid = hex(dpid)[2:]
                dpid = '0' * (16 - len(dpid)) + dpid
                return dpid
            except IndexError:
                raise Exception('can\'t translate int to dpid\n')
        # Initialize topology
        Topo.__init__( self )


        # Add hosts and switches
        h1 = self.addHost('h1', ip='10.0.0.1', mac='00:00:00:00:00:11')
        h2 = self.addHost('h2', ip='10.0.0.2', mac='00:00:00:00:00:12')
        h3 = self.addHost('h3', ip='10.0.0.3', mac='00:00:00:00:00:13')
        h4 = self.addHost('h4', ip='10.0.0.4', mac='00:00:00:00:00:14')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')

        # Add links
        self.addLink(h1,s1)
        self.addLink(h2,s1)
        self.addLink(s1,s2)
        self.addLink(s1,s3)
        self.addLink(s3,s4)
        self.addLink(s2,s4)
        self.addLink(s4,h3)
        self.addLink(s4,h4)



topos = { 'mytopo': ( lambda: MyTopo() ) }
