import os
import struct


class Column:
    """A `Column` instance is a column in a table.
    It is also iterable and iterates over its records.
    """


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

    def __init__(self, table, field, _type):
        self.table = table
        self.field = field
        self.type = _type
        self.col_path = os.path.join(self.table.name, self.field) + ".col"
        self.colfile = open(self.col_path, 'w'); self.colfile.close()
        if self.type == "varchar":
            self.pointers_path = os.path.join(self.table.name, self.field) + ".pointers"
            self.pointersfile = open(self.pointers_path, 'w'); self.pointersfile.close()
            self.cur_pointer = 0  # value of the current pointer

    def close(self):
        self.colfile.close()
        if self.type == "varchar":  # VARCHAR column
            self.pointersfile.close()

    def open(self, mode=""):
        """Opens the column file(s) for:
        reading - by default
        writing - if `mode` == "load"
        """
        self.close()
        if self.type == "varchar":  # VARCHAR column
            self.colfile = open(self.col_path, 'a' if mode=="load" else 'rb')
            self.pointersfile = open(self.pointers_path, 'ab' if mode=="load" else 'rb')
            self.cur_pointer = 0;
        else:  # (INT | FLOAT | TIMESTAMP) column
            self.colfile = open(self.col_path, 'ab'if mode=="load" else 'rb')

    def __iter__(self): return self

    def __next__(self):
        if self.type == "varchar":
            next_bytes = self.pointersfile.read(8)
            if next_bytes:
                next_pointer = struct.unpack('Q', next_bytes)[0]
                record = self.colfile.read(next_pointer-self.cur_pointer).decode("utf-8")
                self.cur_pointer = next_pointer
                return record
        # Numeric column (INT | FLOAT | TIMESTAMP)
        next_bytes = self.colfile.read(8)
        if next_bytes:                   
            record = struct.unpack(Column.TYPE_TO_FORMAT[self.type], next_bytes)[0]
            if record in Column.TYPE_TO_NULL.values(): return "NULL"
            return record
        raise StopIteration