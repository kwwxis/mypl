#!python3
# This script runs the lexer and outputs all the tokens

import sys
import mypl_token
import mypl_lexer
import mypl_error

def main(filename):
    try:
        my_stream = open(filename, 'r')
        my_lexer  = mypl_lexer.Lexer(my_stream)

        t = my_lexer.next_token()

        while t.type != mypl_token.Token.EOS:
            print(t)

            # add a newline if semicolon to distinguish between lines better
            if t.type == mypl_token.Token.SEMICOLON:
                print('')

            t = my_lexer.next_token()

    except IOError as e:
        print("error: unable to open file '" + filename + "'")
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