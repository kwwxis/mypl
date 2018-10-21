#!python3
print_visitor = None
# BASE --------------------------------------------------------------------------------

class ASTNode:
    """The base class for the abstract syntax tree."""
    def accept(self, visitor): pass

    """Get first token of this node"""
    def first_token(self): pass

class Stmt(ASTNode):
    """The base class for all statement nodes."""
    def accept(self, visitor): pass

    """Get first token of this node"""
    def first_token(self): pass

class Expr(ASTNode):
    """The base class for all expression nodes."""
    def accept(self, visitor): pass

    """Get first token of this node"""
    def first_token(self): pass

class BoolExpr(ASTNode):
    """The base class for Boolean (expression) nodes."""
    def accept(self, visitor): pass

    """Get first token of this node"""
    def first_token(self): pass

# IMPL --------------------------------------------------------------------------------

class StmtList(ASTNode):
    """A statement list consists of a list of statements."""

    def __init__(self):
        self.stmts = [] # list of Stmt

    def accept(self, visitor):
        visitor.visit_stmt_list(self)

    def first_token(self):
        if len(self.stmts) == 0:
            return None
        return self.stmts[0].first_token()

# PRINT/READ STATEMENTS

class PrintStmt(Stmt):
    """A print statement consists of a expression to print."""

    def __init__(self):
        self.expr = None # an Expr node
        self.which = None # a PRINT or PRINTLN node
        self.is_println = False

    def accept(self, visitor):
        visitor.visit_print_stmt(self)

    def first_token(self):
        return self.which

class ReadExpr(Expr):
    """A read expression consists of a message string."""

    def __init__(self):
        self.expr = None # expr
        self.which = None # a READINT or READSTR node
        self.is_read_int = False

    def accept(self, visitor):
        visitor.visit_read_expr(self)

    def first_token(self):
        return self.which

# LEN EXPR

class LenExpr(Expr):
    """A length expression consists of something with a size"""

    def __init__(self):
        self.name = None # a LEN node
        self.expr = None # expr

    def accept(self, visitor):
        visitor.visit_len_expr(self)

    def first_token(self):
        return self.name

# ASSIGN STATEMENT

class AssignStmt(Stmt):
    """An assignment statement consists of an identifier (possibly
    indexed), and an expression.
    """

    def __init__(self):
        self.lhs = None # Token (ID)
        self.index_expr = None # Expr node
        self.rhs = None # Expr node

    def accept(self, visitor):
        visitor.visit_assign_stmt(self)

    def first_token(self):
        return self.lhs

# EXPR/ID/VALUE STATEMENTS

class SimpleExpr(Expr):
    """A simple expression consists of a value or identifier."""

    def __init__(self):
        self.term = None # Token
        self.negated = False

    def accept(self, visitor):
        visitor.visit_simple_expr(self)

    def to_bool_expr(self):
        bool_expr = SimpleBoolExpr()
        bool_expr.expr = self
        bool_expr.negated = self.negated
        bool_expr.expr.negated = False
        return bool_expr

    def first_token(self):
        return self.term

class IndexExpr(Expr):
    """An index expression consists of an identifier and an expression."""

    def __init__(self):
        self.identifier = None # Token (ID)
        self.expr = None # Expr node
        self.negated = False

    def accept(self, visitor):
        visitor.visit_index_expr(self)

    def to_bool_expr(self):
        bool_expr = SimpleBoolExpr()
        bool_expr.expr = self
        bool_expr.negated = self.negated
        bool_expr.expr.negated = False
        return bool_expr

    def first_token(self):
        return self.identifier

class ListExpr(Expr):
    """A list expression consists of a list of elements (expressions)."""

    def __init__(self):
        super(ListExpr, self).__init__()
        self.lbracket = None # reference point
        self.expressions = [] # list of Expr nodes

    def accept(self, visitor):
        visitor.visit_list_expr(self)

    def first_token(self):
        return self.lbracket

class ComplexExpr(Expr):
    """A complex expression consist of an expression, followed by a
    mathematical operator (+, -, *, etc.), followed by another
    (possibly complex) expression.
    """

    def __init__(self):
        self.first_operand = None # Expr node
        self.rel = None # Token (+, -, *, etc.)
        self.second_operand = None # Expr node

    def accept(self, visitor):
        visitor.visit_complex_expr(self)

    def to_bool_expr(self):
        self.accept(print_visitor)

        bool_expr = ComplexBoolExpr()

        # [<negated>] <first_expr> <bool_rel> <second_expr> [<bool_connector> <second_operand>]

        bool_expr.negated = self.first_operand.negated
        bool_expr.first_expr = self.first_operand
        bool_expr.first_expr.negated = False
        bool_expr.bool_rel = self.rel

        right = self.second_operand

        if isinstance(right, ComplexExpr):
            bool_expr.second_expr = right.first_operand
            bool_expr.has_bool_connector = True
            bool_expr.bool_connector = right.rel
            bool_expr.second_operand = right.second_operand.to_bool_expr()
            if bool_expr.second_operand == False:
                return False
        elif isinstance(right, SimpleExpr):
            bool_expr.second_expr = right
            bool_expr.has_bool_connector = False
        elif isinstance(right, IndexExpr):
            bool_expr.second_expr = right
            bool_expr.has_bool_connector = False
        elif isinstance(right, LenExpr):
            bool_expr.second_expr = right
            bool_expr.has_bool_connector = False
        else:
            return False

        return bool_expr

    def first_token(self):
        return self.first_operand.first_token()

# BOOLEAN EXPRESSIONS

class SimpleBoolExpr(BoolExpr):
    """A simple boolean expression consists of a single expression,
    possibly negated.
    """

    def __init__(self):
        self.expr = None # Expr node
        self.negated = False

    def accept(self, visitor):
        visitor.visit_simple_bool_expr(self)

    def first_token(self):
        return self.expr.first_token()

class ComplexBoolExpr(BoolExpr):
    """A complex boolean expression consists of an expression, a Boolean
    relation (==, <=, !=, etc.), another expression, and possibly an
    'and' or 'or' followed by additional boolean expressions. An
    entire complex boolean expression can also be negated.
    """

    # [<negated>] <first_expr> <bool_rel> <second_expr> [<bool_connector> <second_operand>]
    def __init__(self):
        super(ComplexBoolExpr, self).__init__()
        self.negated = False
        self.first_expr = None          # Expr node
        self.bool_rel = None            # Token (==, <=, !=, etc.)
        self.second_expr = None         # Expr node
        self.has_bool_connector = False # true if has an AND or OR
        self.bool_connector = None      # Token (AND or OR)
        self.second_operand = None      # Expr node

    def to_simple(self):
        simple_bool_expr = SimpleBoolExpr()
        simple_bool_expr.negated = self.negated
        simple_bool_expr.expr = self.first_expr
        return simple_bool_expr

    def accept(self, visitor):
        visitor.visit_complex_bool_expr(self)

    def first_token(self):
        return self.first_expr.first_token()

# IF STATEMENTS

class BasicIf:
    """A basic if holds a condition (Boolean expression) and a list of
    statements (the body of the if).
    """

    def __init__(self):
        self.which = None # token
        self.bool_expr = None # BoolExpr node
        self.stmt_list = StmtList()

    def first_token(self):
        return self.which

class IfStmt(Stmt):
    """An if stmt consists of a basic if part, a (possibly empty) list of
    else ifs, and an optional else part (represented as a statement
    list).
    """

    def __init__(self):
        self.which = None # token
        self.if_part = BasicIf()
        self.elseifs = [] # list of BasicIf
        self.has_else = False
        self.else_stmts = StmtList()

    def accept(self, visitor):
        visitor.visit_if_stmt(self)

    def first_token(self):
        return self.which

# LOOP STATEMENTS

class WhileStmt(Stmt):
    """A while statement consists of a condition (Boolean expression) and
    a statement list (the body of the while).
    """

    def __init__(self):
        self.which = None # token
        self.bool_expr = None # a BoolExpr node
        self.stmt_list = StmtList()

    def accept(self, visitor):
        visitor.visit_while_stmt(self)

    def first_token(self):
        return self.which

# VISITOR BASE --------------------------------------------------------------------------------

class Visitor:
    """The base class for AST visitors."""

    def visit_stmt_list(self, stmt_list): pass
    def visit_simple_bool_expr(self, simple_bool_expr): pass
    def visit_complex_bool_expr(self, complex_bool_expr): pass
    def visit_if_stmt(self, if_stmt): pass
    def visit_while_stmt(self, while_stmt): pass
    def visit_print_stmt(self, print_stmt): pass
    def visit_assign_stmt(self, assign_stmt): pass
    def visit_simple_expr(self, simple_expr): pass
    def visit_index_expr(self, index_expr): pass
    def visit_list_expr(self, list_expr): pass
    def visit_read_expr(self, read_expr): pass
    def visit_complex_expr(self, complex_expr): pass
    def visit_len_expr(self, len_expr): pass

import sys
import mypl_ast_printer
print_visitor = mypl_ast_printer.ASTPrintVisitor(sys.stdout)