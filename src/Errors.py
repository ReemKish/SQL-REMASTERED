class CSVDBSyntaxError(SyntaxError):
    def __init__(self, message, line, col, text):
        super().__init__()
        self.line = line
        self.col = col
        self.text = text

        # Build location clause of the error message:
        location_clause = ""
        for i, line_text in enumerate(self.text.splitlines() + ["\n"]):
            # s += line_text
            if i == self.line - 1:
                location_clause += line_text + "\n"
                location_clause += " " * (self.col-1) + "^^^"

        self.message = f"CSVDB Syntax error at line {line} col {col}:\n{location_clause}\n{message}\n"
    def __str__(self):
        return self.message


class CSVDBException(Exception):
    def __init__(self):
        self.message = "CSVDB SQL error:\n"


class TableAlreadyExistsError(CSVDBException):
    """Raised by Create when trying to create a table that already exist.
    """
    def __init__(self, table_name):
        super().__init__()
        self.message += f"table {table_name} already exists\n"
    def __str__(self):
        return self.message


class TableNotExistsError(CSVDBException):
    """Raised by Drop | Select | Load when a table is referenced that doesn't exist.
    """
    def __init__(self, table_name):
        super().__init__()
        self.message += f"table {table_name} doesn't exist\n"
    def __str__(self):
        return self.message


class InfileNotExistsError(CSVDBException):
    """Raised by Load when trying to load data from an infile that doesn't exist.
    """
    def __init__(self, filename):
        super().__init__()
        self.message += f"csv infile {filename} doesn't exist\n"
    def __str__(self):
        return self.message

class DirectoryAlreadyExistsError(CSVDBException):
    """Raised by Create when trying to create a table while a directory with the same
    name exists, that isn't a table (if it's a table, TableAlreadyExistsError is raised).
    """
    def __init__(self, table_name):
        super().__init__()
        self.message += f"a direcotry with name {table_name} already exists\n"
    def __str__(self):
        return self.message

class SoftError(CSVDBException):
    """Raised when the function cannot continue, but no due to an error
    """
    def __str__(self):
        return ""