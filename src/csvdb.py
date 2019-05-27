# -------------------------------------- Program Description --------------------------------------
# Command Line Tool for the CSV Data Base - Structured Query Launguage
# By Maayan Kestenberg and Re'em Kishnveksy

from SqlParser import SqlParser
from Table import Table

import argparse
import readline
import os

try:
    from colorama import init, Fore, Style
    has_colors = True
except ModuleNotFoundError:
    has_colors = False

class Console:
    """This class is the core of the program, its purpose is to provide home for
    some methods who share a common nature of being closely related to the
    command line and user input -- the console.
    """


    def __init__(self, has_colors):
        
        self.has_colors = has_colors
        self.program_desc = Console.determine_desc(self.has_colors)
        self.cl_parser = Console.create_commandline_parser(self.program_desc)
        self.macros = Console.set_macros()
        # Length allocated for each column type in the print of the current output:
        self.varchar_length = self.numeric_length = 0  
        

    
    @staticmethod
    def determine_desc(has_colors):
        """
        """
        if has_colors:
            init()  # Init colorama
            program_desc = f"""
                        {Style.BRIGHT}{Fore.YELLOW}SQL Remastered{Style.NORMAL}
            By Re'em Kishnevsky and Maayan Kestenboi{Style.RESET_ALL}
            """
        else:
            program_desc = f"""
                        SQL Remastered
            By Re'em Kishnevsky and Maayan Kestenboi
            """ 
        return program_desc

    @staticmethod
    def create_commandline_parser(program_desc):
        """
        """
        cl_parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description = program_desc)
        cl_parser.add_argument("-d", "--rootdir", help="the root directory of your project. Defaults to the current working directory",
                            metavar="PATH", dest="rootdir_path", default=".")
        cl_parser.add_argument("-r", "--run", help="run a pre-written CSVDB-SQL script inside FILENAME", metavar="FILENAME", dest="script_path")
        cl_parser.add_argument("-v", "--verbose", help="turn on debugging output", action="store_true")
        return cl_parser

    @staticmethod
    def set_macros():
        return {
            "tcreate": "CREATE TABLE test (title VARCHAR, tyear INT, duration TIMESTAMP, score FLOAT);",
            "tload": "LOAD DATA INFILE \"test.csv\" INTO TABLE test IGNORE 1 LINES;",
            "tselect": "SELECT * FROM test;",
            "tdrop": "DROP TABLE IF EXISTS test;",
            "t": "DROP TABLE IF EXISTS test;" +
                 "CREATE TABLE test (title VARCHAR, tyear INT, duration TIMESTAMP, score FLOAT);" +
                 "LOAD DATA INFILE \"test.csv\" INTO TABLE test IGNORE 1 LINES;" +
                 "SELECT * FROM test;"
            
        }
    


    def input_command(self):
        while True:
            try:
                command = input("csvdb> ")
            except EOFError:  # Exit program (Ctrl + D)
                print()
                exit()
            if command.strip() == "exit" or command.strip() == "quit": exit()
            elif command.strip() in self.macros: return self.macros[command.strip()]
            elif command.strip(): break
        while command[-1]!=";":
                try:
                    appendix = input(".......")
                except EOFError:  # Exit program (Ctrl + D)
                    print()
                    exit()
                if appendix.strip():
                    command += "\n" + appendix
                else:
                    command += ';'
                    break
        return command



    def parse_cmdline_args(self):
        args = self.cl_parser.parse_args()  # Acquire argument values from the user (args.rootdir_path, args.script_path, args.verbose)
        if args.rootdir_path and not os.path.isdir(args.rootdir_path):
            self.cl_parser.error(f"argument -r/--run: No such directory: '{args.rootdir_path}'")
        if args.script_path and not os.path.isfile(args.script_path):
            self.cl_parser.error(f"argument -r/--run: No such file: '{args.script_path}'")
        return args



    def handle_script(self, script_path, verbose=False):
        scriptfile = open(script_path, 'r')
        script = scriptfile.read()
        scriptfile.close()
        if script[-1] != ";": script += ';'
        sqlparser = SqlParser(script)
        nodes = sqlparser.parse_multi_commands()
        for node in nodes:
            Table.execute_command(node)



    def handle_interpreter(self, verbose=False):
        print(self.program_desc)
        while True:
            command = self.input_command()
            sqlparser = SqlParser(command)
            nodes = sqlparser.parse_multi_commands()
            for node in nodes:
                rows = Table.execute_command(node)
                if rows is not None: self.print_rows(rows)



    def do(self):
        args = self.parse_cmdline_args()
        os.chdir(args.rootdir_path)
        if args.verbose:  # flag 'v' supplied
            Table.verbose_on()
        if args.script_path:  # script file path supplied
            self.handle_script(args.script_path,args.verbose)
        else:
            self.handle_interpreter(args.verbose)




def main():
    console = Console(has_colors)
    console.do()

if __name__ == "__main__":
    main()