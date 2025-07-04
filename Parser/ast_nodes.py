# ast_nodes.py
"""AST Node Classes for TesLang Compiler with Tree Display"""

class ASTNode:
    """Base class for all AST nodes"""
    
    def __str__(self):
        return self.__class__.__name__
    
    def __repr__(self):
        return self.__str__()
    
    def to_tree(self, indent=0, prefix=""):
        """Convert AST to tree string representation"""
        result = " " * indent + prefix + self.__class__.__name__
        
        # Add node-specific information
        if hasattr(self, 'name'):
            result += f" ({self.name})"
        elif hasattr(self, 'value'):
            result += f" ({self.value})"
        elif hasattr(self, 'op'):
            result += f" ({self.op})"
        
        result += "\n"
        
        # Process children
        children = []
        for attr_name, attr_value in self.__dict__.items():
            if attr_name.startswith('_') or attr_name == 'line':
                continue
            
            if isinstance(attr_value, ASTNode):
                children.append((attr_name, attr_value))
            elif isinstance(attr_value, list):
                for i, item in enumerate(attr_value):
                    if isinstance(item, ASTNode):
                        children.append((f"{attr_name}[{i}]", item))
        
        # Display children
        for i, (child_name, child_node) in enumerate(children):
            is_last = i == len(children) - 1
            child_prefix = "└── " if is_last else "├── "
            child_indent = indent + 4
            next_prefix = "    " if is_last else "│   "
            
            result += " " * indent + child_prefix + f"{child_name}: "
            result += child_node.to_tree(child_indent, "").strip() + "\n"
            
            # Add recursive children with proper indentation
            if hasattr(child_node, '__dict__'):
                grandchildren = []
                for attr_name, attr_value in child_node.__dict__.items():
                    if attr_name.startswith('_') or attr_name == 'line':
                        continue
                    
                    if isinstance(attr_value, ASTNode):
                        grandchildren.append((attr_name, attr_value))
                    elif isinstance(attr_value, list):
                        for j, item in enumerate(attr_value):
                            if isinstance(item, ASTNode):
                                grandchildren.append((f"{attr_name}[{j}]", item))
                
                for j, (grandchild_name, grandchild_node) in enumerate(grandchildren):
                    is_last_grandchild = j == len(grandchildren) - 1
                    grandchild_prefix = "└── " if is_last_grandchild else "├── "
                    grandchild_indent = child_indent + 4
                    
                    result += " " * child_indent + next_prefix + grandchild_prefix + f"{grandchild_name}: "
                    result += grandchild_node.to_tree(grandchild_indent + 4, "").strip() + "\n"
        
        return result

class Program(ASTNode):
    def __init__(self, functions):
        self.functions = functions
    
    def __str__(self):
        return f"Program(functions={len(self.functions)})"

class Function(ASTNode):
    def __init__(self, name, params, return_type, body, line):
        self.name = name
        self.params = params
        self.return_type = return_type
        self.body = body
        self.line = line
    
    def __str__(self):
        return f"Function({self.name}, {self.return_type})"

class Parameter(ASTNode):
    def __init__(self, name, param_type, line):
        self.name = name
        self.param_type = param_type
        self.line = line
    
    def __str__(self):
        return f"Parameter({self.name}: {self.param_type})"

class VarDeclaration(ASTNode):
    def __init__(self, name, var_type, line):
        self.name = name
        self.var_type = var_type
        self.line = line
    
    def __str__(self):
        return f"VarDeclaration({self.name}: {self.var_type})"

class Assignment(ASTNode):
    def __init__(self, target, value, line):
        self.target = target
        self.value = value
        self.line = line
    
    def __str__(self):
        target_str = self.target if isinstance(self.target, str) else str(self.target)
        return f"Assignment({target_str})"

class FunctionCall(ASTNode):
    def __init__(self, name, args, line):
        self.name = name
        self.args = args
        self.line = line
    
    def __str__(self):
        return f"FunctionCall({self.name}, {len(self.args)} args)"

class Return(ASTNode):
    def __init__(self, value, line):
        self.value = value
        self.line = line
    
    def __str__(self):
        return f"Return({self.value is not None})"

class If(ASTNode):
    def __init__(self, condition, then_stmt, else_stmt, line):
        self.condition = condition
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt
        self.line = line
    
    def __str__(self):
        return f"If(has_else={self.else_stmt is not None})"

class For(ASTNode):
    def __init__(self, var, start, end, body, line):
        self.var = var
        self.start = start
        self.end = end
        self.body = body
        self.line = line
    
    def __str__(self):
        return f"For({self.var})"

class While(ASTNode):
    def __init__(self, condition, body, line):
        self.condition = condition
        self.body = body
        self.line = line
    
    def __str__(self):
        return "While"

class DoWhile(ASTNode):
    def __init__(self, body, condition, line):
        self.body = body
        self.condition = condition
        self.line = line

    def __str__(self):
        return f"DoWhile (line {self.line})"


class Block(ASTNode):
    def __init__(self, statements, line):
        self.statements = statements
        self.line = line
    
    def __str__(self):
        return f"Block({len(self.statements)} statements)"

class BinaryOp(ASTNode):
    def __init__(self, left, op, right, line):
        self.left = left
        self.op = op
        self.right = right
        self.line = line
    
    def __str__(self):
        return f"BinaryOp({self.op})"

class UnaryOp(ASTNode):
    def __init__(self, op, operand, line):
        self.op = op
        self.operand = operand
        self.line = line
    
    def __str__(self):
        return f"UnaryOp({self.op})"

class Identifier(ASTNode):
    def __init__(self, name, line):
        self.name = name
        self.line = line
    
    def __str__(self):
        return f"Identifier({self.name})"

class Number(ASTNode):
    def __init__(self, value, line):
        self.value = value
        self.line = line
    
    def __str__(self):
        return f"Number({self.value})"

class String(ASTNode):
    def __init__(self, value, line):
        self.value = value
        self.line = line
    
    def __str__(self):
        return f"String({self.value})"

class Boolean(ASTNode):
    def __init__(self, value, line):
        self.value = value
        self.line = line
    
    def __str__(self):
        return f"Boolean({self.value})"

class TernaryOp(ASTNode):
    def __init__(self, condition, true_expr, false_expr, line):
        self.condition = condition
        self.true_expr = true_expr
        self.false_expr = false_expr
        self.line = line
    
    def __str__(self):
        return "TernaryOp(?:)"

class ArrayAccess(ASTNode):
    def __init__(self, array, index, line):
        self.array = array
        self.index = index
        self.line = line
    
    def __str__(self):
        return f"ArrayAccess({self.array})"

class ArrayLiteral(ASTNode):
    def __init__(self, elements, line):
        self.elements = elements
        self.line = line
    
    def __str__(self):
        return f"ArrayLiteral({len(self.elements)} elements)"

class ListCall(ASTNode):
    def __init__(self, size, line):
        self.size = size
        self.line = line
    
    def __str__(self):
        return f"ListCall({self.size})"


def print_ast_tree(ast_node, title="Abstract Syntax Tree"):
    """Print AST in a tree format"""
    if ast_node is None:
        print(f"{title}: None")
        return
    
    print(f"\n{title}:")
    print("=" * len(title))
    
    def print_node(node, indent=0, prefix="", is_last=True):
        """Recursively print AST nodes"""
        # Current node
        connector = "└── " if is_last else "├── "
        node_info = str(node)
        
        # Add specific information for some nodes
        if hasattr(node, 'name') and node.name:
            node_info += f" '{node.name}'"
        elif hasattr(node, 'value') and node.value is not None:
            node_info += f" = {node.value}"
        elif hasattr(node, 'op') and node.op:
            node_info += f" '{node.op}'"
        
        print(" " * indent + connector + node_info)
        
        # Get children
        children = []
        for attr_name, attr_value in node.__dict__.items():
            if attr_name.startswith('_') or attr_name == 'line':
                continue
            
            if isinstance(attr_value, ASTNode):
                children.append((attr_name, attr_value))
            elif isinstance(attr_value, list) and attr_value:
                for i, item in enumerate(attr_value):
                    if isinstance(item, ASTNode):
                        children.append((f"{attr_name}[{i}]", item))
        
        # Print children
        for i, (child_name, child_node) in enumerate(children):
            is_last_child = i == len(children) - 1
            child_prefix = "    " if is_last else "│   "
            child_indent = indent + 4
            
            # Print attribute name
            attr_connector = "└── " if is_last_child else "├── "
            print(" " * indent + child_prefix + attr_connector + f"{child_name}:")
            
            # Print the child node
            print_node(child_node, child_indent + 4, child_prefix + ("    " if is_last_child else "│   "), True)
    
    print_node(ast_node)
    print()