"""
Test script to verify project structure.
This script checks if all necessary files and directories exist.
Works on both Windows and Linux/Mac.
"""
import os
import sys

def check_project_structure():
    """Check if all necessary files and directories exist."""
    
    # Get the current directory (should be project root)
    project_root = os.getcwd()
    
    print(f"📂 Checking project at: {project_root}")
    print()
    
    required_items = [
        ("file", "requirements.txt"),
        ("file", "README.md"),
        ("file", ".env"),
        ("file", ".env.example"),
        ("file", "run.py"),
        ("dir", "app"),
        ("file", "app/__init__.py"),
        ("file", "app/main.py"),
        ("file", "app/config.py"),
        ("dir", "app/models"),
        ("file", "app/models/__init__.py"),
        ("dir", "app/services"),
        ("file", "app/services/__init__.py"),
        ("dir", "app/routers"),
        ("file", "app/routers/__init__.py"),
        ("dir", "app/db"),
        ("file", "app/db/__init__.py"),
        ("dir", "app/utils"),
        ("file", "app/utils/__init__.py"),
        ("dir", "tests"),
        ("dir", "uploads"),
    ]
    
    print("🔍 Checking Project Structure...")
    print("=" * 70)
    
    all_good = True
    missing_items = []
    
    for item_type, item_path in required_items:
        # Handle both forward and backward slashes for cross-platform compatibility
        item_path_normalized = item_path.replace("/", os.sep)
        full_path = os.path.join(project_root, item_path_normalized)
        exists = os.path.exists(full_path)
        
        if item_type == "dir":
            correct_type = os.path.isdir(full_path) if exists else False
            icon = "📁"
        else:
            correct_type = os.path.isfile(full_path) if exists else False
            icon = "📄"
        
        if exists and correct_type:
            status = "✅"
        else:
            status = "❌"
            all_good = False
            missing_items.append((item_type, item_path))
        
        print(f"{status} {icon} {item_path}")
    
    print("=" * 70)
    print()
    
    if all_good:
        print("✅ Project structure is PERFECT!")
        print()
        print("📋 Next Steps:")
        print("=" * 70)
        print("1. Install dependencies:")
        print("   pip install -r requirements.txt")
        print()
        print("2. Configure your API keys in .env file:")
        print("   - Add your ANTHROPIC_API_KEY")
        print("   - Optionally add OPENAI_API_KEY")
        print()
        print("3. Make sure MongoDB is running (locally or use cloud)")
        print()
        print("4. Run the application:")
        print("   python run.py")
        print()
        print("5. Visit the API documentation:")
        print("   http://localhost:8000/docs")
        print("=" * 70)
        return 0
    else:
        print("❌ Some files or directories are missing!")
        print()
        print("Missing items:")
        print("-" * 70)
        for item_type, item_path in missing_items:
            if item_type == "dir":
                print(f"  📁 Directory: {item_path}")
            else:
                print(f"  📄 File: {item_path}")
        print("-" * 70)
        print()
        print("💡 To create missing directories and __init__.py files:")
        print()
        if os.name == 'nt':  # Windows
            print("Using PowerShell:")
            print('New-Item -ItemType Directory -Force -Path app\\models, app\\services, app\\routers, app\\db, app\\utils, tests, uploads')
            print('New-Item -ItemType File -Force -Path app\\models\\__init__.py, app\\services\\__init__.py, app\\routers\\__init__.py, app\\db\\__init__.py, app\\utils\\__init__.py')
        else:  # Linux/Mac
            print("Using terminal:")
            print('mkdir -p app/models app/services app/routers app/db app/utils tests uploads')
            print('touch app/models/__init__.py app/services/__init__.py app/routers/__init__.py app/db/__init__.py app/utils/__init__.py')
        print()
        return 1

if __name__ == "__main__":
    try:
        sys.exit(check_project_structure())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)