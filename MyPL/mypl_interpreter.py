#!python3

from mypl_util import *
from mypl_token import *
import mypl_ast
import mypl_symbol_table
import sys

class Interpreter(mypl_ast.Visitor):

    def __init__(self):
        self.sym = mypl_symbol_table.SymbolTable()
        self.cval = None
        self.ctype = None

    def visit_stmt_list(self, stmt_list):
        self.sym.push_environment()
        for stmt in stmt_list.stmts:
            stmt.accept(self)
        self.sym.pop_environment()

    # HELPER FUNCTIONS
    # ~~~~~~~~~~~~~~~~

    def __write(self, msg):
        sys.stdout.write(xstr(msg))

    def __read(self, msg):
        return input(msg)

    def __cast_str(self, x):
        if type(x) is bool:
            if x == True:
                return "true"
            else:
                return "false"
        if x == None:
            return ''
        return str(x)

    # PRINT/READ STATEMENTS
    # ~~~~~~~~~~~~~~~~~~~~~

    def visit_print_stmt(self, print_stmt):
        print_stmt.expr.accept(self)
        self.__write(self.cval)

        if print_stmt.is_println:
            self.__write("\n")

    def visit_read_expr(self, read_expr):
        read_expr.expr.accept(self)
        val = self.__read(self.cval)

        if read_expr.is_read_int:
            try:
                self.cval = int(val)
            except ValueError:
                self.cval = 0
            self.ctype = Token.INT
        else:
            self.cval = val
            self.ctype = Token.STRING

    # LEN EXPR
    # ~~~~~~~~

    def visit_len_expr(self, len_expr):
        len_expr.expr.accept(self)

        if type(self.cval) in (tuple, list):
            self.cval = len(self.cval)
        elif isinstance(self.cval, str):
            self.cval = len(self.cval)
        elif hasattr(self.cval, "__len__"):
            self.cval = self.cval.__len__()
        else:
            self.cval = -1

        self.ctype = Token.INT

    # ASSIGN STATEMENT
    # ~~~~~~~~~~~~~~~~

    def visit_assign_stmt(self, assign_stmt):
        var_name = assign_stmt.lhs.lexeme
        index = None

        if not self.sym.variable_exists(var_name):
            self.sym.add_variable(assign_stmt.lhs.lexeme)

        if assign_stmt.index_expr != None:
            assign_stmt.index_expr.accept(self)
            index = self.cval

        assign_stmt.rhs.accept(self)
        var_value = self.cval

        if assign_stmt.index_expr is None:
            self.sym.set_variable_value(var_name, var_value)
        else:
            arr = self.sym.get_variable_value(var_name)
            if index is None:
                arr.append(var_value)
            else:
                arr[index] = var_value

    # EXPR/ID/VALUE STATEMENTS
    # ~~~~~~~~~~~~~~~~~~~~~~~~

    def visit_simple_expr(self, simple_expr):
        if simple_expr.term.type == Token.ID:
            self.cval = self.sym.get_variable_value(simple_expr.term.lexeme)
            self.ctype = Token.ID
        elif simple_expr.term.type == Token.INT:
            self.cval = int(simple_expr.term.lexeme)
            self.ctype = Token.INT
        elif simple_expr.term.type == Token.DNE:
            self.cval = None
            self.ctype = Token.DNE
        elif simple_expr.term.type == Token.BOOL:
            self.cval = True if simple_expr.term.lexeme == "true" else False
            self.ctype = Token.BOOL
        elif simple_expr.term.type == Token.STRING:
            self.cval = simple_expr.term.lexeme
            self.ctype = Token.STRING

    def visit_index_expr(self, index_expr):
        # array
        array_name = index_expr.identifier.lexeme

        # index
        index_expr.expr.accept(self)
        index = int(self.cval)

        real_array = self.sym.get_variable_value(array_name)
        length = len(real_array)

        if index >= length or index < 0:
            index_expr.expr.first_token().error(
                'array index out of bounds! (idx: '+xstr(index)+', len: '+xstr(length)+')')

        self.cval = real_array[index]
        self.ctype = Token.token_from_native(self.cval)

    def visit_list_expr(self, list_expr):
        mylist = []

        for expr in list_expr.expressions:
            expr.accept(self)
            mylist.append(self.cval)

        self.cval = mylist
        self.ctype = Token.ARRAY

    def visit_complex_expr(self, complex_expr):
        # accept left operand
        complex_expr.first_operand.accept(self)
        l = self.cval
        l_type = self.ctype

        # accept right operand
        complex_expr.second_operand.accept(self)
        r = self.cval
        r_type = self.ctype

        rel = complex_expr.rel.type

        if rel == Token.PLUS:
            if l_type == Token.STRING:
                self.cval = l + self.__cast_str(r)
            else:
                self.cval = l + r
        elif rel == Token.MINUS:
            self.cval = l - r
        elif rel == Token.MULTIPLY:
            self.cval = l * r
        elif rel == Token.DIVIDE:
            self.cval = l / r
        elif rel == Token.MODULUS:
            self.cval = l % r
        else:
            complex_expr.rel.error("unknown or invalid operator")

        self.ctype = Token.token_from_native(self.cval)

    # BOOLEAN EXPRESSIONS
    # ~~~~~~~~~~~~~~~~~~~

    def visit_simple_bool_expr(self, simple_bool_expr):
        simple_bool_expr.expr.accept(self)
        if self.cval:
            self.cval = True
        else:
            self.cval = False
        if simple_bool_expr.negated:
            self.cval = not self.cval
        self.ctype = Token.BOOL

    def visit_complex_bool_expr(self, complex_bool_expr):
        complex_bool_expr.first_expr.accept(self)
        l = self.cval

        complex_bool_expr.second_expr.accept(self)
        r = self.cval

        rel = complex_bool_expr.bool_rel.type

        if rel == Token.EQUAL:
            self.cval = (l == r)
        elif rel == Token.NOT_EQUAL:
            self.cval = (l != r)
        elif rel == Token.LESS_THAN:
            self.cval = (l < r)
        elif rel == Token.GREATER_THAN:
            self.cval = (l > r)
        elif rel == Token.LESS_THAN_EQUAL:
            self.cval = (l <= r)
        elif rel == Token.GREATER_THAN_EQUAL:
            self.cval = (l >= r)
        else:
            complex_bool_expr.bool_rel.error("unknown or invalid operator")

        result = self.cval
        result2 = True

        if complex_bool_expr.has_bool_connector:
            complex_bool_expr.second_operand.accept(self)
            result2 = self.cval
        else:
            return result

        if complex_bool_expr.bool_connector.type == Token.AND:
            self.cval = (result and result2)
        else:
            self.cval = (result or result2)

        self.ctype = Token.BOOL

    # IF STATEMENTS
    # ~~~~~~~~~~~~~

    def visit_if_stmt(self, if_stmt):
        # IF
        if_stmt.if_part.bool_expr.accept(self)
        # THEN
        if self.cval:
            if_stmt.if_part.stmt_list.accept(self)
        else:
            any_true = False
            for elseif in if_stmt.elseifs:
                # ELSE IF
                elseif.bool_expr.accept(self)
                # THEN
                if self.cval:
                    any_true = True
                    elseif.stmt_list.accept(self)
                    break
            # ELSE
            if not any_true and if_stmt.has_else:
                if_stmt.else_stmts.accept(self)

    # LOOP STATEMENTS
    # ~~~~~~~~~~~~~~~

    def visit_while_stmt(self, while_stmt):
        # WHILE
        while_stmt.bool_expr.accept(self)
        state = self.cval
        while (state):
            # DO
            while_stmt.stmt_list.accept(self)

            while_stmt.bool_expr.accept(self)
            state = self.cval