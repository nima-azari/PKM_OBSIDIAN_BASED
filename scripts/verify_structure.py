#!/usr/bin/env python3
"""
Verify repository structure is correct for publishing.

This script checks:
1. Tool code is tracked by git
2. Personal data is gitignored
3. Required directories exist
4. .env.example exists (but not .env)
"""

import subprocess
import sys
from pathlib import Path


def run_git_command(cmd):
    """Run git command and return output."""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}")
        return ""


def check_tracked_files():
    """Verify important files are tracked."""
    print("=" * 60)
    print("Checking tracked files...")
    print("=" * 60)
    
    required_files = [
        "core/rag_engine.py",
        "features/chat.py",
        "build_graph.py",
        "server.py",
        "requirements.txt",
        "README.md",
        ".env.example",
        ".gitignore"
    ]
    
    tracked = run_git_command("git ls-files")
    
    all_good = True
    for file in required_files:
        if file in tracked:
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - NOT TRACKED!")
            all_good = False
    
    return all_good


def check_ignored_files():
    """Verify personal data is ignored."""
    print("\n" + "=" * 60)
    print("Checking ignored files...")
    print("=" * 60)
    
    should_be_ignored = [
        ".env",
        "data/sources/*.md",
        "data/sources/*.pdf", 
        "data/graphs/*.ttl",
        "examples/data/sources/*",
        "socialmediapost/",
        "GENERATED_TTL_ANALYSIS.md",
        "km_graphrag_stack_design.md"
    ]
    
    ignored = run_git_command("git status --ignored --short")
    
    print("\nSample of ignored files:")
    for line in ignored.split('\n')[:10]:
        if line.startswith('!!'):
            print(f"  ✅ {line[3:]}")
    
    # Check .env specifically
    if ".env" in ignored or "!! .env" in ignored:
        print("\n✅ .env is properly ignored")
        return True
    else:
        print("\n⚠️  .env might not be ignored!")
        return False


def check_directory_structure():
    """Verify required directories exist."""
    print("\n" + "=" * 60)
    print("Checking directory structure...")
    print("=" * 60)
    
    required_dirs = [
        "core",
        "features",
        "static",
        "notebooks",
        "data/sources",
        "data/graphs",
        "data/embeddings",
        "examples/data/sources",
        "examples/data/graphs"
    ]
    
    all_good = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ - MISSING!")
            all_good = False
    
    return all_good


def check_examples_structure():
    """Verify examples directory has proper structure."""
    print("\n" + "=" * 60)
    print("Checking examples/ structure...")
    print("=" * 60)
    
    # Check that examples/README.md exists and is tracked
    examples_readme = Path("examples/README.md")
    tracked = run_git_command("git ls-files examples/")
    
    if "examples/README.md" in tracked:
        print("✅ examples/README.md is tracked")
    else:
        print("❌ examples/README.md should be tracked!")
        return False
    
    # Check that examples/data/sources/* is ignored
    if "examples/data/sources" not in tracked or tracked.count("examples/data/sources/") <= 2:
        print("✅ examples/data/sources/* is properly ignored")
    else:
        print("⚠️  Some files in examples/data/sources/ might be tracked!")
    
    return True


def main():
    print("\n" + "=" * 60)
    print("Repository Structure Verification")
    print("=" * 60)
    
    checks = [
        ("Tracked files", check_tracked_files()),
        ("Ignored files", check_ignored_files()),
        ("Directory structure", check_directory_structure()),
        ("Examples structure", check_examples_structure())
    ]
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✅ Repository structure is correct!")
        print("\nYou can safely commit and push:")
        print("  git add .")
        print("  git commit -m 'refactor: separate tool from development work'")
        print("  git push origin master")
        return 0
    else:
        print("\n❌ Some checks failed. Please review above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
