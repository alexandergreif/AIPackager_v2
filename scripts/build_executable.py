#!/usr/bin/env python3
"""Build script for creating a standalone executable using shiv."""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> None:
    """Run a command and handle errors."""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        sys.exit(1)


def main():
    """Main build function."""
    print("🚀 Building PSADT AI Agent executable...")

    # Get project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Create dist directory
    dist_dir = project_root / "dist"
    dist_dir.mkdir(exist_ok=True)

    # Define output executable name
    output_file = dist_dir / "psadt-agent.pyz"

    # Clean up previous build
    if output_file.exists():
        print(f"🧹 Cleaning up previous build: {output_file}")
        output_file.unlink()

    # Install dev dependencies (including shiv)
    run_command(
        ["pip", "install", "-r", "requirements-dev.txt"],
        "Installing development dependencies",
    )

    # Create entry point script
    entry_point = """
import sys
import os
from pathlib import Path

# Add the source directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up environment
os.environ.setdefault("FLASK_APP", "ai_psadt_agent") # Changed src.ai_psadt_agent

if __name__ == "__main__":
    from flask import Flask
    from ai_psadt_agent import create_app # Changed src.ai_psadt_agent

    app = create_app()

    # Get port from environment or use default
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"🚀 Starting PSADT AI Agent on {host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"📊 Metrics: http://{host}:{port}/metrics")
    print(f"💚 Health Check: http://{host}:{port}/health")

    app.run(host=host, port=port, debug=False)
"""

    # Write entry point to temporary file
    entry_point_file = project_root / "__main__.py"
    entry_point_file.write_text(entry_point)

    try:
        # Build the executable with shiv
        shiv_cmd = [
            "python",
            "-m",
            "shiv",
            "--site-packages",
            str(project_root / ".venv" / "lib" / "python3.12" / "site-packages"),
            "--compressed",
            "--output-file",
            str(output_file),
            "--entry-point",
            "__main__:main",
            "--python",
            "/usr/bin/env python3",
            ".",
        ]

        run_command(shiv_cmd, "Building executable with shiv")

        # Make executable
        if sys.platform != "win32":
            os.chmod(output_file, 0o755)

        print(f"✅ Executable built successfully: {output_file}")
        print(f"📏 Size: {output_file.stat().st_size / (1024 * 1024):.1f} MB")

        # Create Windows batch script
        batch_script = dist_dir / "psadt-agent.bat"
        batch_content = f"""@echo off
REM PSADT AI Agent - Windows Batch Script
echo Starting PSADT AI Agent...
python "{output_file.name}" %*
"""
        batch_script.write_text(batch_content)

        print(f"📋 Windows batch script created: {batch_script}")

        # Test the executable
        print("🧪 Testing executable...")
        test_cmd = ["python", str(output_file), "--help"]
        try:
            subprocess.run(test_cmd, check=True, capture_output=True, timeout=10)
            print("✅ Executable test passed!")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            print("⚠️  Executable test failed, but build completed")

        print(f"""
🎉 Build completed successfully!

📦 Executable: {output_file}
📋 Windows script: {batch_script}

🚀 Usage:
  python {output_file.name}

  Or on Windows:
  {batch_script.name}

🔧 Environment variables:
  API_KEY=your-api-key
  OPENAI_API_KEY=your-openai-key
  PORT=5000
  HOST=0.0.0.0
  LOG_FORMAT=structured
""")

    finally:
        # Clean up temporary entry point
        if entry_point_file.exists():
            entry_point_file.unlink()


if __name__ == "__main__":
    main()
