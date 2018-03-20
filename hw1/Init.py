
from mininet.topo import Topo

class MyTopo( Topo ):


    def __init__( self ):

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        h1 = self.addHost( 'h1' ,mac='00:00:00:00:00:01')
        h2 = self.addHost( 'h2' ,mac='00:00:00:00:00:02')
        h3 = self.addHost( 'h3' ,mac='00:00:00:00:00:03')
        h4 = self.addHost( 'h4' ,mac='00:00:00:00:00:04')
        s1 = self.addSwitch( 's1')
        s2 = self.addSwitch( 's2')
        s3 = self.addSwitch( 's3')
        s4 = self.addSwitch( 's4')

        # Add links
        self.addLink(h1,s1)
        self.addLink(h2, s1)
        self.addLink(s1, s2)
        self.addLink(s1,s3)
        self.addLink(s3,s4)
        self.addLink(s2,s4)
        self.addLink(s4,h3)
        self.addLink(s4, h4)



topos = { 'mytopo': ( lambda: MyTopo() ) }

