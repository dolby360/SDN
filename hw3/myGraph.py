
import networkx as nx
import matplotlib.pyplot as plt
import random

class myGraph():
    def __init__(self):
        self.l = [] 
        #n, i.e. total number of nodes
        self.n = 10
        #p, i.e. the value of the probability
        self.p = 0.1
        #Create an empty graph add n nodes to it
        self.G = nx.Graph()
    def makeGrph(self):
        for i in range(0,self.n):
            self.G.add_node(i)
        for t1 in range(0,self.n):
            for t2 in range(0,self.n):
                if t1 != t2 and random.random() < self.p:
                    self.G.add_edge(t1,t2)
                    self.l.append((t1,t2))
        # G.add_edges_from(l)
        switchesList = [i for i in range(self.n)]
        #G.add_path(switchesList)
        pos = nx.spring_layout(self.G)
        # drawing setup for switches
        nx.draw_networkx_nodes(self.G,pos,nodelis=switchesList,node_color='b',node_size=500,alpha=0.8)
        nx.draw_networkx_edges(self.G,pos,edgelist=self.l,width=8,alpha=0.5,edge_color='y')
        #nx.draw(G)
        plt.show()