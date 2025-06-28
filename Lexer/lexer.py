# lexer
import ply.lex as lex
import Lexer.tokens as tokens  
lexer = lex.lex(module=tokens)

def find_column(code, token):
    line_start = code.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1


def print_tokens(code):
    lexer.input(code)
    tokens_list = list(lexer)

    print(f"{'Line':>6} | {'Column':>7} | {'Token':<20} | Value")
    print('-' * 80)
    for tok in tokens_list:
        print(f"{tok.lineno:>6} | {find_column(code, tok):>7} | {tok.type:<20} | {tok.value}")



