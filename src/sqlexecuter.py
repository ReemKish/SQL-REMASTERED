# sqlexecuter.py
# Contains 4 execution methods for the 4 possible commands
# as well as a general method that directs a node to the correct execute command.

import os, json

from sqlparser import NodeCreate, NodeDrop, NodeLoad, NodeSelect

def execNode(node, verbose=False):
    if isinstance(node, NodeCreate):  # Create node
        execCreate(node, verbose)
    elif isinstance(node, NodeDrop):  # Drop node
        execDrop(node, verbose)        
    elif isinstance(node, NodeLoad):  # Load node
        execLoad(node, verbose)    
    elif isinstance(node, NodeSelect):  # Select node
        execSelect(node, verbose)

def execCreate(node, verbose=False):
    if os.path.isdir(node.table_name):  # table already exists
        if node.if_not_exists:  # end command gracefully
            if verbose:
                print(f"Verbose: Table {node.table_name} already exists therefore no changes were made to the database.\n")
            return
        else:  # end command by an exception
            raise TableAlreadyExistsException;
    os.mkdir(node.table_name)  # create directoy for the table

    # Create JSON file:
    json_file = open(os.path.join(node.table_name, "table.json"), 'w')
    json.dump({'schema': [{'field': column.identifier, 'type': column.type} for column in node.scheme]},
              json_file, sort_keys=True, indent=2, separators=(',', ': '))
    json_file.close()

    # Further implementation:
    pass


def execDrop(node, verbose=False):
    pass

def execLoad(node, verbose=False):
    pass

def execSelect(node, verbose=False):
    pass