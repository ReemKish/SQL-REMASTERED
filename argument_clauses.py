class Condition(object):
    """A Condition object represents a simple sql condition:
    Syntax:
        _field_name_ _operator_ _constant_

        {IDENTIFIER} _field_name_: [a-zA-Z_]\w*
        {OPERATOR | KEYWORD} _operator_: [< | <= | = | >= | > | <> | IS | IS NOT]
        {LIT_NUM | LIT_STR} _constant_: Number, string enclosed in double quotes, 
                                        or identifier NULL indicating null value
    
    e.g:
        age > 15  =>  _field_name_ = "age"
                      _operator_ = ">"
                      _constant_ = 15
    """

    def __init__(self, field_name, operator, constant):
        self.field_name = field_name
        self.operator = operator
        self.constant = constant

    def __str__(self):
        return f"{self.field_name} {self.operator} {self.constant}"



class Field(object):
    """Base class for representing field objects: SelectField, GroupField, OrderField.
    """

    def __init__(self, identifier):
        self.identifier = identifier
    
    def __str__(self):
        return f"{self.identifier}"

    def __repr__(self):
        return self.__str__()


class SelectField(Field):
    """A SelectField object represents a field expression to be selected by the SELECT command:
    Two kinds of select field expressions:
    1. Simple expression:
        Syntax: 
            _field_name_
            {IDENTIFIER} _field_name_: [a-zA-Z_]\w*

    2. Aggregated expression:
        Syntax:
            _agg_func_(_field_name_)
            {KEYWORD} _agg_func_: [MIN|MAX|AVG|SUM|COUNT]
            {IDENTIFIER} _field_name_: [a-zA-Z_]\w*

    Both expressions can be assigned a non-default identifier:
    Syntax:
        _field_expression_ AS _field_identifier_
        _field_expression_: [_field_name_ | _agg_func_(_field_name_)]
        {IDENTIFIER} _output_field_name_: [a-zA-Z_]\w*

    If 'AS' is omitted, the field expression will be assigned a default identifier:
    1. For simple expression: _field_name_ - the default identifier is _field_name_
    2. For aggregated expression: _agg_func_(_field_name) - the default identifier is _agg_func_(_field_name_)
       e.g: COUNT(col0) - default identifier is 'count(col0)'
    """

    def __init__(self, field_name, identifier=None, agg_func=None):
        if identifier:
            # an identifier was supplied
            super().__init__(identifier)
        elif agg_func:
            # default identifier for aggregate expression
            super().__init__(f"{agg_func}({field_name})")
        else:
            # default identifier for simple expression
            super().__init__(field_name)

        self.field_name = field_name
        self.agg_func = agg_func

    def __str__(self):
        # Aggregate expression:
        if self.agg_func:
            if self.identifier != f"{self.agg_func}({self.field_name})":
                return f"{self.agg_func}({self.field_name}) AS {self.identifier}"
            return f"{self.agg_func}({self.field_name})"

        # Simple expression:
        if self.identifier != self.field_name:
            return f"{self.field_name} AS {self.identifier}"
        return f"{self.field_name}"

    def __repr__(self):
        return self.__str__()


class GroupField(Field):
    """A GroupField object represents a field supplied in the GROUP BY clause of the SELECT command:
    Syntax: 
            _field_identifier_
            {IDENTIFIER} _field_identifier_: [a-zA-Z_]\w*

    Note: GroupField fields cannot be aggregated nor assigned a different identifier.
    """

    def __init__(self, identifier):
        super().__init__(identifier)


class OrderField(Field):
    """An OrderField object represents a field expression supplied in the ORDER BY clause of the SELECT command:
    Syntax: 
            _field_identifier_
            {IDENTIFIER} _field_identifier_: [a-zA-Z_]\w*

    Note: OrderField fields cannot be aggregated nor assigned a different identifier.
    """

    def __init__(self, identifier, order="asc"):
        super().__init__(identifier)
        self.order = order

    def __str__(self):
        return f"{self.identifier} {self.order.upper()}"

    def __repr__(self):
        return self.__str__()


class CreateField(Field):
    """A CreateField object represents a table field (column) in the scheme clause of the CREATE command:
    Syntax: 
        _name_ _type_

        {IDENTIFIER} _name_: [a-zA-Z_]\w*
        {KEYWORD} _type_: [INT|FLOAT|VARCHAR|TIMESTAMP]
    """

    def __init__(self, field_name, _type):
        super().__init__(field_name)
        self.type = _type;

    def __str__(self):
        return f"{self.identifier} {self.type}"

    def __repr__(self):
        return self.__str__()

