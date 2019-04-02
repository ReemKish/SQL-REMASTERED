# -------------------------------------- Program Description --------------------------------------
# Command Line Tool for the CSV Data Base - Structured Query Launguage
# By Maayan Kestenberg and Re'em Kishnveksy

import argparse
from colorama import init, Fore, Style # For displaying colored text to the terminal
import os
import sqlparser
import sqlexecuter

# ---------------------------------------- Initialization -----------------------------------------
init()  # Init colorama
program_desc = f"""
             {Style.BRIGHT}{Fore.YELLOW}SQL Remastered{Style.NORMAL}
By Re'em Kishnevsky and Maayan Kestenboi{Style.RESET_ALL}
"""  # In the future the description will contain a nice ascii graphic. But that will be the last thing we do in this project

cl_parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description = program_desc)
cl_parser.add_argument("-d", "--rootdir", help="the root directory of your project. Defaults to the current working directory",
                       metavar="PATH", dest="rootdir_path", default=".")
cl_parser.add_argument("-r", "--run", help="run a pre-written CSVDB-SQL script inside FILENAME", metavar="FILENAME", dest="script_path")
cl_parser.add_argument("-v", "--verbose", help="turn on debugging output", action="store_true")



# ------------------------------------------- Functions -------------------------------------------
def input_command():
    while True:
        try:
            command = input("csvdb> ")
        except EOFError:  # Exit program
            exit()
        if command.strip() == "exit" or command.strip() == "quit": exit()
        elif command: break
    while command[-1]!=";":
        command += " " + input(".......")
    return command

def parse_cmdline_args():
    args = cl_parser.parse_args()  # Acquire argument values from the user (args.rootdir_path, args.script_path, args.verbose)
    if args.rootdir_path and not os.path.isdir(args.rootdir_path):
        cl_parser.error(f"argument -r/--run: No such directory: '{args.rootdir_path}'")
    if args.script_path and not os.path.isfile(args.script_path):
        cl_parser.error(f"argument -r/--run: No such file: '{args.script_path}'")
    print(program_desc)
    return args

def handle_script(script_path, rootdir, verbose):
    script = open(script_path).read()
    sql_parser = sqlparser.SqlParser(script)
    nodes = sql_parser.parse_multi_commands()
    for node in nodes:
        sqlexecuter.execNode(node, rootdir, verbose)

def handle_interpreter(rootdir, verbose):
    while True:
        command = input_command()
        sql_parser = sqlparser.SqlParser(command)  # 3 times 'sql parser' in one line LoL
        node = sql_parser.parse_show_error()
        sqlexecuter.execNode(node, rootdir, verbose)

def main():
    args = parse_cmdline_args()
    if args.script_path:  # User supplied a script file path
        handle_script(args.script_path, args.rootdir_path, args.verbose)
    else:
        handle_interpreter(args.rootdir_path, args.verbose)
        


if __name__ == "__main__":
    main()