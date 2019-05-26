from Column import Column
from Errors import *
from SqlParser import NodeCreate, NodeDrop, NodeLoad, NodeSelect
from Printer import Printer

import os
import json 
import csv
import struct


class Table:
    """ A `Table` instance represents a table.
    This class contains:
        - instance methods for each command and their static sub-methods.
        - static method ExecuteCommand to execute a command.
        - class variable 'table_dict':
            `table_dict` maps a table name to a `Table` instance (CSVDB table).
            When a table name `table_name` is referenced the sql command to execute,
            `table_name` is searched in table_dict in order to perform the command on it.
            If `table_name` isn't in `table_dict` then a Table instance for `table_name` is
            created and added to `table_dict`.
            Obviously, table_dict is empty at the start of each session, but loading tables
            into it is not expensive enough for us to save it to a file.
    """
    # Static dictionaries:
    
    table_dict = {}
    verbose = False

    TYPE_TO_FORMAT = {
        "int": 'q',
        "float": 'd',
        "timestamp": 'Q'
    }
    TYPE_TO_NULL = {
        "int": -2**63,
        "float": float("-inf"),
        "timestamp": 0
    }

    def __init__(self, table_name):
        Table.table_dict[table_name] = self
        if Table.table_exists(table_name):
            jsonfile = open(os.path.join(table_name, "table.json"), 'r')
            jsondata = json.load(jsonfile)
            jsonfile.close()
            # The following are python variables representation of the data in 'table.json'
            self.name = jsondata["name"]
            self.num_cols = jsondata["cols"]
            self.num_rows = jsondata["rows"]
            self.columns = [Column(self, column["field"], column["type"])
                         for column in jsondata["schema"]]
            self.printer = Printer(self.columns)  # for printing SELECT output to the console
            

    @staticmethod
    def verbose_on():
        Table.verbose = True

    @staticmethod
    def execute_command(node):
        # Get `Table` instance:
        table = Table.table_dict.get(node.table_name)
        if table is None:
            table = Table(node.table_name)
        
        if isinstance(node, NodeSelect):  # Select node
            return table.Select(node)
        elif isinstance(node, NodeLoad):  # Load node
            table.Load(node)    
        elif isinstance(node, NodeCreate):  # Create node
            table.Create(node)
        elif isinstance(node, NodeDrop):  # Drop node
            table.Drop(node)        

    @staticmethod
    def table_exists(table_name):
        """Checks if 'table_name' is a table in the current working directory.
        First checks if 'table_name' is a directory, then checks if it's contents
        match the schema of a table directory (mandatory 'table.json', all other files are .col or .pointers)
        """
        if os.path.isdir(table_name):
            json_file_exists = False
            for f in os.listdir(table_name):
                name, ext = os.path.splitext(f)
                if f == "table.json": json_file_exists = True
                elif ext != ".col" and ext != ".pointers":
                    return False
            if json_file_exists:
                return True
        return False

    @staticmethod
    def file_exists(filename):
        return os.path.isfile(filename)


    def update_json(self):
        jsondata = {
            "name": self.name,
            "rows": self.num_rows,
            "cols": self.num_cols,
            "schema": [
                {  # VARCHAR column data
                    'field': column.field,
                    'type': column.type,
                    'col_path': column.col_path,
                    'pointers_path': column.pointers_path          
                } if column.type == "varchar" else 
                {  # (INT | FLOAT | TIMESTAMP) column data
                    'field': column.field,
                    'type': column.type,
                    'col_path': column.col_path
                } for column in self.columns 
            ]
        }
        json_file = open(os.path.join(self.name, "table.json"), 'w')
        json.dump(jsondata,json_file, sort_keys=True, indent=2, separators=(',', ': '))
        json_file.close()



    def Create(self, node):
        if Table.table_exists(node.table_name):
            if node.if_not_exists:  # end command gracefully
                if Table.verbose:
                    print(f"Verbose: Table {node.table_name} already exists therefore no changes were made to the database.\n")
            else:  # end command by exception
                print(TableAlreadyExistsError(node.table_name))
            return

        # TODO - what if a folder by the same name exists but is not a table
        os.mkdir(node.table_name)  # create directoy for the table
        # Set table properties and write the JSON file:
        self.name = node.table_name
        self.num_rows = 0
        self.num_cols = len(node.schema)
        self.columns = [Column(self, column.identifier, column.type) for column in node.schema]
        self.update_json()
        self.printer = Printer(self.columns) 



    def Drop(self, node):
        if not Table.table_exists(node.table_name):
            if node.if_exists:  # end command gracefully
                if Table.verbose:
                    print(f"Verbose: Table {node.table_name} doesn't exist therefore no changes were made to the database.\n")
            else:  # end command by exception
                print(TableNotExistsError(node.table_name))
            return               

        # Remove the table directory and all its contents:
        for f in os.listdir(node.table_name):
            os.remove(os.path.join(node.table_name, f))
        os.rmdir(node.table_name)


    def load_varchar(self, column, record):
        """Loads a varchar value `record` into file `colfile` and updates file `pointerfile` accordingly.
        Pointers are of type 64 bit unsigned int therefore packed by format 'Q'
        """
        column.colfile.write(record)
        column.pointersfile.write(struct.pack("Q",column.colfile.tell()))

    def load_numeric(self, column, record, format):
        """Loads a numeric value `record` into file `colfile` in the format `format`.
        Possible `format` values:
            'q' -- INT
            'd' -- FLOAT
            'Q' -- TIMESTAMP
        """
        if not record:  # NULL value
            record_val = Table.TYPE_TO_NULL[column.type]
        elif format == "d":
            record_val = float(record)
        else:
            record_val = int(record)
        column.colfile.write(struct.pack(format, record_val))


    def load_record(self, column, record):
        """Loads a record `record` into column `column`
        """ 
        if column.type == "varchar":
            self.load_varchar(column, record)
        else:  # numeric column (INT | FLOAT | TIMESTAMP)
            self.load_numeric(column, record, format=Table.TYPE_TO_FORMAT[column.type])

    def Load(self, node):
        if not Table.file_exists(node.infile_name):  # .csv file doesn't exist
            print(InfileNotExistsError(node.infile_name))
            return
        if not Table.table_exists(node.table_name):  # table to load into doesn't exist
            print(TableNotExistsError(node.table_name))
            return

        # Both infile and table exist, continue:
        # Count rows and update `rows` field of the json data:
        infile = open(node.infile_name, 'r')
        rows = sum(1 for line in infile)
        self.num_rows += rows
        self.update_json()

        infile = open(node.infile_name, 'r')
        reader = csv.reader(infile)
        # Skip `ignore_lines` lines from the top:
        for _ in range(node.ignore_lines):
            next(reader) 
        
        # Open all column files:
        for column in self.columns:
            column.open(mode="load")

        # Start loading:
        for row in reader:
            for column, record in zip(self.columns, row):
                record = record.replace('\xa0', ' ')
                self.load_record(column, record)
        # Finished loading - close all files:
        for column in self.columns: 
            column.close()



    def select_generator(self, node):
        if not node.expression_list:  # 'Select * from ...'
            for column in self.columns: column.open()
            yield [column.field for column in self.columns]  # yield column fields
            for row in zip(*self.columns): yield row  # yield all column values


    def Select(self, node):
        rows = self.select_generator(node)
        if node.outfile_name:  # export output to csv file
            # TODO - export to csv
            pass
        else:  # print output to terminal
            self.printer.print_rows(rows)

        
            
