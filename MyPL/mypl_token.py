#!python3

import mypl_error

class Token:
    # LANGUAGE-CONSTRUCT FUNCTIONS
    PRINT = 'PRINT'
    PRINTLN = 'PRINTLN'
    READINT = 'READINT'
    READSTR = 'READSTR'
    LEN = 'LEN'

    # LANGUAGE-CONSTRUCT BLOCKS
    IF = 'IF'
    THEN = 'THEN'
    ELSEIF = 'ELSEIF'
    ELSE = 'ELSE'
    END = 'END'
    WHILE = 'WHILE'
    DO = 'DO'

    # SYNTAX
    LPAREN = 'LPAREN'
    RPAREN = 'RPAREN'
    SEMICOLON = 'SEMICOLON'
    LBRACKET = 'LBRACKET'
    RBRACKET = 'RBRACKET'
    LBRACE = 'LBRACE'
    RBRACE = 'RBRACE'
    COMMA = 'COMMA'

    ID = 'ID'

    # OPERATORS
    PLUS = 'PLUS'
    MINUS = 'MINUS'
    DIVIDE = 'DIVIDE'
    MULTIPLY = 'MULTIPLY'
    MODULUS = 'MODULUS'

    # BOOLEAN OPERATORS
    NOT = 'NOT'
    AND = 'AND'
    OR = 'OR'
    EQUAL = 'EQUAL'
    NOT_EQUAL = 'NOT_EQUAL'
    LESS_THAN = 'LESS_THAN'
    GREATER_THAN = 'GREATER_THAN'
    LESS_THAN_EQUAL = 'LESS_THAN_EQUAL'
    GREATER_THAN_EQUAL = 'GREATER_THAN_EQUAL'

    # LITERALS
    STRING = 'STRING'
    INT = 'INT'
    BOOL = 'BOOL'
    ASSIGN = 'ASSIGN'
    ARRAY = 'ARRAY'

    # NULL-LIKE TYPES
    NA = 'NA' # Not Available (there is a non-null type, but we're not sure what it is until runtime)

    # SPECIAL
    EOS = 'EOS'
    DNE = 'DNE'

    def __init__(self, type, lexeme, line, column):
        self.type   = type
        self.lexeme = lexeme
        self.line   = line
        self.column = column

    def __str__(self):
        s = ''
        s += str(self.type)
        s += ' '
        s += "'"+str(self.lexeme)+"'"
        s += ' '
        s += str(self.line)+':'+str(self.column)
        return s

    def error(self, error_msg):
        raise mypl_error.Error(error_msg, self.line, self.column)

    def is_end(self):
        return self.type == Token.EOS or self.type == Token.SEMICOLON

    def weight(self):
        """ Get operator weight, non-operators have a weight of 0. A higher weight means more priority. """

        # Math operators

        if self.type == Token.PLUS:
            return 100
        elif self.type == Token.MINUS:
            return 100
        elif self.type == Token.DIVIDE:
            return 200
        elif self.type == Token.MULTIPLY:
            return 200
        elif self.type == Token.MODULUS:
            return 200

        # Boolean operators

        elif self.type == Token.AND:
            return 400
        elif self.type == Token.OR:
            return 400

        # Comparison operators

        elif self.type == Token.NOT:
            return 300
        elif self.type == Token.EQUAL:
            return 300
        elif self.type == Token.NOT_EQUAL:
            return 300
        elif self.type == Token.LESS_THAN:
            return 300
        elif self.type == Token.GREATER_THAN:
            return 300
        elif self.type == Token.LESS_THAN_EQUAL:
            return 300
        elif self.type == Token.GREATER_THAN_EQUAL:
            return 300

        # Non-operators

        else:
            return 0

    @staticmethod
    def token_from_native(value):
        x = type(value).__name__

        if x == 'str':
            return Token.STRING
        elif x == 'int':
            return Token.INT
        elif x == 'float':
            pass
        elif x == 'list':
            return Token.ARRAY
        elif x == 'tuple':
            return Token.ARRAY
        elif x == 'bool':
            return Token.BOOL

        return Token.NA