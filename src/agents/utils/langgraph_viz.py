"""
Helper script to visualise the agent graph using pygraphviz.
Setup on mac [see more here https://github.com/pygraphviz/pygraphviz/blob/main/INSTALL.txt]:
# $ brew install graphviz
# $ pip install pygraphviz
"""

agent = ...


graph = agent.app.get_graph()
print(graph)
graph.draw_png("./graph.png")