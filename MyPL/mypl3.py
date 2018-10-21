#!python3
# This script performs just a type check

import sys
import mypl_lexer
import mypl_parser
import mypl_error
import mypl_ast
import mypl_type_checker

def main(filename):
    try:
        file_stream = open(filename, 'r')

        the_parser = mypl_parser.Parser(mypl_lexer.Lexer(file_stream))
        stmt_list = the_parser.parse()

        checker = mypl_type_checker.TypeChecker()
        stmt_list.accept(checker)
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