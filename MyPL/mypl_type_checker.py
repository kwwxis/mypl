#!python3

from mypl_util import *
from mypl_token import *

import mypl_ast
import mypl_symbol_table

#import sys
#import mypl_ast_printer
#print_visitor = mypl_ast_printer.ASTPrintVisitor(sys.stdout)

class TypeChecker(mypl_ast.Visitor):

    def __init__(self):
        self.sym = mypl_symbol_table.SymbolTable()
        self.ctype = None

    def visit_stmt_list(self, stmt_list):
        self.sym.push_environment()
        for stmt in stmt_list.stmts:
            stmt.accept(self)
        self.sym.pop_environment()

    # HELPER FUNCTIONS
    # ~~~~~~~~~~~~~~~~

    def __gettype_or_fail(self, identifier):
        if self.sym.variable_exists(identifier.lexeme):
            return self.sym.get_variable_type(identifier.lexeme)
        else:
            identifier.error("undefined variable '"+xstr(identifier.lexeme)+"'")
            return None

    def __checkrel_int(self, rel):
        return (rel.type in [Token.PLUS, Token.MINUS, Token.MULTIPLY, Token.DIVIDE, Token.MODULUS, \
                        Token.EQUAL, Token.LESS_THAN, Token.GREATER_THAN, Token.LESS_THAN_EQUAL, \
                        Token.GREATER_THAN_EQUAL, Token.NOT_EQUAL])

    def __checkrel_string(self, rel):
        return rel.type == Token.PLUS

    def __checkrel_bool(self, rel):
        return (rel.type in [Token.EQUAL, Token.NOT_EQUAL])

    def __checkrel_compare(self, rel):
        return (rel.type in [Token.EQUAL, Token.LESS_THAN, Token.GREATER_THAN, Token.LESS_THAN_EQUAL, \
                        Token.GREATER_THAN_EQUAL, Token.NOT_EQUAL])

    # PRINT/READ STATEMENTS
    # ~~~~~~~~~~~~~~~~~~~~~

    def visit_print_stmt(self, print_stmt):
        print_stmt.expr.accept(self)

    def visit_read_expr(self, read_expr):
        read_expr.expr.accept(self)
        if read_expr.is_read_int:
            self.ctype = Token.INT
        else:
            self.ctype = Token.STRING

    # LEN EXPR
    # ~~~~~~~~

    def visit_len_expr(self, len_expr):
        len_expr.expr.accept(self)

    # ASSIGN STATEMENT
    # ~~~~~~~~~~~~~~~~

    def visit_assign_stmt(self, assign_stmt):
        # name and type of variable being modified
        var_name = assign_stmt.lhs.lexeme
        is_index = False

        # accept indexed ID (modifing element of variable instead of variable)
        if assign_stmt.index_expr != None:
            assign_stmt.index_expr.accept(self)
            is_index = True

        # accept rhs
        assign_stmt.rhs.accept(self)

        # get type of variable, or add it if it doesn't exist
        if self.sym.variable_exists(var_name):
            var_type = self.sym.get_variable_type(var_name)

            if is_index:
                if var_type == Token.ARRAY or var_type == Token.STRING:
                    return
                else:
                    assign_stmt.first_token().error("cannot access index on the type " + xstr(var_type))
                    return

            # check if match
            if self.ctype != var_type and var_type != Token.NA and self.ctype != Token.NA:
                assign_stmt.first_token().error("expected " + xstr(var_type) + " for '" + \
                    xstr(var_name) + "', got " + xstr(self.ctype))
            else:
                self.sym.set_variable_type(var_name, self.ctype)
        else:
            if is_index:
                assign_stmt.first_token().error("cannot access index on nonexistent variable, " + xstr(var_name))

            self.sym.add_variable(var_name)
            self.sym.set_variable_type(var_name, self.ctype)


    # EXPR/ID/VALUE STATEMENTS
    # ~~~~~~~~~~~~~~~~~~~~~~~~

    def visit_simple_expr(self, simple_expr):
        term = simple_expr.term

        if term.type == Token.ID:
            # variable
            self.ctype = self.__gettype_or_fail(term)
        else:
            # primitive
            self.ctype = term.type

        return

    def visit_index_expr(self, index_expr):
        # identifier[expr]

        # first check if variable exists and is an array
        array_name = index_expr.identifier.lexeme
        array_type = self.__gettype_or_fail(index_expr.identifier)

        if array_type != Token.ARRAY and array_type != Token.STRING:
            index_expr.identifier.error("expected an array or string type for index access on '" + xstr(array_name) + "', got " + xstr(array_type))

        # accept index expressions
        index_expr.expr.accept(self)

        # indices should be ints
        if self.ctype != Token.INT and self.ctype != Token.NA:
            index_expr.first_token().error('expected INT, got ' + xstr(self.ctype))

        # set current type
        self.ctype = Token.NA

    def visit_list_expr(self, list_expr):
        # common_type is the type that all items (item_type) in the list should match
        # it is set to the type of the first item in the list
        common_type = None

        # Make sure everything in the array has the same type
        for expr in list_expr.expressions:
            expr.accept(self)
            item_type = self.ctype

            if common_type == None:
                common_type = item_type
            elif item_type != common_type:
                expr.first_token().error("expected " + xstr(common_type) + ", got " + xstr(item_type))

        # Set to curren type to array type of common_type
        self.ctype = Token.ARRAY

    def visit_complex_expr(self, complex_expr):
        # accept left operand
        complex_expr.first_operand.accept(self)
        left_type = self.ctype
        rel = complex_expr.rel

        # accept right operand
        complex_expr.second_operand.accept(self)
        right_type = self.ctype

        # Both operands must be of same type
        if left_type != right_type:
            if left_type == Token.STRING and right_type == Token.INT:
                # allow string and int concatenation if int is right-hand side
                self.ctype = Token.STRING
            elif left_type == Token.NA or right_type == Token.NA:
                # If either operand is NA, then ctype should become name
                self.ctype = Token.NA
            else:
                complex_expr.second_operand.first_token().error("expected " + xstr(left_type) + ", got " + xstr(right_type))
        else:
            # ctype should right now be set to right_type
            # left_type and right_type are the same, so no need to change anything
            pass

        if left_type == Token.ARRAY:
            if rel != Token.PLUS:
                rel.error("cannot perform " + rel.type + " on ARRAY type")
        elif left_type == Token.INT:
            if self.__checkrel_int(rel) == False:
                rel.error("cannot perform " + rel.type + " on INT type")
        elif left_type == Token.STRING:
            if self.__checkrel_string(rel) == False:
                rel.error("cannot perform " + rel.type + " on STRING type")
        elif left_type == Token.BOOL:
            if self.__checkrel_bool(rel) == False:
                rel.error("cannot perform " + rel.type + " on BOOL type")

    # BOOLEAN EXPRESSIONS
    # ~~~~~~~~~~~~~~~~~~~

    def visit_simple_bool_expr(self, simple_bool_expr):
        simple_bool_expr.expr.accept(self)

        if self.ctype != Token.BOOL and self.ctype != Token.NA:
            simple_bool_expr.expr.first_token().error('condition must be of BOOL type, instead got ' + xstr(self.ctype))

    def visit_complex_bool_expr(self, complex_bool_expr):
        complex_bool_expr.first_expr.accept(self)
        first_type = self.ctype

        complex_bool_expr.second_expr.accept(self)
        second_type = self.ctype

        # Both operands must be of same type
        if first_type != second_type:
            complex_bool_expr.second_expr.first_token().error('expected '+xstr(first_type)+', got ' + xstr(second_type))

        # Check operator
        if first_type == Token.INT:
            if self.__checkrel_compare(complex_bool_expr.bool_rel) == False:
                complex_bool_expr.bool_rel.error( \
                    'cannot use ' + complex_bool_expr.bool_rel.type + ' to compare INT types')
        elif first_type == Token.BOOL:
            if self.__checkrel_bool(complex_bool_expr.bool_rel) == False:
                complex_bool_expr.bool_rel.error( \
                    'cannot use ' + complex_bool_expr.bool_rel.type + ' to compare BOOL types')
        else:
            complex_bool_expr.first_expr.first_token().error('encountered uncomparable type ' + xstr(first_type))

        if complex_bool_expr.has_bool_connector:
            # 'second_operand' is either a complex or simple bool expr, both of which
            # will set ctype to BOOL. So no need to check anything here.
            complex_bool_expr.second_operand.accept(self)

        self.ctype = Token.BOOL

    # IF STATEMENTS
    # ~~~~~~~~~~~~~

    def visit_if_stmt(self, if_stmt):
        # IF
        if_stmt.if_part.bool_expr.accept(self)
        # THEN
        if_stmt.if_part.stmt_list.accept(self)
        for elseif in if_stmt.elseifs:
            # ELSE IF
            elseif.bool_expr.accept(self)
            # THEN
            elseif.stmt_list.accept(self)
        if if_stmt.has_else:
            # ELSE
            if_stmt.else_stmts.accept(self)

    # LOOP STATEMENTS
    # ~~~~~~~~~~~~~~~

    def visit_while_stmt(self, while_stmt):
        # WHILE
        while_stmt.bool_expr.accept(self)
        # DO
        while_stmt.stmt_list.accept(self)

