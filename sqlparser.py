import sqltokenizer
import re
from argument_clauses import *
from sys import float_info


class CSVDBSyntaxError(ValueError):
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

class BaseSyntaxNode(object):
    """base class for all syntax-tree nodes"""
    def __iter__(self):
        attributes = [a for a in dir(self) if not a.startswith('__') and not callable(getattr(self,a))]
        for attr in attributes:
            yield attr, getattr(self, attr)
    
    def __str__(self):
        res = ""
        for (attr, value) in self:
            res += f"{attr}: {value}\n"
        return res

class NodeDrop(BaseSyntaxNode):
    def __init__(self, table_name, if_exists):
        self.table_name = table_name
        self.if_exists =  if_exists

class NodeLoad(BaseSyntaxNode):
    def __init__(self, infile_name, table_name, ignore_lines):
        self.infile_name = infile_name
        self.table_name = table_name
        self.ignore_lines = ignore_lines

class NodeCreate(BaseSyntaxNode):
    def __init__(self, if_not_exists, table_name, scheme, select_command):
        self.if_not_exists = if_not_exists
        self.table_name = table_name
        self.scheme = scheme
        self.select_command = select_command

class NodeSelect(BaseSyntaxNode):
    def __init__(self, expression_list, outfile_name, table_name, row_condition,
                 group_fields, group_condition, order_fields):
        self.expression_list = expression_list
        self.outfile_name = outfile_name
        self.table_name = table_name
        self.row_condition = row_condition
        self.group_fields = group_fields
        self.group_condition = group_condition
        self.order_fields = order_fields

class SqlParser(object):
    def __init__(self, text):
        self._text = text
        self._tokenizer = sqltokenizer.SqlTokenizer(text)
        self._line = None
        self._col = None
        self._token = None
        self._val = None  # current token value

    def _next_token(self):
        self._line, self._col = self._tokenizer.cur_text_location()
        self._token, self._val = self._tokenizer.next_token()

    def _expect_next_token(self, token, expected_val_or_none=None, regex=None):
        self._next_token()
        self._expect_cur_token(token, expected_val_or_none, regex)

    def _expect_cur_token(self, tokens, expected_val_or_none=None, regex=None):
        if expected_val_or_none and not isinstance(expected_val_or_none, list):
             # make possible value in the format of a list
            expected_val_or_none = [expected_val_or_none]
        if not isinstance(tokens, list):
             # make possible value in the format of a list
            tokens = [tokens]
        if self._token not in tokens:
            self._raise_error("Unexpected token: {}:{} (expecting {})".format(self._token, self._val, " | ".join([str(tk) for tk in tokens])))
        elif (expected_val_or_none and self._val not in expected_val_or_none) \
             or (regex and not re.match(regex, self._val)):
            self._raise_error("Unexpected token value: " + str(self._val))

    def parse_single_command(self):
        """Parse a single command and return syntax-tree-node.
        If no command (EOF) return None."""
        self._next_token()
        tok = self._token
        val = self._val
        if tok == sqltokenizer.SqlTokenKind.EOF:
            return None
        self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD)
        if val == "create":
            return self._parse_create()
        elif val == "drop":
            return self._parse_drop()
        elif val == "load":
            return self._parse_load()
        elif val == "select":
            return self._parse_select()
        else:
            self._raise_error("Unexpected command: " + str(self._val))

    def parse_multi_commands(self, show_error=True):
        """Parse SQL commands, return a list of the Syntax Tree-root-node for each command"""
        nodes = []
        while True:
            if show_error:
                node = self.parse_show_error()
            else:
                node = self.parse_single_command()
            if not node:
                return nodes
            nodes.append(node)


    def _raise_error(self, message):
        raise CSVDBSyntaxError(message, self._line, self._col, self._text)

    def _parse_drop(self):
        """Parse a DROP command.
        Syntax:
            DROP TABLE [IF EXISTS] _table_name_;

            {IDENTIFIER} _table_name_: [a-zA-Z_]\w*
   
        Returns:
            NodeDrop -- node with the DROP command arguments.
        """

        # Node arguments:
        _if_exists_ = False
        _table_name_ = ""

        self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, "drop")
        self._expect_next_token(sqltokenizer.SqlTokenKind.KEYWORD, "table")
        self._next_token()

        # Parse "IF EXISTS" clause, if it exists ;) :
        if self._token == sqltokenizer.SqlTokenKind.KEYWORD and self._val == "if":
            self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, "if")
            self._expect_next_token(sqltokenizer.SqlTokenKind.KEYWORD, "exists")
            self._next_token()
            _if_exists_ = True

        self._expect_cur_token(sqltokenizer.SqlTokenKind.IDENTIFIER)
        _table_name_ = self._val
        self._expect_next_token(sqltokenizer.SqlTokenKind.OPERATOR, ";")
        return NodeDrop(_table_name_, _if_exists_)

    def _parse_load(self):
        """Parse a LOAD command.
        Syntax:
            LOAD DATA INFILE _infile_name_
            INTO TABLE _table_name_
            [IGNORE _ignore_lines_ LINES];

            {LIT_STR} _infile_name_: FILENAME
            {IDENTIFIER} _table_name_: [a-zA-Z_]\w*
            {LIT_NUM} _ignore_lines_: \d+
   
        Returns:
            NodeLoad -- node with the LOAD command arguments.
        """
        
        # Node arguments:
        _infile_name_ = ""
        _table_name_ = ""
        _ignore_lines_ = 0

        # Parse "LOAD DATA INFILE" clause:
        self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, "load")
        self._expect_next_token(sqltokenizer.SqlTokenKind.KEYWORD, "data")
        self._expect_next_token(sqltokenizer.SqlTokenKind.KEYWORD, "infile")
        self._expect_next_token(sqltokenizer.SqlTokenKind.LIT_STR)
        _infile_name_ = self._val

        # Parse "INTO TABLE" clause:
        self._expect_next_token(sqltokenizer.SqlTokenKind.KEYWORD, "into")
        self._expect_next_token(sqltokenizer.SqlTokenKind.KEYWORD, "table")
        self._expect_next_token(sqltokenizer.SqlTokenKind.IDENTIFIER)
        _table_name_ = self._val
        self._next_token()
        
        # Attempt parse optional IGNORE clause:
        if self._token == sqltokenizer.SqlTokenKind.KEYWORD and self._val == "ignore":
            self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, "ignore")
            self._expect_next_token(sqltokenizer.SqlTokenKind.LIT_NUM)
            _ignore_lines_ = self._val
            self._expect_next_token(sqltokenizer.SqlTokenKind.KEYWORD, "lines")
            self._next_token()

        # No more possible optional clauses to parse, reached end of command:
        self._expect_cur_token(sqltokenizer.SqlTokenKind.OPERATOR, ";")
        return NodeLoad(_infile_name_, _table_name_, _ignore_lines_)

    def _parse_create(self):
        """Parse a CREATE command.
        Syntax:
            1.
                CREATE TABLE [IF NOT EXISTS] _table_name_ (
                    _scheme_
                );

                {IDENTIFIER} _table_name_: [a-zA-Z_]\w*
                _scheme_: [_name_ _type_,]*
                           _name_ _type_
                    {IDENTIFIER} _name_: [a-zA-Z_]\w*
                    {KEYWORD} _type_: [INT|FLOAT|VARCHAR|TIMESTAMP]
            2.
                CREATE TABLE [IF NOT EXISTS] _table_name_ AS _select_command_

                {IDENTIFIER} _table_name_: [a-zA-Z_]\w*
                _select_command_: SELECT command syntax (see _parse_select documentation)
    
        Returns:
            NodeCreate -- node with the CREATE command arguments.
        """

        # Node arguments:
        _if_not_exists_ = False
        _table_name_ = ""
        _scheme_ = []
        _select_command_ = None

        self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, "create")
        self._expect_next_token(sqltokenizer.SqlTokenKind.KEYWORD, "table")
        self._next_token()

        # Parse "IF NOT EXISTS" clause:
        if self._token == sqltokenizer.SqlTokenKind.KEYWORD and self._val == "if":
            self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, "if")
            self._expect_next_token(sqltokenizer.SqlTokenKind.KEYWORD, "not")
            self._expect_next_token(sqltokenizer.SqlTokenKind.KEYWORD, "exists")
            self._next_token()
            _if_not_exists_ = True
        
        self._expect_cur_token(sqltokenizer.SqlTokenKind.IDENTIFIER, regex=r"[a-zA-Z_]\w*")
        _table_name_ = self._val
        self._next_token()
        self._expect_cur_token([sqltokenizer.SqlTokenKind.KEYWORD,sqltokenizer.SqlTokenKind.OPERATOR])

        if self._val == "(" and self._token == sqltokenizer.SqlTokenKind.OPERATOR:
            # Parse table scheme:
            self._expect_cur_token(sqltokenizer.SqlTokenKind.OPERATOR, "(")
            while True:
                _name_ = _type_ = None
                self._expect_next_token(sqltokenizer.SqlTokenKind.IDENTIFIER)
                _name_ = self._val
                self._expect_next_token(sqltokenizer.SqlTokenKind.KEYWORD, ["int", "float", "varchar", "timestamp"])
                _type_ = self._val
                _scheme_.append(CreateField(_name_, _type_))

                self._expect_next_token(sqltokenizer.SqlTokenKind.OPERATOR)
                if self._val == ")":
                    self._next_token()
                    break
        else:
            self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, "as")
            self._next_token()
            _select_command_ = self._parse_select()
        

        
        self._expect_cur_token(sqltokenizer.SqlTokenKind.OPERATOR, ";")
        return NodeCreate(_if_not_exists_, _table_name_, _scheme_, _select_command_)


    def _parse_select(self):
        """Parse a SELECT command.
        Syntax:
            SELECT [*|_expression_list_]
            [INTO OUTFILE _outfile_name_]
            FROM _table_name_
            [WHERE _row_condition_]
            [GROUP BY _group_fields_]
            [HAVING _group_condition_]
            [ORDER BY _order_fields_];


            _expression_list_: [_expression_, ]* _expression_
                _expression_: [_field_name_ | _agg_expression_ ] [AS _field_identifier_]
                    {IDENTIFIER} _field_name_: [a-zA-Z_]\w*
                    _agg_expression_: _agg_func_(_field_name_)
                        {KEYWORD} _agg_func_: [MIN|MAX|AVG|SUM|COUNT]
                    {IDENTIFIER} _field_identifier_: [a-zA-Z_]\w*

            {LIT_STR} _outfile_name_: FILENAME

            _row_condition_: _field_name_ _operator_ _constant_
                {LIT_NUM | LIT_STR} _constant_: Number, string enclosed in double quotes, or string 'NULL' indicating null value
                {OPERATOR | KEYWORD} _operator_: [< | <= | = | >= | > | <> | IS | IS NOT]
            _group_fields_: [_field_identifier_,]* _field_identifier_

            _group_condition_: _field_identifier_ _operator_ _constant_

            _order_fields_: [_order_field_,]* _order_field_
                _order_field_ : _field_identifier_ _order_
                    {KEYWORD} _order_: [ASC|DESC]

        Returns:
            NodeSelect -- node with the SELECT command arguments.
        """

        # Node arguments:
        _expression_list_ = []
        _outfile_name_ = ""
        _table_name_ = ""
        _row_condition_ = None
        _group_fields_ = []
        _group_condition_ = None
        _order_fields_ = []

        self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, "select")
        self._next_token()
        self._expect_cur_token([sqltokenizer.SqlTokenKind.KEYWORD, sqltokenizer.SqlTokenKind.IDENTIFIER, sqltokenizer.SqlTokenKind.OPERATOR])
        if self._token == sqltokenizer.SqlTokenKind.OPERATOR and self._val == "*":
            self._expect_cur_token(sqltokenizer.SqlTokenKind.OPERATOR, '*')
            self._next_token()
        else:
            # Parse expression list:
            while True:
                # Parse single expression:
                _agg_func_ = _field_name_ = _field_identifier_ = None
                self._expect_cur_token([sqltokenizer.SqlTokenKind.KEYWORD, sqltokenizer.SqlTokenKind.IDENTIFIER])
                if self._val in ["min","max","avg","sum","count"]: # aggregate expression
                    self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, ["min","max","avg","sum","count"])
                    _agg_func_ = self._val
                    self._expect_next_token(sqltokenizer.SqlTokenKind.OPERATOR, "(")
                    self._expect_next_token(sqltokenizer.SqlTokenKind.IDENTIFIER, regex=r"[a-zA-Z_]\w*")
                    _field_name_ = self._val
                    self._expect_next_token(sqltokenizer.SqlTokenKind.OPERATOR, ")") 
                else: # field name expression
                    self._expect_cur_token(sqltokenizer.SqlTokenKind.IDENTIFIER)
                    _field_name_ = self._val
                self._next_token()

                if self._token == sqltokenizer.SqlTokenKind.KEYWORD and self._val == "as":
                    # Assign a non-default identifier for the expression: 
                    self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, "as")
                    self._expect_next_token(sqltokenizer.SqlTokenKind.IDENTIFIER)
                    _field_identifier_ = self._val
                    self._next_token()
                
                # Construct and log the expression into expression_list:
                _expression_ = SelectField(_field_name_, _field_identifier_, _agg_func_)
                _expression_list_.append(_expression_)

                if self._token != sqltokenizer.SqlTokenKind.OPERATOR or self._val != ",":
                    # end of expression list
                    break
                self._expect_cur_token(sqltokenizer.SqlTokenKind.OPERATOR, ',')
                self._next_token()

        # Attempt parse optional "INTO OUTFILE" clause:
        if self._token == sqltokenizer.SqlTokenKind.KEYWORD and self._val == "into":
            self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, "into")
            self._expect_next_token(sqltokenizer.SqlTokenKind.KEYWORD, "outfile")
            self._expect_next_token(sqltokenizer.SqlTokenKind.LIT_STR)
            _outfile_name_ = self._val
            self._next_token()
        
        # Parse "FROM table_name" clause:
        self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, "from")
        self._expect_next_token(sqltokenizer.SqlTokenKind.IDENTIFIER)
        _table_name_ = self._val
        self._next_token()

        self._expect_cur_token([sqltokenizer.SqlTokenKind.KEYWORD, sqltokenizer.SqlTokenKind.OPERATOR])

        # Attempt parse optional "WHERE" clause:
        if self._token == sqltokenizer.SqlTokenKind.KEYWORD and self._val == "where":
            self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, "where")
            _row_condition_ = self.parse_condition_clause()

        # Attempt parse optional "GROUP BY" clause:
        if self._token == sqltokenizer.SqlTokenKind.KEYWORD and self._val == "group":
            self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, "group")
            self._expect_next_token(sqltokenizer.SqlTokenKind.KEYWORD, "by")
            while True:
                self._expect_next_token(sqltokenizer.SqlTokenKind.IDENTIFIER)
                _field_identifier_ = self._val
                _expression_ = GroupField(_field_identifier_)
                _group_fields_.append(_expression_)
                self._next_token()
                if self._token != sqltokenizer.SqlTokenKind.OPERATOR or self._val != ",":
                    # reached end of fields list
                    break

        # Attempt parse optional "HAVING" clause:
        if self._token == sqltokenizer.SqlTokenKind.KEYWORD and self._val == "having":
            self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, "having")
            _group_condition_ = self.parse_condition_clause()


        # Attempt parse optional "ORDER BY" clause:
        if self._token == sqltokenizer.SqlTokenKind.KEYWORD and self._val == "order":
            self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, "order")
            self._expect_next_token(sqltokenizer.SqlTokenKind.KEYWORD, "by")
            while True:
                self._expect_next_token(sqltokenizer.SqlTokenKind.IDENTIFIER)
                _field_identifier_ = self._val
                self._next_token()
                _order_ = "asc"  # order is ascending by default
                if self._token == sqltokenizer.SqlTokenKind.KEYWORD:
                    self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, ["asc","desc"])
                    _order_ = self._val
                    self._next_token()
                _expression_ = OrderField(_field_identifier_, _order_)
                _order_fields_.append(_expression_)
                if self._token != sqltokenizer.SqlTokenKind.OPERATOR or self._val != ",":
                    # reached end of fields list
                    break

        # No more possible optional clauses to parse, reached end of command:
        self._expect_cur_token(sqltokenizer.SqlTokenKind.OPERATOR, ";")
        return NodeSelect(_expression_list_, _outfile_name_, _table_name_, _row_condition_,
                            _group_fields_, _group_condition_, _order_fields_) 

    
    def parse_condition_clause(self):
        """Parses a condition clause and returns it as a Condition object.
        
        Returns:
            Condition -- the constructed condition.
        """

        # Parse _field_name_:
        self._expect_next_token(sqltokenizer.SqlTokenKind.IDENTIFIER)
        _field_name_ = self._val
        self._next_token()

        # Parse _operator_:
        if self._token == sqltokenizer.SqlTokenKind.KEYWORD:
            self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, "is")
            self._next_token()
            if self._token == sqltokenizer.SqlTokenKind.KEYWORD and self._val == "not":
                self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, "not")
                _operator_ = "is not"
                self._next_token()
            else:
                _operator_ = "is"
        else:
            self._expect_cur_token(sqltokenizer.SqlTokenKind.OPERATOR, ["<","<=","=",">=",">","<>"])
            _operator_ = self._val
            self._next_token()

        # Parse _constant_:
        if self._token == sqltokenizer.SqlTokenKind.LIT_NUM:
            self._expect_cur_token(sqltokenizer.SqlTokenKind.LIT_NUM)
            _constant_ = self._val
        elif self._token == sqltokenizer.SqlTokenKind.LIT_STR:
            self._expect_cur_token(sqltokenizer.SqlTokenKind.LIT_STR)
            _constant_ = self._val
        else:  # null value
            self._expect_cur_token(sqltokenizer.SqlTokenKind.KEYWORD, "null")
            _constant_ = float('-inf')
        
        # Advance the cursor and construct the condition:
        self._next_token()  
        _condition_ = Condition(_field_name_, _operator_, _constant_)
        return _condition_
        
        
    def parse_show_error(self):
        try:
            return self.parse_single_command()
        except CSVDBSyntaxError as ex:
            print(ex)


def _test():
    commands = ['DROP TABLE IF EXISTS movies;',
                'LOAD DATA INFILE "data.txt"\nINTO TABLE _table\nIGNORE 2 LINES;',
                'CREATE TABLE _table AS SELECT SUM(_col0_) as _sum_col1_ FROM _table0 ORDER BY _col0_;',
                'CREATE TABLE IF NOT EXISTS _table (\n\tcol0 INT,\n\tcol1 FLOAT,\n\tcol2 VARCHAR,\n\tcol3 TIMESTAMP\n);',
                'SELECT col0 AS _col0_, col1, SUM(col2) AS _sum_col2_\nINTO OUTFILE "result.csv"\nFROM _table\nWHERE _col0_ <> 5.5e2\nGROUP BY col1, _col0_\nHAVING _sum_col2_ < 10\nORDER BY col1 DESC, _col0_ ASC;']

    for command in commands:
        print(command, end="\n\n")
        parser = SqlParser(command)
        node = parser.parse_show_error()
        print(node, end="\n\n")

if __name__ == "__main__":
    _test()
