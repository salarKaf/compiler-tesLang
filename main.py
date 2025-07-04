# main.py
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from Lexer import lexer
    from Parser.parser import compile_teslang, parse_code
    from Parser.ast_nodes import print_ast_tree
    from IR.codegen import compile_teslang_with_codegen
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all files are in the correct directory structure")
    sys.exit(1)

def main():
    # Example code from the problem description
    test_code = '''funk add(a as int, b as int) <int>
{
    result :: int;
    result = a + b;
    return result;
}

funk main() <null>
{
    a :: int;
    b :: int;
   
    a = scan();
    b = scan();
   
    print(add(a, b));
    return;
}'''
   
    print("TesLang Compiler - Complete Analysis")
    print("=" * 50)
   
    # Step 0: Parse and show AST
    print("Step 0: Parsing and AST Generation...")
    ast = parse_code(test_code)
    
    if ast:
        print("✓ Parsing successful")
        print_ast_tree(ast, "Abstract Syntax Tree (AST)")
        
        # Optional: Save AST to file
        try:
            with open('ast_output.txt', 'w', encoding='utf-8') as f:
                f.write("TesLang AST Output\n")
                f.write("=" * 50 + "\n\n")
                
                def write_ast_to_file(node, indent=0, prefix="", is_last=True):
                    connector = "└── " if is_last else "├── "
                    node_info = str(node)
                    
                    if hasattr(node, 'name') and node.name:
                        node_info += f" '{node.name}'"
                    elif hasattr(node, 'value') and node.value is not None:
                        node_info += f" = {node.value}"
                    elif hasattr(node, 'op') and node.op:
                        node_info += f" '{node.op}'"
                    
                    f.write(" " * indent + connector + node_info + "\n")
                    
                    children = []
                    for attr_name, attr_value in node.__dict__.items():
                        if attr_name.startswith('_') or attr_name == 'line':
                            continue
                        
                        if isinstance(attr_value, type(node)) or hasattr(attr_value, '__dict__'):
                            children.append((attr_name, attr_value))
                        elif isinstance(attr_value, list) and attr_value:
                            for i, item in enumerate(attr_value):
                                if hasattr(item, '__dict__'):
                                    children.append((f"{attr_name}[{i}]", item))
                    
                    for i, (child_name, child_node) in enumerate(children):
                        is_last_child = i == len(children) - 1
                        child_prefix = "    " if is_last else "│   "
                        child_indent = indent + 4
                        
                        attr_connector = "└── " if is_last_child else "├── "
                        f.write(" " * indent + child_prefix + attr_connector + f"{child_name}:\n")
                        write_ast_to_file(child_node, child_indent + 4, child_prefix + ("    " if is_last_child else "│   "), True)
                
                write_ast_to_file(ast)
            print("✓ AST saved to ast_output.txt")
        except Exception as e:
            print(f"⚠ Could not save AST to file: {e}")
    else:
        print("✗ Parsing failed")
        return
   
    # Step 1 & 2: Semantic Analysis
    print("\nStep 1 & 2: Semantic Analysis...")
    print("-" * 30)
    errors = compile_teslang(test_code)
   
    if errors:
        print("Compilation errors found:")
        print("-" * 30)
        for error in errors:
            print(error)
        return
    else:
        print("✓ Semantic analysis successful")
   
    # Step 3: Generate intermediate code
    print("\nStep 3: Generating Intermediate Code...")
    print("-" * 30)
   
    intermediate_code, codegen_errors = compile_teslang_with_codegen(test_code)
   
    if codegen_errors:
        print("Code generation errors:")
        for error in codegen_errors:
            print(error)
    else:
        print("✓ Code generation successful")
        print("\nGenerated Intermediate Code:")
        print("=" * 50)
        print(intermediate_code)
        print("=" * 50)

def main_file():
    """Handle file input"""
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
   
    print(f"TesLang Compiler - Processing: {input_file}")
    print("=" * 50)
   
    # Step 0: Parse and show AST
    print("Step 0: Parsing and AST Generation...")
    ast = parse_code(code)
    
    if ast:
        print("✓ Parsing successful")
        print_ast_tree(ast, "Abstract Syntax Tree (AST)")
        
        # Save AST to file
        ast_output_file = input_file.replace('.tl', '_ast.txt').replace('.txt', '_ast.txt')
        if ast_output_file == input_file:
            ast_output_file = input_file + '_ast.txt'
        
        try:
            with open(ast_output_file, 'w', encoding='utf-8') as f:
                f.write(f"TesLang AST Output for: {input_file}\n")
                f.write("=" * 50 + "\n\n")
                
                def write_ast_to_file(node, indent=0, prefix="", is_last=True):
                    connector = "└── " if is_last else "├── "
                    node_info = str(node)
                    
                    if hasattr(node, 'name') and node.name:
                        node_info += f" '{node.name}'"
                    elif hasattr(node, 'value') and node.value is not None:
                        node_info += f" = {node.value}"
                    elif hasattr(node, 'op') and node.op:
                        node_info += f" '{node.op}'"
                    
                    f.write(" " * indent + connector + node_info + "\n")
                    
                    children = []
                    for attr_name, attr_value in node.__dict__.items():
                        if attr_name.startswith('_') or attr_name == 'line':
                            continue
                        
                        if hasattr(attr_value, '__dict__'):
                            children.append((attr_name, attr_value))
                        elif isinstance(attr_value, list) and attr_value:
                            for i, item in enumerate(attr_value):
                                if hasattr(item, '__dict__'):
                                    children.append((f"{attr_name}[{i}]", item))
                    
                    for i, (child_name, child_node) in enumerate(children):
                        is_last_child = i == len(children) - 1
                        child_prefix = "    " if is_last else "│   "
                        child_indent = indent + 4
                        
                        attr_connector = "└── " if is_last_child else "├── "
                        f.write(" " * indent + child_prefix + attr_connector + f"{child_name}:\n")
                        write_ast_to_file(child_node, child_indent + 4, child_prefix + ("    " if is_last_child else "│   "), True)
                
                write_ast_to_file(ast)
            print(f"✓ AST saved to {ast_output_file}")
        except Exception as e:
            print(f"⚠ Could not save AST to file: {e}")
    else:
        print("✗ Parsing failed")
        return
   
    # Step 1 & 2: Semantic Analysis
    print("\nStep 1 & 2: Semantic Analysis...")
    print("-" * 30)
    errors = compile_teslang(code)
   
    if errors:
        print("Compilation errors found:")
        print("-" * 30)
        for error in errors:
            print(error)
        return
    else:
        print("✓ Semantic analysis successful")
   
    # Step 3: Generate intermediate code
    print("\nStep 3: Generating Intermediate Code...")
    print("-" * 30)
   
    intermediate_code, codegen_errors = compile_teslang_with_codegen(code)
   
    if codegen_errors:
        print("Code generation errors:")
        for error in codegen_errors:
            print(error)
    else:
        print("✓ Code generation successful")
        print("\nGenerated Intermediate Code:")
        print("=" * 50)
        print(intermediate_code)
        print("=" * 50)
       
        # Save intermediate code to output file
        output_file = input_file.replace('.tl', '.tsm').replace('.txt', '.tsm')
        if output_file == input_file:
            output_file = input_file + '.tsm'
       
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(intermediate_code)
            print(f"\n✓ Intermediate code saved to: {output_file}")
        except Exception as e:
            print(f"\n⚠ Could not save output file: {e}")

def interactive_mode():
    """Interactive mode for testing code snippets"""
    print("TesLang Compiler - Interactive Mode")
    print("=" * 40)
    print("Enter 'quit' to exit, 'help' for help")
    print()
    
    while True:
        try:
            print("Enter TesLang code (end with empty line):")
            lines = []
            while True:
                line = input()
                if line.strip() == "":
                    break
                lines.append(line)
            
            if not lines:
                continue
                
            code = '\n'.join(lines)
            
            if code.strip().lower() == 'quit':
                break
            elif code.strip().lower() == 'help':
                print("Commands:")
                print("  quit - Exit interactive mode")
                print("  help - Show this help")
                print("  Enter TesLang code and press Enter twice to compile")
                print()
                continue
            
            print("\n" + "="*40)
            print("Analyzing code...")
            print("-" * 20)
            
            # Parse and show AST
            ast = parse_code(code)
            if ast:
                print("✓ Parsing successful")
                print_ast_tree(ast, "AST")
                
                # Semantic analysis
                errors = compile_teslang(code)
                if errors:
                    print("Compilation errors:")
                    for error in errors:
                        print(f"  {error}")
                else:
                    print("✓ Semantic analysis successful")
                    
                    # Code generation
                    intermediate_code, codegen_errors = compile_teslang_with_codegen(code)
                    if codegen_errors:
                        print("Code generation errors:")
                        for error in codegen_errors:
                            print(f"  {error}")
                    else:
                        print("✓ Code generation successful")
                        print("\nGenerated code:")
                        print(intermediate_code)
            else:
                print("✗ Parsing failed")
            
            print("="*40 + "\n")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except EOFError:
            print("\nExiting...")
            break

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '-i' or sys.argv[1] == '--interactive':
            interactive_mode()
        else:
            main_file()
    else:
        main()