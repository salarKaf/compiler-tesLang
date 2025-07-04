import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from Lexer import lexer
    from Parser.parser import compile_teslang, parse_code, errors as parser_errors
    from Parser.ast_nodes import print_ast_tree
    from IR.codegen import compile_teslang_with_codegen
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all files are in the correct directory structure")
    sys.exit(1)

def main():
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
    
    # Step 1 & 2: Parse and perform semantic analysis
    print("Step 1 & 2: Parsing and Semantic Analysis...")
    errors = compile_teslang(code)
    
    if errors:
        print("Compilation errors found:")
        print("-" * 30)
        for error in errors:
            print(error)
        return
    else:
        print("✓ Parsing and semantic analysis successful")
        ast = parse_code(code)
        print_ast_tree(ast, "Abstract Syntax Tree (AST)")


    
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
        
        # Optionally save to output file
        output_file = input_file.replace('.tl', '.tsm').replace('.txt', '.tsm')
        if output_file == input_file:
            output_file = input_file + '.tsm'
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(intermediate_code)
            print(f"\n✓ Intermediate code saved to: {output_file}")
        except Exception as e:
            print(f"\n⚠ Could not save output file: {e}")

if __name__ == "__main__":
        main()
