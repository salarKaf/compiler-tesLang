# ast_nodes.py
"""AST Node Classes for TesLang Compiler"""

class ASTNode:
    """Base class for all AST nodes"""
    pass

class Program(ASTNode):
    def __init__(self, functions):
        self.functions = functions

class Function(ASTNode):
    def __init__(self, name, params, return_type, body, line):
        self.name = name
        self.params = params
        self.return_type = return_type
        self.body = body
        self.line = line

class Parameter(ASTNode):
    def __init__(self, name, param_type, line):
        self.name = name
        self.param_type = param_type
        self.line = line

class VarDeclaration(ASTNode):
    def __init__(self, name, var_type, line):
        self.name = name
        self.var_type = var_type
        self.line = line

class Assignment(ASTNode):
    def __init__(self, target, value, line):
        self.target = target
        self.value = value
        self.line = line

class FunctionCall(ASTNode):
    def __init__(self, name, args, line):
        self.name = name
        self.args = args
        self.line = line

class Return(ASTNode):
    def __init__(self, value, line):
        self.value = value
        self.line = line

class If(ASTNode):
    def __init__(self, condition, then_stmt, else_stmt, line):
        self.condition = condition
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt
        self.line = line

class For(ASTNode):
    def __init__(self, var, start, end, body, line):
        self.var = var
        self.start = start
        self.end = end
        self.body = body
        self.line = line

class While(ASTNode):
    def __init__(self, condition, body, line):
        self.condition = condition
        self.body = body
        self.line = line

class BinaryOp(ASTNode):
    def __init__(self, left, op, right, line):
        self.left = left
        self.op = op
        self.right = right
        self.line = line

class UnaryOp(ASTNode):
    def __init__(self, op, operand, line):
        self.op = op
        self.operand = operand
        self.line = line

class Identifier(ASTNode):
    def __init__(self, name, line):
        self.name = name
        self.line = line

class Number(ASTNode):
    def __init__(self, value, line):
        self.value = value
        self.line = line

class String(ASTNode):
    def __init__(self, value, line):
        self.value = value
        self.line = line

class Boolean(ASTNode):
    def __init__(self, value, line):
        self.value = value
        self.line = line

class TernaryOp(ASTNode):
    def __init__(self, condition, true_expr, false_expr, line):
        self.condition = condition
        self.true_expr = true_expr
        self.false_expr = false_expr
        self.line = line

class ArrayAccess(ASTNode):
    def __init__(self, array, index, line):
        self.array = array
        self.index = index
        self.line = line

class ListCall(ASTNode):
    def __init__(self, size, line):
        self.size = size
        self.line = line