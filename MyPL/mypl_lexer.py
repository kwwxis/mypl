#!python3

from mypl_token import *
from mypl_error import *

class Lexer:

    def __init__(self, input_stream):
        self.line   = 1
        self.column = 1
        self.stream = input_stream

    # Input Stream Helper Functions
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __peek(self, len=1):
        pos     = self.stream.tell()
        symbol  = self.stream.read(len)

        self.stream.seek(pos)
        return symbol

    def __read(self, len=1):
        return self.stream.read(len)

    def __back(self, len=1):
        pos = self.stream.tell()
        self.stream.seek(pos - len)

    def __pos(self):
        return self.stream.tell()

    def __goto(self, pos):
        self.stream.seek(pos)

    # Walk Functions
    # ~~~~~~~~~~~~~~

    # walk through the stream until no more alphanumeric or underscores characters
    # return the alphanumeric string
    def __walkthru_id(self):
        s = ''
        while self.__peek().isalpha() or self.__peek().isdigit() or self.__peek() == '_':
            s += self.__read()
        return s

    # walk through string
    # end_char - either `'` or `"`
    def __walkthru_string(self, end_char):
        s = ''

        prev = self.__peek()
        while True:
            ch = self.__read()

            if ch == '':
                self.__raise('unexpected end of stream')
            if ch == '\n':
                self.__raise('encountered new line character in string')

            # break if encountered ending " and no leading \
            if ch == end_char and prev != '\\':
                break
            # escape character
            elif ch == '\\' and prev != '\\':
                prev = '\\'
                continue
            # everything else
            else:
                prev = ch
                s += ch

        return s

    def __walkthru_comment(self):
        while self.__peek(2) != '*/':
            self.__read()

    # walk through an integer
    def __walkthru_int(self):
        s = ''
        while self.__peek().isdigit():
            s += self.__read()
        return s

    # walk up to end of line or EOS, does not pass the actual new line character
    def __walkto_eol(self):
        while self.__peek() != '\n' and len(self.__peek()) != 0:
            self.__read()

    # Next Token
    # ~~~~~~~~~~

    def next_token(self):
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        # 8 is the length of the longest reserved keyword                           #
        # Remember to update this number if a longer keyword is added!!!!!          #
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

        s = self.__peek(8)

        # EOS (End of File/Stream)
        # ~~~~~~~~~~~~~~~~~~~~~~~~
        if len(s) == 0:
            return self.__token(Token.EOS, '', 0)

        # EOL Comments
        # ~~~~~~~~~~~~
        if (s[:2] == '//'):
            # walks right up to the new line character but not passing (or otherwise
            # EOS) calling next_token() will invoke the whitespace condition for "\n"
            # which'll update the line number and reset the column to 0
            self.__walkto_eol()
            return self.next_token()

        # Multi-Line Comments
        # ~~~~~~~~~~~~~~~~~~~
        elif (s[:1] == '/*'):
            self.__walkthru_comment()
            return self.next_token()

        # Default functions
        # ~~~~~~~~~~~~~~~~~
        elif (s[:8] == 'println('):
            return self.__token(Token.PRINTLN, 'println', 7)
        elif (s[:8] == 'readstr('):
            return self.__token(Token.READSTR, 'readstr', 7)
        elif (s[:8] == 'readint('):
            return self.__token(Token.READINT, 'readint', 7)
        elif (s[:6] == 'print('):
            return self.__token(Token.PRINT, 'print', 5)
        elif (s[:4] == 'len('):
            return self.__token(Token.LEN, 'len', 3)

        # Relational Operators
        # ~~~~~~~~~~~~~~~~~~~~
        # (this section must be before 'Math and Other Operators')
        # Must put longer before shorter, otherwise, '<', for example, could override '<='

        elif (s[:2] == '=='):
            return self.__token(Token.EQUAL, '==', 2)
        elif (s[:2] == '<='):
            return self.__token(Token.LESS_THAN_EQUAL, '<=', 2)
        elif (s[:2] == '>='):
            return self.__token(Token.GREATER_THAN_EQUAL, '>=', 2)
        elif (s[:2] == '!='):
            return self.__token(Token.NOT_EQUAL, '!=', 2)
        elif (s[:1] == '<'):
            return self.__token(Token.LESS_THAN, '<', 1)
        elif (s[:1] == '>'):
            return self.__token(Token.GREATER_THAN, '>', 1)

        # Keywords
        # ~~~~~~~~~
        elif (s[:7] == 'else if'):
            return self.__token(Token.ELSEIF, 'elseif', 7)
        elif (s[:5] == 'while'):
            return self.__token(Token.WHILE, 'while', 5)
        elif (s[:4] == 'else'):
            return self.__token(Token.ELSE, 'else', 4)
        elif (s[:3] == 'not'):
            return self.__token(Token.NOT, 'not', 3)
        elif (s[:3] == 'and'):
            return self.__token(Token.AND, 'and', 3)
        elif (s[:2] == 'if'):
            return self.__token(Token.IF, 'if', 2)
        elif (s[:2] == 'or'):
            return self.__token(Token.OR, 'or', 2)

        # Math and Other Operators
        # ~~~~~~~~~~~~~~~~~~~~~~~~
        elif (s[:1] == '+'):
            return self.__token(Token.PLUS, '+', 1)
        elif (s[:1] == '-'):
            return self.__token(Token.MINUS, '-', 1)
        elif (s[:1] == '/'):
            return self.__token(Token.DIVIDE, '/', 1)
        elif (s[:1] == '*'):
            return self.__token(Token.MULTIPLY, '*', 1)
        elif (s[:1] == '%'):
            return self.__token(Token.MODULUS, '%', 1)
        elif (s[:1] == '='):
            return self.__token(Token.ASSIGN, '=', 1)


        # Various Syntax
        # ~~~~~~~~~~~~~~
        elif (s[:1] == ','):
            return self.__token(Token.COMMA, ',', 1)
        elif (s[:1] == ';'):
            return self.__token(Token.SEMICOLON, ';', 1)
        elif (s[:1] == '('):
            return self.__token(Token.LPAREN, '(', 1)
        elif (s[:1] == ')'):
            return self.__token(Token.RPAREN, ')', 1)
        elif (s[:1] == '['):
            return self.__token(Token.LBRACKET, '[', 1)
        elif (s[:1] == ']'):
            return self.__token(Token.RBRACKET, ']', 1)
        elif (s[:1] == '{'):
            return self.__token(Token.LBRACE, '{', 1)
        elif (s[:1] == '}'):
            return self.__token(Token.RBRACE, '}', 1)

        # Boolean Literals
        # ~~~~~~~~~~~~~~~~
        elif (s[:4] == 'true'):
            return self.__token(Token.BOOL, 'true', 4)
        elif (s[:5] == 'false'):
            return self.__token(Token.BOOL, 'false', 5)

        # Number Literals
        # ~~~~~~~~~~~~~~~
        elif (s[:1].isdigit()):
            i = self.__walkthru_int()
            return self.__token(Token.INT, i, len(i), False)

        # String Literals
        # ~~~~~~~~~~~~~~~

        elif (s[:1] == '"' or s[:1] == "'"):
            self.__read(1) # skip the first " character
            s = self.__walkthru_string(s[:1]) # walks until ending "/' character (or errors on EOS or EOL)
            return self.__token(Token.STRING, s, len(s), False)

        # Identifiers
        # ~~~~~~~~~~~

        elif (s[:1].isalpha()):
            id = self.__walkthru_id()
            return self.__token(Token.ID, id, len(id), False)

        # Whitespace
        # ~~~~~~~~~~
        # (update column/line, but ignore as token)
        elif (s[:1].isspace()):
            if (s[:1] == '\n'):
                self.line += 1
                self.column = 1
            else:
                self.column += 1

            self.__read()
            return self.next_token()

        # Unknown Tokens
        # ~~~~~~~~~~~~~~
        else:
            self.__raise('encountered unexpected character: \'' + s[:1] + '\'')

    # Create a DNE token - represents a token of length 0 (a token that Does Not Exist)
    # Used represent that the space between two directly adjacent tokens has some significance
    def DNE_token(self):
        return self.__token(Token.DNE, '', 0, False)

    # Token object creation helper
    # params:
    #   type    - the token type
    #   lexeme  - the token lexeme
    #   inc     - the length of the lexeme, in otherwords, the number to INCrement the column/read by
    #   do_read - option to not do __read since the '__walk*' functions do __read on their own
    def __token(self, type, lexeme, inc, do_read = True):
        t = Token(type, lexeme, self.line, self.column)

        if do_read:
            self.__read(inc)

        self.column += inc
        return t

    # Raise an error -- a helper function because this is shorter to type
    def __raise(self, message):
        raise Error(message, self.line, self.column)

