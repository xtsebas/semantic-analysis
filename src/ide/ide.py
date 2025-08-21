# -*- coding: utf-8 -*-
import streamlit as st
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

# Add project paths for imports
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))
sys.path.insert(0, str(repo_root / "program"))

from src.parser.parser import parse_file, tree_as_lisp
from src.semantic.semantic import SemanticVisitor, SemanticIssue


def load_file_content(file_path: str) -> Optional[str]:
    """Load content from a .cps file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None


def save_temp_file(content: str) -> str:
    """Save content to a temporary .cps file and return the path"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cps', delete=False, encoding='utf-8') as f:
        f.write(content)
        return f.name


def run_compilation(file_path: str) -> Tuple[bool, List[str], List[SemanticIssue], Optional[str]]:
    """
    Run compilation using the parser and semantic analyzer.
    Returns: (success, syntax_errors, semantic_errors, tree_output)
    """
    try:
        # Parse the file
        result = parse_file(file_path)
        
        # Check for syntax errors
        if result.issues:
            syntax_errors = [f"Line {e.line}, Col {e.column}: {e.message}" for e in result.issues]
            return False, syntax_errors, [], None
        
        # Run semantic analysis
        visitor = SemanticVisitor()
        _ = result.tree.accept(visitor)
        
        # Check for semantic errors
        if visitor.issues:
            return False, [], visitor.issues, None
        
        # Get tree representation
        tree_output = tree_as_lisp(result)
        return True, [], [], tree_output
        
    except Exception as e:
        return False, [f"Compilation error: {str(e)}"], [], None


def main():
    st.set_page_config(
        page_title="Compiscript IDE",
        page_icon="🔧",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("Compiscript IDE")
    st.markdown("*Integrated Development Environment for Compiscript Language*")
    
    # Initialize session state
    if 'file_content' not in st.session_state:
        st.session_state.file_content = ""
    if 'current_file' not in st.session_state:
        st.session_state.current_file = None
    if 'compilation_results' not in st.session_state:
        st.session_state.compilation_results = None
    
    # Sidebar for file operations
    with st.sidebar:
        st.header("File Operations")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a .cps file",
            type=['cps'],
            help="Upload a Compiscript source file"
        )
        
        if uploaded_file is not None:
            content = uploaded_file.read().decode('utf-8')
            st.session_state.file_content = content
            st.session_state.current_file = uploaded_file.name
            st.success(f"Loaded: {uploaded_file.name}")
        
        # Load example file
        example_file = repo_root / "program" / "program.cps"
        if st.button("Load Example Program"):
            if example_file.exists():
                content = load_file_content(str(example_file))
                if content:
                    st.session_state.file_content = content
                    st.session_state.current_file = "program.cps"
                    st.success("Loaded example program")
            else:
                st.error("Example file not found")
        
        # File info
        if st.session_state.current_file:
            st.info(f"**Current file:** {st.session_state.current_file}")
            st.info(f"**Lines:** {len(st.session_state.file_content.splitlines())}")
    
    # Main content area
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.header("Code Editor")
        
        # Code editor
        new_content = st.text_area(
            "Edit your Compiscript code:",
            value=st.session_state.file_content,
            height=400,
            help="Write or edit your Compiscript source code here"
        )
        
        # Update content if changed
        if new_content != st.session_state.file_content:
            st.session_state.file_content = new_content
        
        # Compilation button
        col_compile, col_clear = st.columns([2, 1])
        
        with col_compile:
            compile_clicked = st.button(
                "🔨 Compile & Analyze",
                type="primary",
                disabled=not st.session_state.file_content.strip(),
                help="Run syntax and semantic analysis"
            )
        
        with col_clear:
            if st.button("🗑️ Clear"):
                st.session_state.file_content = ""
                st.session_state.current_file = None
                st.session_state.compilation_results = None
                st.rerun()
    
    with col2:
        st.header("Analysis Results")
        
        # Run compilation when button is clicked
        if compile_clicked and st.session_state.file_content.strip():
            with st.spinner("Compiling..."):
                # Save content to temporary file
                temp_file = save_temp_file(st.session_state.file_content)
                
                try:
                    # Run compilation
                    success, syntax_errors, semantic_errors, tree_output = run_compilation(temp_file)
                    st.session_state.compilation_results = {
                        'success': success,
                        'syntax_errors': syntax_errors,
                        'semantic_errors': semantic_errors,
                        'tree_output': tree_output
                    }
                finally:
                    # Clean up temp file
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
        
        # Display compilation results
        if st.session_state.compilation_results:
            results = st.session_state.compilation_results
            
            if results['success']:
                st.success("✅ Compilation successful!")
                
                # Show syntax tree
                if results['tree_output']:
                    with st.expander("🌳 Syntax Tree", expanded=False):
                        st.code(results['tree_output'], language='lisp')
            
            else:
                st.error("❌ Compilation failed!")
                
                # Show syntax errors
                if results['syntax_errors']:
                    st.subheader("🔴 Syntax Errors")
                    for error in results['syntax_errors']:
                        st.error(error)
                
                # Show semantic errors
                if results['semantic_errors']:
                    st.subheader("🟡 Semantic Errors")
                    for error in results['semantic_errors']:
                        st.error(f"Line {error.line}, Col {error.column}: {error.message}")
        
        else:
            st.info("👆 Click 'Compile & Analyze' to see results")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "Compiscript IDE - Built with Streamlit & ANTLR4"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()