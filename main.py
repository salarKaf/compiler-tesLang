# from Lexer.lexer import print_tokens

# if __name__ == '__main__':
#     with open("./tests/test_input.tes", "r") as f:
#         code = f.read()
#     print_tokens(code)

# main.py
# import ply.lex as lex
# import Lexer.tokens as tokens
# from Parser.parser import Parser
# from SemanticAnalyzer.semantic_analyzer import SemanticAnalyzer

# def compile_teslang(filename):
#     """Main compiler function"""
    
#     # Read input file
#     try:
#         with open(filename, "r", encoding='utf-8') as f:
#             code = f.read()
#     except FileNotFoundError:
#         print(f"Error: File '{filename}' not found")
#         return
#     except Exception as e:
#         print(f"Error reading file: {e}")
#         return

#     print("=== TesLang Compiler - Phase 2 ===")
#     print(f"Compiling: {filename}\n")

#     # Phase 1: Lexical Analysis
#     print("Phase 1: Lexical Analysis")
#     lexer = lex.lex(module=tokens)
#     lexer.input(code)
    
#     # Get all tokens
#     token_list = []
#     try:
#         while True:
#             tok = lexer.token()
#             if not tok:
#                 break
#             token_list.append(tok)
#     except Exception as e:
#         print(f"Lexical error: {e}")
#         return

#     print(f"Lexical analysis completed. Found {len(token_list)} tokens.\n")

#     # Phase 2: Syntax Analysis
#     print("Phase 2: Syntax Analysis")
#     parser = Parser(token_list, code)
#     ast = parser.parse()

#     # Check for parsing errors
#     if parser.errors:
#         print("Syntax Errors Found:")
#         for error in parser.errors:
#             print(f"  Line {error.line}, Column {error.column}: {error.message}")
#         print()
#     else:
#         print("Syntax analysis completed successfully.\n")

#     # Phase 3: Semantic Analysis
#     if ast and not parser.errors:
#         print("Phase 3: Semantic Analysis")
#         analyzer = SemanticAnalyzer()
#         analyzer.analyze(ast)

#         if analyzer.errors:
#             print("Semantic Errors Found:")
#             for error in analyzer.errors:
#                 print(f"Error:")
#                 print(f"function '{analyzer.current_function.name if analyzer.current_function else 'unknown'}': {error.message}")
#         else:
#             print("Semantic analysis completed successfully.")
#             print("Program is semantically correct!")

#     elif parser.errors:
#         print("Skipping semantic analysis due to syntax errors.")

# def main():
#     """Main entry point"""
#     import sys
    
#     if len(sys.argv) != 2:
#         print("Usage: python main.py <teslang_file>")
#         print("Example: python main.py test.tes")
#         return
    
#     filename = sys.argv[1]
#     compile_teslang(filename)

# if __name__ == "__main__":
#     main()




# main.py
# import sys
# import os
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# from Lexer.lexer import lexer
# from parser import parse_code
# from semantic_analyzer import SemanticAnalyzer

# def main():
#     if len(sys.argv) != 2:
#         print("Usage: python main.py <filename.tsl>")
#         sys.exit(1)
    
#     filename = sys.argv[1]
    
#     try:
#         with open(filename, 'r', encoding='utf-8') as file:
#             code = file.read()
#     except FileNotFoundError:
#         print(f"Error: File '{filename}' not found.")
#         sys.exit(1)
#     except Exception as e:
#         print(f"Error reading file: {e}")
#         sys.exit(1)
    
#     # Lexical Analysis
#     print("=== Lexical Analysis ===")
#     lexer.input(code)
#     tokens_list = []
#     while True:
#         tok = lexer.token()
#         if not tok:
#             break
#         tokens_list.append(tok)
    
#     print(f"{'Line':>6} | {'Column':>7} | {'Token':<20} | Value")
#     print('-' * 80)
    
#     def find_column(code, token):
#         line_start = code.rfind('\n', 0, token.lexpos) + 1
#         return (token.lexpos - line_start) + 1
    
#     for tok in tokens_list:
#         print(f"{tok.lineno:>6} | {find_column(code, tok):>7} | {tok.type:<20} | {tok.value}")
    
#     print("\n=== Syntax Analysis ===")
    
#     # Parse the code
#     ast = parse_code(code)
    
#     if ast is None:
#         print("Parsing failed.")
#         sys.exit(1)
    
#     print("Parsing successful!")
    
#     # Semantic Analysis
#     print("\n=== Semantic Analysis ===")
#     analyzer = SemanticAnalyzer()
#     errors = analyzer.analyze(ast)
    
#     if errors:
#         print("Semantic errors found:")
#         for error in errors:
#             print(f"Error: {error}")
#     else:
#         print("No semantic errors found.")
    
#     # Print AST structure (optional)
#     print("\n=== AST Structure ===")
#     print_ast(ast)

# def print_ast(node, indent=0):
#     """Pretty print the AST"""
#     if node is None:
#         return
    
#     spaces = "  " * indent
#     node_type = type(node).__name__
#     print(f"{spaces}{node_type}", end="")
    
#     if hasattr(node, 'name'):
#         print(f" (name: {node.name})", end="")
#     if hasattr(node, 'value') and not hasattr(node, 'name'):
#         print(f" (value: {node.value})", end="")
#     if hasattr(node, 'op'):
#         print(f" (op: {node.op})", end="")
#     if hasattr(node, 'type') and node_type in ['Parameter', 'VarDeclaration']:
#         print(f" (type: {node.type})", end="")
    
#     print()
    
#     # Visit children
#     if hasattr(node, 'functions'):
#         for func in node.functions:
#             print_ast(func, indent + 1)
#     elif hasattr(node, 'body') and hasattr(node.body, 'statements'):
#         for stmt in node.body.statements:
#             print_ast(stmt, indent + 1)
#     elif hasattr(node, 'statements'):
#         for stmt in node.statements:
#             print_ast(stmt, indent + 1)
#     elif hasattr(node, 'params'):
#         for param in node.params:
#             print_ast(param, indent + 1)
#         if hasattr(node, 'body'):
#             print_ast(node.body, indent + 1)
#     elif hasattr(node, 'condition'):
#         print_ast(node.condition, indent + 1)
#         if hasattr(node, 'then_stmt'):
#             print_ast(node.then_stmt, indent + 1)
#         if hasattr(node, 'else_stmt'):
#             print_ast(node.else_stmt, indent + 1)
#         if hasattr(node, 'body'):
#             print_ast(node.body, indent + 1)
#     elif hasattr(node, 'target') and hasattr(node, 'value'):
#         print_ast(node.target, indent + 1)
#         print_ast(node.value, indent + 1)
#     elif hasattr(node, 'left') and hasattr(node, 'right'):
#         print_ast(node.left, indent + 1)
#         print_ast(node.right, indent + 1)
#     elif hasattr(node, 'operand'):
#         print_ast(node.operand, indent + 1)
#     elif hasattr(node, 'array') and hasattr(node, 'index'):
#         print_ast(node.array, indent + 1)
#         print_ast(node.index, indent + 1)
#     elif hasattr(node, 'args'):
#         for arg in node.args:
#             print_ast(arg, indent + 1)
#     elif hasattr(node, 'value') and hasattr(node, 'value'):
#         if node.value is not None:
#             print_ast(node.value, indent + 1)

# if __name__ == "__main__":
#     main()




# main.py
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from Lexer import lexer
    from parser import compile_teslang
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all files are in the correct directory structure")
    sys.exit(1)

def main():
    # For testing, we'll use the hardcoded example first
    test_code = '''funk find(A as vector, n as int) <int>
{
k :: int;
j :: int;
for (i = 0 to length(A))
begin
if [[ n == k ]]
begin
return j;
end
j = x + 1;
end
return -1;
}
funk main() <null>
{
A :: int;
a :: int;
A = list(3);
A[0] = 1;
A[1] = 2;
A[2] = 3;
print(find(A, a));
print(find(A));
print(find(a, A));
return A;
}'''
    
    print("Compiling TesLang code...")
    print("=" * 50)
    
    # Compile the code
    errors = compile_teslang(test_code)
    
    if errors:
        print("Compilation errors found:")
        print("-" * 30)
        for error in errors:
            print(error)
    else:
        print("Compilation successful - no errors found")

def main_file():
    if len(sys.argv) != 2:
        print("Usage: python main.py <input_file>")
        print("Or run without arguments to test the example code")
        main()  # Run with example code
        return
    
    input_file = sys.argv[1]
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            code = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # Compile the code
    errors = compile_teslang(code)
    
    if errors:
        for error in errors:
            print(error)
    else:
        print("Compilation successful - no errors found")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main_file()
    else:
        main()