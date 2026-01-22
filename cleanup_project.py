#!/usr/bin/env python
"""
Project cleanup script - Remove unnecessary files and reorganize
"""
import os
import shutil
from pathlib import Path

# Project root
ROOT = Path(__file__).parent

def remove_pycache():
    """Remove all __pycache__ directories"""
    print("🧹 Removing __pycache__ directories...")
    count = 0
    for pycache in ROOT.rglob("__pycache__"):
        if pycache.is_dir():
            shutil.rmtree(pycache)
            count += 1
            print(f"   ✓ Removed: {pycache.relative_to(ROOT)}")
    print(f"   Removed {count} __pycache__ directories\n")

def remove_pyc_files():
    """Remove all .pyc and .pyo files"""
    print("🧹 Removing .pyc and .pyo files...")
    count = 0
    for pattern in ["*.pyc", "*.pyo"]:
        for file in ROOT.rglob(pattern):
            if file.is_file():
                file.unlink()
                count += 1
                print(f"   ✓ Removed: {file.relative_to(ROOT)}")
    print(f"   Removed {count} compiled Python files\n")

def clean_logs():
    """Clean old log files (keep structure)"""
    print("🧹 Cleaning log files...")
    logs_dir = ROOT / "logs"
    if logs_dir.exists():
        count = 0
        for log_file in logs_dir.glob("*.log"):
            if log_file.name != ".gitkeep":
                # Truncate log files instead of deleting them
                with open(log_file, 'w') as f:
                    f.write("")
                count += 1
                print(f"   ✓ Cleared: {log_file.name}")
        print(f"   Cleared {count} log files\n")

def remove_duplicate_compile_scripts():
    """Remove compile_translations.py (keep compile_po.py)"""
    print("🧹 Removing duplicate compilation scripts...")
    old_script = ROOT / "compile_translations.py"
    if old_script.exists():
        old_script.unlink()
        print(f"   ✓ Removed: compile_translations.py (keeping compile_po.py)\n")
    else:
        print("   No duplicate scripts found\n")

def organize_root_files():
    """Ensure scripts directory exists and is organized"""
    print("📁 Organizing root directory...")
    scripts_dir = ROOT / "scripts"
    if not scripts_dir.exists():
        scripts_dir.mkdir()
        print(f"   ✓ Created: scripts/")
    
    # Files that could be moved to scripts (optional - commented out for safety)
    # script_files = ["compile_po.py", "translate_po.py"]
    # for script in script_files:
    #     src = ROOT / script
    #     dst = scripts_dir / script
    #     if src.exists() and not dst.exists():
    #         shutil.move(str(src), str(dst))
    #         print(f"   ✓ Moved: {script} → scripts/{script}")
    
    print("   Root directory organized\n")

def check_gitignore():
    """Verify .gitignore is properly configured"""
    print("✅ Checking .gitignore configuration...")
    gitignore = ROOT / ".gitignore"
    
    required_entries = [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "*.log",
        ".env",
        "venv",
        "db.sqlite3",
        "staticfiles",
        "media",
        "backups"
    ]
    
    if gitignore.exists():
        content = gitignore.read_text()
        missing = [entry for entry in required_entries if entry not in content]
        if missing:
            print(f"   ⚠️  Missing entries in .gitignore: {', '.join(missing)}")
        else:
            print("   ✓ .gitignore properly configured")
    else:
        print("   ⚠️  .gitignore not found!")
    print()

def display_summary():
    """Display project structure summary"""
    print("📊 Project Structure Summary:")
    print("=" * 60)
    
    # Count directories and files
    dirs = {
        "Apps": len([d for d in ROOT.iterdir() if d.is_dir() and not d.name.startswith('.') and d.name not in ['venv', 'static', 'templates', 'locale', 'logs', 'backups', 'docs', '__pycache__']]),
        "Templates": len(list((ROOT / "templates").rglob("*.html"))) if (ROOT / "templates").exists() else 0,
        "Static files": len(list((ROOT / "static").rglob("*.*"))) if (ROOT / "static").exists() else 0,
        "Documentation": len(list((ROOT / "docs").glob("*.md"))) if (ROOT / "docs").exists() else 0,
        "Translations": len(list((ROOT / "locale").rglob("*.po"))) if (ROOT / "locale").exists() else 0,
    }
    
    for name, count in dirs.items():
        print(f"   {name:20} {count:4} items")
    
    print("=" * 60)
    print()

def main():
    """Run all cleanup tasks"""
    print("🚀 Starting project cleanup...")
    print("=" * 60)
    print()
    
    # Run cleanup tasks
    remove_pycache()
    remove_pyc_files()
    clean_logs()
    remove_duplicate_compile_scripts()
    organize_root_files()
    check_gitignore()
    display_summary()
    
    print("✅ Cleanup completed successfully!")
    print()
    print("📝 Recommendations:")
    print("   1. Run 'git status' to see what was cleaned")
    print("   2. Database backups are kept in backups/ directory")
    print("   3. Documentation is organized in docs/ directory")
    print("   4. Run this script periodically to keep project clean")
    print()

if __name__ == "__main__":
    main()
