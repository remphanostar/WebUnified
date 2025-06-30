# scripts/manage_venvs.py
import os
import sys
import subprocess
from pathlib import Path

# This script should be run from the PROJECT_ROOT directory
PROJECT_ROOT = Path.cwd()
WEBUI_ROOT = Path('/content')

# Configuration for each WebUI
TOOL_CONFIG = {
    "A1111": {
        "repo": "https://github.com/AUTOMATIC1111/stable-diffusion-webui.git",
        "venv_py": "python3.10",
        "reqs_file": "requirements_versions.txt",
        "post_install": [
            "pip install numpy==1.26.4",
            "pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu121",
            "pip install xformers==0.0.23.post1 --index-url https://download.pytorch.org/whl/cu121",
        ]
    },
    "Forge": {
        "repo": "https://github.com/lllyasviel/stable-diffusion-webui-forge.git",
        "venv_py": "python3.11",
        "reqs_file": "requirements_versions.txt",
        "post_install": [
            "pip install torch==2.3.1 torchvision==0.18.1 --index-url https://download.pytorch.org/whl/cu121",
            "pip install xformers"
        ]
    },
    # Add ComfyUI, etc. here later
}

def log_message(message):
    """Prints a formatted log message."""
    print(f"[VenvManager] {message}")

def run_command_with_live_output(command, cwd, venv_path=None):
    """
    Runs a command and streams its stdout/stderr to the console in real-time.
    Optionally activates a virtual environment for the command.
    """
    log_message(f"Executing: {command}")
    
    env = os.environ.copy()
    if venv_path:
        # Prepend the venv's bin directory to the PATH
        env['PATH'] = f"{venv_path / 'bin'}:{env['PATH']}"
        # Some tools might need VIRTUAL_ENV set
        env['VIRTUAL_ENV'] = str(venv_path)

    try:
        process = subprocess.Popen(
            command,
            shell=True,  # shell=True is often needed for activating venvs or complex commands
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1  # Line-buffered
        )

        # Read and print output line by line as it comes in
        for line in iter(process.stdout.readline, ''):
            # Print with an indent to show it's sub-process output
            print(f"  > {line.strip()}")
        
        # Wait for the process to complete and get the return code
        return_code = process.wait()
        
        if return_code != 0:
            log_message(f"❌ Command failed with exit code {return_code}.")
            return False
        
        return True

    except Exception as e:
        log_message(f"❌ An exception occurred while running command: {e}")
        return False

def setup_tool(tool_name, config):
    """Sets up a single tool with its own venv."""
    log_message(f"--- Setting up {tool_name} ---")
    tool_path = WEBUI_ROOT / tool_name
    venv_path = tool_path / 'venv'

    # 1. Clone repo
    if not tool_path.exists():
        log_message(f"Cloning {tool_name} repository...")
        if not run_command_with_live_output(f"git clone --depth 1 {config['repo']} {tool_path}", cwd=WEBUI_ROOT):
            log_message(f"❌ FAILED to clone {tool_name}.")
            return False
    else:
        log_message(f"{tool_name} directory already exists.")

    # 2. Create venv
    if not venv_path.exists():
        log_message(f"Creating virtual environment using {config['venv_py']}...")
        if not run_command_with_live_output(f"{config['venv_py']} -m venv {venv_path}", cwd=tool_path):
            log_message(f"❌ FAILED to create venv for {tool_name}. Is {config['venv_py']} installed?")
            return False
    else:
        log_message("Virtual environment already exists.")

    # 3. Install dependencies from requirements file
    log_message(f"Installing dependencies from {config['reqs_file']}...")
    venv_pip = venv_path / "bin" / "pip"
    if not run_command_with_live_output(f"{venv_pip} install -r {config['reqs_file']}", cwd=tool_path):
        log_message(f"❌ FAILED to install requirements for {tool_name}.")
        return False

    # 4. Run post-install commands for compatibility
    if "post_install" in config:
        log_message("Running post-install compatibility fixes...")
        for cmd in config['post_install']:
            # For pip commands, we need to specify the venv's pip
            full_cmd = cmd.replace("pip", str(venv_pip))
            if not run_command_with_live_output(full_cmd, cwd=tool_path, venv_path=venv_path):
                log_message(f"❌ FAILED to run post-install command: {cmd}")
                return False

    log_message(f"✅ {tool_name} setup complete!")
    return True

def main():
    # Setup all configured tools
    for tool_name, config in TOOL_CONFIG.items():
        setup_tool(tool_name, config)

if __name__ == "__main__":
    main()
