#!python3
# This script parses and prints the AST

import sys
import mypl_lexer
import mypl_parser
import mypl_error
import mypl_ast
import mypl_ast_printer

def main(filename):
    try:
        file_stream = open(filename, 'r')
        the_lexer = mypl_lexer.Lexer(file_stream)
        the_parser = mypl_parser.Parser(the_lexer)
        stmt_list = the_parser.parse()
        print_visitor = mypl_ast_printer.ASTPrintVisitor(sys.stdout)
        stmt_list.accept(print_visitor)
    except IOError as e:
        print("error: unable to open file '"+filename+"'")
        sys.exit(1)
    except mypl_error.Error as e:
        print(e)
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage:', sys.argv[0], 'source-code-file')
        sys.exit(1)
    else:
        main(sys.argv[1])