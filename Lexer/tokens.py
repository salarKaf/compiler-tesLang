#tokens

import re

tokens = [
    'ID', 'NUMBER', 'STRING', 'MSTRING',
    'PLUS', 'MINUS', 'MULTIPLY', 'DIVIDE',
    'EQ', 'EQEQ', 'NEQ', 'GTEQ', 'LTEQ', 'GREATER_THAN', 'LESS_THAN',
    'DBL_COLON', 'SEMI_COLON', 'COMMA',
    'LPAREN', 'RPAREN', 'LCURLYEBR', 'RCURLYEBR', 'LSQUAREBR', 'RSQUAREBR',
    'OR', 'AND', 'NOT',
    'QMARK', 'COLON'
]

keywords = {
    'funk': 'FUNK',
    'return': 'RETURN',
    'as': 'AS',
    'for': 'FOR',
    'to': 'TO',
    'length': 'LEN',
    'begin': 'BEGIN',
    'end': 'END',
    'if': 'IF',
    'else': 'ELSE',
    'while': 'WHILE',
    'do': 'DO',
    'int': 'INT',
    'vector': 'VECTOR',
    'str': 'STR',
    'mstr': 'MSTR',
    'bool': 'BOOL',
    'null': 'NULL',
    'true': 'TRUE',
    'false': 'FALSE',
    'print': 'PRINT',
}

tokens = list(set(tokens + list(keywords.values())))



t_PLUS           = r'\+'
t_MINUS          = r'-'
t_MULTIPLY       = r'\*'
t_DIVIDE         = r'/'
t_EQEQ           = r'=='
t_NEQ            = r'!='
t_GTEQ           = r'>='
t_LTEQ           = r'<='
t_GREATER_THAN   = r'>'
t_LESS_THAN      = r'<'
t_EQ             = r'='
t_DBL_COLON      = r'::'
t_SEMI_COLON     = r';'
t_COMMA          = r','
t_QMARK          = r'\?'
t_COLON          = r':'
t_OR             = r'\|\|'
t_AND            = r'&&'
t_NOT            = r'!'
t_LPAREN         = r'\('
t_RPAREN         = r'\)'
t_LCURLYEBR      = r'\{'
t_RCURLYEBR      = r'\}'
t_LSQUAREBR      = r'\['
t_RSQUAREBR      = r'\]'

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = keywords.get(t.value, 'ID')
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_STRING(t):
    r'("([^"\\\n]|\\.)*")|(\'([^\'\\\n]|\\.)*\')'
    t.value = t.value[1:-1]
    return t


def t_MSTRING(t):
    r'"""(.|\n)*?"""'
    t.lexer.lineno += t.value.count('\n')  
    t.value = t.value[3:-3]  
    return t


def t_comment(t):
    r'</'
    start_pos = t.lexer.lexpos - 2  
    depth = 1

    while True:
        if t.lexer.lexpos >= len(t.lexer.lexdata):
            print(f"Error: Unclosed comment starting at line {t.lineno}")
            # بازگشت به محتوای کامنت به عنوان کد
            comment_body = t.lexer.lexdata[start_pos:]
            t.lexer.input(comment_body)
            t.lexer.lineno = t.lineno  # حفظ شماره خط
            t.lexer.lexpos = 0
            return None

        if t.lexer.lexdata[t.lexer.lexpos:t.lexer.lexpos+2] == '</':
            depth += 1
            t.lexer.lexpos += 2
        elif t.lexer.lexdata[t.lexer.lexpos:t.lexer.lexpos+2] == '/>':
            depth -= 1
            t.lexer.lexpos += 2
            if depth == 0:
                return  
        else:
            if t.lexer.lexdata[t.lexer.lexpos] == '\n':
                t.lexer.lineno += 1
            t.lexer.lexpos += 1


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_ignore = ' \t'






def t_error(t):
    invalid_str = t.value[0]
    i = 1
    while True:
        next_char = t.lexer.lexdata[t.lexer.lexpos]
        if next_char in [' ' , ';' , "\n" , '\t'] :
            print("Illegal token \"" + invalid_str[0:i - 1] + "\" in line " + t.lineno.__str__())
            break
        invalid_str += t.value[i]
        i = i + 1
        t.lexer.skip(1)



