import os
from Column import Column

class Printer:
    """This class handles the printing of a SELECT command output to the console in the correct format. 
    """

    def __init__(self, columns):
        self.width = Printer.try_get_width()  # width of the console
        self.columns = columns  # get info of table columns for printing
        self.num_cols = len(columns)
        self.column_lengths = [0] * self.num_cols  # i-th value is the length of column i in the current print
        self.print_width = 0  # total width of the current print
    


    @staticmethod
    def try_get_width():
        """Tries getting exact number of columns in terminal for correct output formatting (linux only).
        Returns number of columns (defaults to 150 if not successful)
        """
        try: width = int(os.popen('stty size', 'r').read().split()[1])
        except: width = 100
        return width


    def set_column_lengths(self):
        """Calculate the length of each varchar and each numeric column in the
        current output for it to display correctly
        """
        ratio = 2;  # ratio of varchar column length to numeric column length
        num_varchar = sum(1 for column in self.columns if column.type == "varchar" )
        num_numeric = self.num_cols - num_varchar
        numeric_length = (self.width - num_numeric - num_varchar + 1) // (ratio*num_varchar + num_numeric)
        varchar_length = numeric_length * ratio
        self.column_lengths = [varchar_length if column.type=="varchar" else numeric_length for column in self.columns]


    def print_rows(self, rows):
        self.set_column_lengths()
        # Print fields:
        fields = next(rows)
        self.print_row(fields)
        # Print separator line:
        separator = ""
        for length in self.column_lengths:
            separator += '-' * length + '+'
        separator = separator[:-1]
        print(separator)
        # Print records:
        for row in rows:
            self.print_row(row)

    def print_row(self, row):
        is_last = False
        for i, record in enumerate(row):
            if record in Column.TYPE_TO_NULL.values(): record = "NULL"            
            if i == len(row) - 1:
                is_last = True
            length = self.column_lengths[i]
            self.print_record(record, length, is_last)
        print()

    def print_record(self, record, length, is_last=False):
        # if isinstance(record, str): print(f"length: {length}")
        record = str(record)
        if len(record) > length:
            record = record[:length-2] + ".."
        length -= len(record)
        print(' ' * (length // 2), end="")
        print(record, end=" " if length & 1 else "")
        print(' ' * (length // 2), end="" if is_last else '|')