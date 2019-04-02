# sqlexecuter.py
# Contains four execution methods for the 4 possible commands
# as well as a general method that directs a node to the correct execute command.

from sqlparser import NodeCreate, NodeDrop, NodeLoad, NodeSelect

def execNode(node, rootdir, verbose):
    if isinstance(node, NodeCreate):  # Create node
        execCreate(node, rootdir, verbose)
    elif isinstance(node, NodeDrop):  # Drop node
        execDrop(node, rootdir, verbose)        
    elif isinstance(node, NodeLoad):  # Load node
        execLoad(node, rootdir, verbose)    
    elif isinstance(node, NodeSelect):  # Select node
        execSelect(node, rootdir, verbose)

def execCreate(node, rootdir, verbose):
    pass

def execDrop(node, rootdir, verbose):
    pass

def execLoad(node, rootdir, verbose):
    pass

def execSelect(node, rootdir, verbose):
    pass