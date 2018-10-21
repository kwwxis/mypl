#!python3

import mypl_lexer
from mypl_token import *
import mypl_error
import mypl_ast as ast

import sys
import mypl_ast_printer
print_visitor = mypl_ast_printer.ASTPrintVisitor(sys.stdout)

class Parser:

    def __init__(self, lexer):
        self.lexer = lexer
        self.c = None # c - cursor/current token
        self.pc = None # previous current token

    # PRIMARY FUNCTION
    # ------------------------------------------------------------------------------------------

    def parse(self):
        self.c = None
        self.pc = None

        root_node = ast.StmtList()

        self.next()
        self.stmts(root_node)
        self.eat(Token.EOS, 'expecting end of file')

        return root_node

    # HELPER FUNCTIONS
    # ------------------------------------------------------------------------------------------

    def next(self):
        self.pc = self.c
        self.c = self.lexer.next_token()
        return

    # if c.type is tokentype, then calls next(), otherwise raises error
    # If tokentype is True, then always succeeds
    # If tokentype is False, then always fails
    def eat(self, tokentype, error_msg=None):
        if self.c.type == tokentype or tokentype == True:
            self.next()
            return tokentype
        else:
            self.error(error_msg)
        return

    # eat only if matches the given tokentype and return true,
    # otherwise do nothing and return false
    def optional(self, tokentype):
        if self.c.type == tokentype or tokentype == True:
            self.eat(tokentype, None)
            return True
        return False

    # require that the previous token or the current token equals one of the passed in varargs
    # if the current token equals, eat
    # if the previous token equals, do nothing
    # returns the matching token or throws error if no match
    def require(self, error_msg, *args):
        for tokentype in args:
            if self.c.type == tokentype or tokentype == True:
                self.next()
                return self.c
            if self.pc.type == tokentype:
                return self.pc
        self.error(error_msg)
        return None

    # same as eat, but can take in multiple possible tokentypes
    # and will succeed if any of them matches
    # If success, returns the first token that was the match
    def any(self, error_msg, *args):
        for tokentype in args:
            if self.c.type == tokentype or tokentype == True:
                token = self.c
                self.next()
                return token
        self.error(error_msg)
        return None

    def any_optional(self, *args):
        for tokentype in args:
            if self.c.type == tokentype or tokentype == True:
                token = self.c
                self.next()
                return token
        return None

    def error(self, error_msg):
        if error_msg == None:
            error_msg = 'unknown error'
        error_msg = error_msg + ' instead got ' + self.c.type + '(\'' + self.c.lexeme + '\')'
        self.c.error(error_msg)
        return

    # BEGIN STMTS
    # ------------------------------------------------------------------------------------------

    def stmts(self, stmt_list_node = None):
        if stmt_list_node is None:
            stmt_list_node = ast.StmtList()

        # <output>
        ret = None
        if self.c.type == Token.PRINT:
            self.next()
            ret = self.output()
        # <output>
        elif self.c.type == Token.PRINTLN:
            self.next()
            ret = self.output()
        # <assign>
        elif self.c.type == Token.ID:
            self.next()
            ret = self.assign()
        # <conditional>
        elif self.c.type == Token.IF:
            ret = self.cond()
        # <loop>
        elif self.c.type == Token.WHILE:
            ret = self.loop()
        # anything else
        else:
            self.c.error("unexpected token: " + self.c.type + '(\'' + self.c.lexeme + '\')')

        if ret is not None:
            stmt_list_node.stmts.append(ret)

        # BLOCK EXIT
        if self.c.type == Token.RBRACE or \
                self.c.type == Token.ELSEIF or \
                self.c.type == Token.ELSE:
            return stmt_list_node
        # END OF STREAM
        if self.c.type == Token.EOS:
            return stmt_list_node
        # Continue...
        else:
            self.stmts(stmt_list_node)
            return stmt_list_node


    # PRINT/READ STATEMENTS
    # ------------------------------------------------------------------------------------------

    # <input>
    def input(self):
        read_node = ast.ReadExpr()

        which = self.require('expected "readint" or "readstr"', Token.READINT, Token.READSTR).type
        read_node.which = which
        read_node.is_read_int = (which == Token.READINT)

        self.eat(Token.LPAREN, 'expected "("')
        read_node.expr = self.expr()
        self.require('expected ")"', Token.RPAREN)

        return read_node

    # <output>
    def output(self):
        print_node = ast.PrintStmt()

        which = self.require('expected "print" or "println"', Token.PRINT, Token.PRINTLN).type
        print_node.which = which
        print_node.is_println = (which == Token.PRINTLN)

        self.eat(Token.LPAREN, 'expected "("')
        print_node.expr = self.expr()
        self.require('expected ")"', Token.RPAREN)
        self.semicolon()

        return print_node

    # LEN EXPR
    # ------------------------------------------------------------------------------------------

    def lenexpr(self):
        len_node = ast.LenExpr()

        len_node.name = self.require('expected "LEN"', Token.LEN).type

        self.eat(Token.LPAREN, 'expected "("')
        len_node.expr = self.expr()
        self.require('expected ")"', Token.RPAREN)

        return len_node

    # ASSIGN STATEMENT
    # ------------------------------------------------------------------------------------------

    # <assign>
    def assign(self):
        assign_node = ast.AssignStmt()

        # <id>
        assign_node.lhs = self.require("expected an identifier", Token.ID)

        # check for either "[" or "="
        which = self.any('expected "[#]" or "=" after id', Token.LBRACKET, Token.ASSIGN).type

        # <listindex> if was "["
        if which == Token.LBRACKET:
            assign_node.index_expr = self.listindex()
            self.eat(Token.ASSIGN, 'expected "="')

        # <expr>
        assign_node.rhs = self.expr()
        self.semicolon()

        return assign_node

    # EXPR/ID/VALUE STATEMENTS
    # ------------------------------------------------------------------------------------------

    # <expr>
    def expr(self):
        items = []

        while True:
            items.append( self.value() ) # returns an instance of ast.Expr

            op_token = None

            if op_token == None:
                op_token = self.math_rel_opt() # <math_rel> <expr> -- returns None if not found

            if op_token == None:
                op_token = self.bool_rel_opt() # <bool_rel> <expr> -- returns None if not found

            if op_token: # If an operator was found, op_token is a Token object
                items.append(op_token)
                continue

            break

        return self.exprcompile(items)

    # compile expr items
    def exprcompile(self, items):
        if len(items) == 1:
            return items[0]

        # we have a bunch of operands and operators in a single list, we have to compile them into
        # groups based on operator priority. Should be left-associative.

        op_weight_idx = None
        op_weight = None

        for idx, item in enumerate(items):
            if isinstance(item, Token) and item.weight() > 0:
                item_weight = item.weight()

                # If there are multiple of the lowest weight, then we use the one to the very right
                # in order to maintain left-associativity
                if not op_weight or item_weight <= op_weight:
                    op_weight = item_weight
                    op_weight_idx = idx

        # If we didn't find an operator, then that means there's only one item. But the if statement
        # at the top of this method should've taken care of that. Meaning this if statement should
        # never be true, if it does evaluate to true then something went very very wrong
        if not op_weight_idx:
            items[0].first_token().error('exprcompile - expected a following operator') # This should never happen

        # Split items into two lists with the index of the last lowested weighted operator
        # We want to perform the lowest-weight operations first and leave the highest-weight for last
        left_side_items = items[:op_weight_idx]
        right_side_items = items[op_weight_idx+1:]
        operator = items[op_weight_idx]

        node = ast.ComplexExpr()
        node.first_operand = self.exprcompile(left_side_items)
        node.second_operand = self.exprcompile(right_side_items)
        node.rel = operator

        return node

    # <value>
    def value(self):
        not_token = self.c
        has_not = self.optional(Token.NOT)

        which = self.any('expected value',
            Token.ID,           # SimpleExpr
            Token.STRING,       # SimpleExpr
            Token.INT,          # SimpleExpr
            Token.BOOL,         # SimpleExpr
            Token.READINT,      # ReadStmt
            Token.READSTR,      # ReadStmt
            Token.LEN,          # LenExpr
            Token.LPAREN,       # ComplexExpr
            Token.LBRACKET)     # ListExpr

        # ID <listindex>
        if which.type == Token.ID:
            if self.c.type == Token.LBRACKET:
                self.next()

                # IndexExpr
                index_node = ast.IndexExpr()
                index_node.identifier = which
                index_node.negated = has_not
                index_node.expr = self.listindex()
                return index_node
        # ReadStmt
        elif which.type == Token.READINT:
            return self.input()
        elif which.type == Token.READSTR:
            return self.input()
        # LenExpr
        elif which.type == Token.LEN:
            return self.lenexpr()
        # LPAREN <expr> RPAREN
        elif which.type == Token.LPAREN:
            nested_expr = self.expr()
            self.eat(Token.RPAREN, 'expected ")"')
            return nested_expr
        # LBRACKET <exprlist> RBRACKET
        elif which.type == Token.LBRACKET:
            if has_not:
                not_token.error('unexpected "not" before list')

            list_node = ast.ListExpr()
            list_node.lbracket = which

            if self.optional(Token.RBRACKET): # empty list
                return list_node

            list_node.expressions = self.exprlist()
            self.eat(Token.RBRACKET, 'expected "]"')

            return list_node

        # Non-SimpleExpr nodes should be handled in the if-elif block above
        # If not already returned, assume a SimpleExpr using which

        simple_expr_node = ast.SimpleExpr()
        simple_expr_node.term = which
        simple_expr_node.negated = has_not
        return simple_expr_node

    # <exprlist>
    def exprlist(self, list=[]):
        # empty
        if self.c.is_end():
            return list
        # <expr> <exprlisttail>
        else:
            list.append(self.expr())
            list = self.exprlisttail(list)
            return list

    # <exprlisttail>
    def exprlisttail(self, list):
        # empty
        if self.c.type == Token.RBRACKET:
            return list
        # COMMA <expr> <exprlisttail>
        else:
            self.eat(Token.COMMA, 'expected ","')
            list.append(self.expr())
            list = self.exprlisttail(list)
        return list

    # <math_rel>
    def math_rel(self):
        return self.any('expected math operator', \
            Token.PLUS, Token.MINUS, Token.DIVIDE, Token.MULTIPLY, Token.MODULUS)

    def math_rel_opt(self):
        return self.any_optional( # 'expected math operator', \
            Token.PLUS, Token.MINUS, Token.DIVIDE, Token.MULTIPLY, Token.MODULUS)

    # <listindex>
    def listindex(self):
        self.require('expected "["', Token.LBRACKET)
        if self.c.is_end():
            return None
        if self.optional(Token.RBRACKET):
            expr_node = ast.SimpleExpr()
            expr_node.term = self.lexer.DNE_token()
            return expr_node
        expr_node = self.expr()
        self.eat(Token.RBRACKET, 'expected "]"')
        return expr_node

    # eat Token.SEMICOLON
    def semicolon(self):
        if self.c.type == Token.EOS:
            return
        self.eat(Token.SEMICOLON, 'expected ";"')
        return

    # BOOLEAN EXPRESSIONS
    # ------------------------------------------------------------------------------------------

    # <bexpr>
    def bexpr(self):
        token_before_expr = self.c # for errors

        expr = self.expr() # get complex expr

        # ComplexExpr, IndexExpr, SimpleExpr have 'to_bool_expr'
        # ListExpr is not compatible

        if isinstance(expr, ast.ListExpr):
            token_before_expr.error("unexpected list, expected boolean expression")

        # convert to bool expr
        bool_expr = expr.to_bool_expr()

        # check for error
        if bool_expr == False:
            token_before_expr.error("invalid boolean expression")

        return bool_expr

    # <bool_rel>
    def bool_rel(self):
        return self.any('expected boolean relational operator', \
            Token.EQUAL, Token.LESS_THAN, Token.GREATER_THAN, Token.LESS_THAN_EQUAL, \
            Token.GREATER_THAN_EQUAL, Token.NOT_EQUAL, Token.AND, Token.OR)

    def bool_rel_opt(self):
        return self.any_optional( # 'expected boolean relational operator', \
            Token.EQUAL, Token.LESS_THAN, Token.GREATER_THAN, Token.LESS_THAN_EQUAL, \
            Token.GREATER_THAN_EQUAL, Token.NOT_EQUAL, Token.AND, Token.OR)


    # IF STATEMENTS
    # ------------------------------------------------------------------------------------------

    def cond(self):
        if_stmt = ast.IfStmt()

        if_stmt.which = self.require('expected "if"', Token.IF)
        if_stmt.if_part.bool_expr = self.bexpr()
        self.eat(Token.LBRACE, 'expected "{" after IF statement condition')
        if_stmt.if_part.stmt_list = self.stmts()

        if_stmt = self.condt(if_stmt)
        return if_stmt

    def condt(self, if_stmt):
        self.require('expected "}" following conditional block', Token.RBRACE)

        which = self.any_optional( # 'expected "else if", "else" or "}"', \
            Token.ELSEIF, Token.ELSE)

        if which is None:
            pass
        elif which.type == Token.ELSEIF:
            if_stmt.has_else = True

            basic_if_stmt = ast.BasicIf()
            basic_if_stmt.which = which

            basic_if_stmt.bool_expr = self.bexpr()
            self.eat(Token.LBRACE, 'expected "{" after ELSEIF statement condition')
            basic_if_stmt.stmt_list = self.stmts()

            if_stmt.elseifs.append(basic_if_stmt)

            if_stmt = self.condt(if_stmt) # recursive call to check for more ELSEIFs or ELSE
        elif which.type == Token.ELSE:
            if_stmt.has_else = True

            self.require('expected "else"', Token.ELSE)

            self.eat(Token.LBRACE, 'expected "{" after ELSE statement')

            if_stmt.else_stmts = self.stmts()

            self.eat(Token.RBRACE, 'expected "}" following conditional block')

        return if_stmt

    # LOOP STATEMENTS
    # ------------------------------------------------------------------------------------------

    # <loop>
    def loop(self):
        while_stmt_node = ast.WhileStmt()

        while_stmt_node.which = self.require('expected "while"', Token.WHILE)
        while_stmt_node.bool_expr = self.bexpr()
        self.eat(Token.LBRACE, 'expected "{" after WHILE statement condition')
        while_stmt_node.stmt_list = self.stmts()
        self.eat(Token.RBRACE, 'expected "}" following conditional repeating block')

        return while_stmt_node





















