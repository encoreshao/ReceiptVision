#!/usr/bin/env python3
"""
ReceiptVision Setup Script
Automated setup for the ReceiptVision OCR application
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """Print the ReceiptVision banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║                    📄✨ ReceiptVision ✨📄                    ║
    ║                                                              ║
    ║            Advanced OCR for Receipts & Invoices             ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} is compatible")

def check_system_dependencies():
    """Check and install system dependencies"""
    print("\n🔧 Checking system dependencies...")

    system = platform.system().lower()

    # Check for Tesseract
    try:
        result = subprocess.run(['tesseract', '--version'],
                              capture_output=True, text=True, check=True)
        print("✅ Tesseract OCR is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Tesseract OCR not found!")
        print_tesseract_install_instructions(system)
        return False

    # Check for poppler (PDF processing)
    try:
        if system == 'windows':
            # On Windows, check for pdftoppm
            subprocess.run(['pdftoppm', '-h'],
                          capture_output=True, check=True)
        else:
            # On Unix-like systems
            subprocess.run(['pdftoppm', '-h'],
                          capture_output=True, check=True)
        print("✅ Poppler (PDF processing) is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Poppler (PDF processing) not found!")
        print_poppler_install_instructions(system)
        return False

    return True

def print_tesseract_install_instructions(system):
    """Print Tesseract installation instructions"""
    print("\n📋 Tesseract Installation Instructions:")

    if system == 'darwin':  # macOS
        print("   brew install tesseract")
    elif system == 'linux':
        print("   sudo apt-get install tesseract-ocr  # Ubuntu/Debian")
        print("   sudo yum install tesseract           # CentOS/RHEL")
    elif system == 'windows':
        print("   Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("   Add to system PATH after installation")

def print_poppler_install_instructions(system):
    """Print Poppler installation instructions"""
    print("\n📋 Poppler Installation Instructions:")

    if system == 'darwin':  # macOS
        print("   brew install poppler")
    elif system == 'linux':
        print("   sudo apt-get install poppler-utils  # Ubuntu/Debian")
        print("   sudo yum install poppler-utils       # CentOS/RHEL")
    elif system == 'windows':
        print("   Download from: https://blog.alivate.com.au/poppler-windows/")
        print("   Add to system PATH after installation")

def setup_virtual_environment():
    """Set up Python virtual environment"""
    print("\n🏗️  Setting up virtual environment...")

    venv_path = Path("venv")

    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True

    try:
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
        print("✅ Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def install_python_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")

    # Determine pip path
    system = platform.system().lower()
    if system == 'windows':
        pip_path = Path("venv/Scripts/pip")
    else:
        pip_path = Path("venv/bin/pip")

    if not pip_path.exists():
        print("❌ Virtual environment not found or not activated")
        return False

    try:
        # Upgrade pip first
        subprocess.run([str(pip_path), 'install', '--upgrade', 'pip'], check=True)

        # Install requirements
        subprocess.run([str(pip_path), 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Python dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment_file():
    """Set up environment file"""
    print("\n⚙️  Setting up environment configuration...")

    env_file = Path(".env")
    env_example = Path("env.example")

    if env_file.exists():
        print("✅ .env file already exists")
        return True

    if env_example.exists():
        try:
            # Copy example to .env
            with open(env_example, 'r') as src, open(env_file, 'w') as dst:
                dst.write(src.read())
            print("✅ Environment file created from template")
            print("⚠️  Please edit .env with your database credentials")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("❌ env.example file not found")
        return False

def check_postgresql():
    """Check PostgreSQL installation"""
    print("\n🗄️  Checking PostgreSQL...")

    try:
        result = subprocess.run(['psql', '--version'],
                              capture_output=True, text=True, check=True)
        print("✅ PostgreSQL is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PostgreSQL not found!")
        print_postgresql_install_instructions()
        return False

def print_postgresql_install_instructions():
    """Print PostgreSQL installation instructions"""
    system = platform.system().lower()
    print("\n📋 PostgreSQL Installation Instructions:")

    if system == 'darwin':  # macOS
        print("   brew install postgresql")
        print("   brew services start postgresql")
    elif system == 'linux':
        print("   sudo apt-get install postgresql postgresql-contrib  # Ubuntu/Debian")
        print("   sudo systemctl start postgresql")
    elif system == 'windows':
        print("   Download from: https://www.postgresql.org/download/windows/")

def create_database():
    """Create the database"""
    print("\n🗃️  Setting up database...")

    try:
        # Try to create database
        subprocess.run(['createdb', 'receiptvision'],
                      capture_output=True, check=True)
        print("✅ Database 'receiptvision' created")
    except subprocess.CalledProcessError:
        print("⚠️  Database might already exist or PostgreSQL not running")

    return True

def initialize_database():
    """Initialize the database with tables"""
    print("\n🏗️  Initializing database tables...")

    try:
        # Determine python path in venv
        system = platform.system().lower()
        if system == 'windows':
            python_path = Path("venv/Scripts/python")
        else:
            python_path = Path("venv/bin/python")

        subprocess.run([str(python_path), 'migrations/init_db.py'], check=True)
        print("✅ Database tables initialized")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to initialize database: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print("\n🎉 Setup Complete!")
    print("\n📋 Next Steps:")
    print("1. Edit .env file with your database credentials")
    print("2. Activate virtual environment:")

    system = platform.system().lower()
    if system == 'windows':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")

    print("3. Start the application:")
    print("   python app.py")
    print("4. Open your browser to: http://localhost:5000")
    print("\n✨ Happy receipt processing! ✨")

def main():
    """Main setup function"""
    print_banner()

    # Check Python version
    check_python_version()

    # Check system dependencies
    if not check_system_dependencies():
        print("\n❌ Please install missing system dependencies and run setup again")
        sys.exit(1)

    # Setup virtual environment
    if not setup_virtual_environment():
        sys.exit(1)

    # Install Python dependencies
    if not install_python_dependencies():
        sys.exit(1)

    # Setup environment file
    if not setup_environment_file():
        sys.exit(1)

    # Check PostgreSQL
    if not check_postgresql():
        print("\n⚠️  Please install PostgreSQL and run setup again")
        print("   You can continue without it, but database features won't work")
    else:
        # Create and initialize database
        create_database()
        initialize_database()

    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
