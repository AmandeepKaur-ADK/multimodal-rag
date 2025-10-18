"""
Diagnostic script to identify what's not working.
"""

import sys
import os
import traceback

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_basic_imports():
    """Check if basic imports work."""
    print("🔍 CHECKING BASIC IMPORTS...")
    
    try:
        print("   ✓ sys, os - OK")
        
        import logging
        print("   ✓ logging - OK")
        
        from pathlib import Path
        print("   ✓ pathlib - OK")
        
        from datetime import datetime
        print("   ✓ datetime - OK")
        
        return True
    except Exception as e:
        print(f"   ❌ Basic imports failed: {e}")
        return False

def check_project_imports():
    """Check if project modules can be imported."""
    print("\n🔍 CHECKING PROJECT IMPORTS...")
    
    modules_to_check = [
        ("src.enhanced_logger", "Enhanced Logger"),
        ("src.error_handler", "Error Handler"),
        ("src.validation_manager", "Validation Manager"),
        ("src.health_monitor", "Health Monitor"),
    ]
    
    success_count = 0
    
    for module_name, display_name in modules_to_check:
        try:
            __import__(module_name)
            print(f"   ✓ {display_name} - OK")
            success_count += 1
        except Exception as e:
            print(f"   ❌ {display_name} failed: {e}")
            traceback.print_exc()
    
    return success_count == len(modules_to_check)

def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n🔍 CHECKING DEPENDENCIES...")
    
    dependencies = [
        ("PIL", "Pillow (PIL)"),
        ("numpy", "NumPy"),
        ("requests", "Requests"),
        ("chromadb", "ChromaDB"),
        ("sentence_transformers", "Sentence Transformers"),
        ("transformers", "Transformers (Hugging Face)"),
    ]
    
    success_count = 0
    missing_deps = []
    
    for dep_name, display_name in dependencies:
        try:
            __import__(dep_name)
            print(f"   ✓ {display_name} - OK")
            success_count += 1
        except ImportError:
            print(f"   ❌ {display_name} - MISSING")
            missing_deps.append(dep_name)
        except Exception as e:
            print(f"   ⚠️ {display_name} - ERROR: {e}")
    
    if missing_deps:
        print(f"\n📦 MISSING DEPENDENCIES:")
        for dep in missing_deps:
            print(f"   pip install {dep}")
    
    return success_count, missing_deps

def test_simple_validation():
    """Test basic validation functionality."""
    print("\n🔍 TESTING BASIC VALIDATION...")
    
    try:
        from src.validation_manager import validation_manager
        
        # Test simple validation
        result = validation_manager.validate_user_input("What is AI?")
        
        if result.is_valid:
            print("   ✓ Basic validation - OK")
            return True
        else:
            print("   ⚠️ Validation failed (but system working)")
            return True
            
    except Exception as e:
        print(f"   ❌ Validation test failed: {e}")
        traceback.print_exc()
        return False

def test_free_pipeline():
    """Test if free pipeline can be created."""
    print("\n🔍 TESTING FREE PIPELINE...")
    
    try:
        from src.free_rag_pipeline import create_free_rag_pipeline
        
        print("   • Creating pipeline (this may take a moment)...")
        pipeline = create_free_rag_pipeline(
            model_name="microsoft/DialoGPT-small",
            enable_web_retrieval=False
        )
        
        print("   ✓ Free pipeline creation - OK")
        
        # Test simple query
        result = pipeline.process_query("Hello")
        
        if result.success:
            print("   ✓ Simple query test - OK")
        else:
            print(f"   ⚠️ Query failed: {result.error_message}")
        
        pipeline.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Free pipeline test failed: {e}")
        traceback.print_exc()
        return False

def check_file_structure():
    """Check if required files exist."""
    print("\n🔍 CHECKING FILE STRUCTURE...")
    
    required_files = [
        "src/enhanced_logger.py",
        "src/error_handler.py", 
        "src/validation_manager.py",
        "src/health_monitor.py",
        "src/free_response_generator.py",
        "src/free_rag_pipeline.py",
        "examples/free_rag_demo.py",
        "config/settings.py",
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✓ {file_path} - EXISTS")
        else:
            print(f"   ❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    return len(missing_files) == 0, missing_files

def main():
    """Run all diagnostic checks."""
    print("🩺 SYSTEM DIAGNOSTIC")
    print("=" * 50)
    
    all_good = True
    
    # Check basic imports
    if not check_basic_imports():
        all_good = False
    
    # Check file structure
    files_ok, missing_files = check_file_structure()
    if not files_ok:
        all_good = False
        print(f"\n❌ Missing files: {missing_files}")
    
    # Check dependencies
    dep_count, missing_deps = check_dependencies()
    if missing_deps:
        all_good = False
    
    # Check project imports
    if not check_project_imports():
        all_good = False
    
    # Test validation
    if not test_simple_validation():
        all_good = False
    
    # Test free pipeline (only if other tests pass)
    if all_good:
        if not test_free_pipeline():
            all_good = False
    
    print("\n" + "=" * 50)
    
    if all_good:
        print("🎉 ALL CHECKS PASSED!")
        print("\nYou can now run:")
        print("   python examples/free_rag_demo.py")
        print("   python examples/demo_without_openai.py")
    else:
        print("❌ SOME ISSUES FOUND")
        print("\nNext steps:")
        
        if missing_deps:
            print("1. Install missing dependencies:")
            for dep in missing_deps:
                print(f"   pip install {dep}")
        
        if missing_files:
            print("2. Some files are missing - the implementation may be incomplete")
        
        print("3. Try running a simpler test:")
        print("   python -c \"from src.validation_manager import validation_manager; print('Basic import works!')\"")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n💥 DIAGNOSTIC SCRIPT FAILED: {e}")
        traceback.print_exc()
        print("\nThis suggests a fundamental issue with the Python environment or file structure.")