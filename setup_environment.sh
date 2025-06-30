#!/bin/bash
# Unified WebUI Environment Setup Script
# This script automates the complete setup of all WebUI tools

set -e  # Exit on any error

# Configuration
WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace}"
MODELS_DIR="${MODELS_DIR:-/data/models}"
CONFIG_FILE="${WORKSPACE_DIR}/config.json"
LAUNCHER_DIR="${WORKSPACE_DIR}/unified-launcher"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python versions
    for version in "3.10" "3.11"; do
        if command -v python${version} >/dev/null 2>&1; then
            log_success "Python ${version} found: $(python${version} --version)"
        else
            log_warning "Python ${version} not found - some tools may not work"
        fi
    done
    
    # Check Git
    if command -v git >/dev/null 2>&1; then
        log_success "Git found: $(git --version)"
    else
        log_error "Git not found - please install Git first"
        exit 1
    fi
    
    # Check disk space
    AVAILABLE_SPACE=$(df "$WORKSPACE_DIR" | awk 'NR==2 {print $4}')
    AVAILABLE_GB=$((AVAILABLE_SPACE / 1024 / 1024))
    
    if [ $AVAILABLE_GB -lt 50 ]; then
        log_warning "Only ${AVAILABLE_GB}GB available - recommend at least 50GB"
    else
        log_success "Disk space: ${AVAILABLE_GB}GB available"
    fi
}

# Create directory structure
create_directories() {
    log_info "Creating directory structure..."
    
    # Main directories
    mkdir -p "$WORKSPACE_DIR"
    mkdir -p "$MODELS_DIR"
    mkdir -p "$WORKSPACE_DIR/logs"
    mkdir -p "$LAUNCHER_DIR"
    
    # Model subdirectories
    for category in "Stable-diffusion" "Lora" "VAE" "ControlNet" "embeddings" "ESRGAN" "hypernetworks"; do
        mkdir -p "$MODELS_DIR/$category"
    done
    
    log_success "Directory structure created"
}

# Setup launcher
setup_launcher() {
    log_info "Setting up launcher..."
    
    cd "$LAUNCHER_DIR"
    
    # Create virtual environment for launcher
    if [ ! -d "launcher_venv" ]; then
        python3 -m venv launcher_venv
        log_success "Launcher virtual environment created"
    fi
    
    # Activate and install dependencies
    source launcher_venv/bin/activate
    pip install --upgrade pip
    
    if [ -f "requirements-launcher.txt" ]; then
        pip install -r requirements-launcher.txt
        log_success "Launcher dependencies installed"
    else
        log_warning "requirements-launcher.txt not found"
    fi
}

# Copy configuration files
setup_config() {
    log_info "Setting up configuration..."
    
    # Copy config file if it doesn't exist
    if [ ! -f "$CONFIG_FILE" ]; then
        if [ -f "$LAUNCHER_DIR/config.json" ]; then
            cp "$LAUNCHER_DIR/config.json" "$CONFIG_FILE"
            log_success "Configuration file copied"
        else
            log_warning "config.json not found - will be created on first run"
        fi
    fi
    
    # Update paths in config
    if command -v python3 >/dev/null 2>&1; then
        python3 << EOF
import json
import os

config_file = "$CONFIG_FILE"
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    config['workspace_settings']['workspace_dir'] = "$WORKSPACE_DIR"
    config['workspace_settings']['models_dir'] = "$MODELS_DIR"
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("Configuration updated with current paths")
EOF
    fi
}

# Setup individual tools
setup_tools() {
    log_info "Setting up WebUI tools..."
    
    cd "$LAUNCHER_DIR"
    
    # Use the manager to setup tools
    if [ -f "manage_venvs.py" ]; then
        source launcher_venv/bin/activate
        python manage_venvs.py --config "$CONFIG_FILE" --setup-all
    else
        log_warning "manage_venvs.py not found - tools will need to be set up manually"
    fi
}

# Create launch scripts
create_launch_scripts() {
    log_info "Creating launch scripts..."
    
    # Create launcher script
    cat > "$WORKSPACE_DIR/launch_webui_manager.sh" << 'EOF'
#!/bin/bash
# WebUI Manager Launcher Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER_DIR="$SCRIPT_DIR/unified-launcher"

echo "🚀 Starting Unified WebUI Launcher..."

cd "$LAUNCHER_DIR"

# Activate launcher environment
if [ -d "launcher_venv" ]; then
    source launcher_venv/bin/activate
else
    echo "❌ Launcher environment not found. Please run setup_environment.sh first."
    exit 1
fi

# Launch the notebook
if [ -f "unified_launcher.ipynb" ]; then
    echo "📓 Starting Jupyter notebook..."
    jupyter notebook unified_launcher.ipynb --ip=0.0.0.0 --port=8888 --no-browser --allow-root
else
    echo "❌ Launcher notebook not found."
    exit 1
fi
EOF
    
    chmod +x "$WORKSPACE_DIR/launch_webui_manager.sh"
    log_success "Launch script created"
    
    # Create CLI management script
    cat > "$WORKSPACE_DIR/manage_webuis.sh" << 'EOF'
#!/bin/bash
# CLI WebUI Management Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER_DIR="$SCRIPT_DIR/unified-launcher"
CONFIG_FILE="$SCRIPT_DIR/config.json"

cd "$LAUNCHER_DIR"

if [ -d "launcher_venv" ]; then
    source launcher_venv/bin/activate
    python manage_venvs.py --config "$CONFIG_FILE" "$@"
else
    echo "❌ Launcher environment not found. Please run setup_environment.sh first."
    exit 1
fi
EOF
    
    chmod +x "$WORKSPACE_DIR/manage_webuis.sh"
    log_success "CLI management script created"
}

# Main setup function
main() {
    echo "🚀 Unified WebUI Environment Setup"
    echo "=================================="
    echo ""
    echo "Workspace: $WORKSPACE_DIR"
    echo "Models:    $MODELS_DIR"
    echo ""
    
    check_prerequisites
    create_directories
    setup_launcher
    setup_config
    
    # Ask if user wants to setup tools now
    read -p "Setup all WebUI tools now? This will take significant time and bandwidth. (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_tools
    else
        log_info "Tool setup skipped. You can run it later with: ./manage_webuis.sh --setup-all"
    fi
    
    create_launch_scripts
    
    echo ""
    log_success "Setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. To launch the WebUI manager: ./launch_webui_manager.sh"
    echo "2. To manage tools via CLI: ./manage_webuis.sh --help"
    echo "3. Place your models in: $MODELS_DIR"
    echo ""
    echo "For more information, see the README.md file."
}

# Run main function
main "$@"
