# Unified Multi-WebUI Stable Diffusion Launcher

A comprehensive solution for managing multiple Stable Diffusion WebUIs with isolated environments and centralized asset management.

## 🎯 Project Overview

This project solves the two major challenges of running multiple Stable Diffusion WebUIs:

1. **Dependency Conflicts**: Each WebUI has different Python and package requirements that conflict with each other
2. **Storage Redundancy**: Multiple WebUIs duplicate models, wasting 50-100GB+ of storage

### ✅ Solution: Multi-Environment Architecture + Centralized Assets

- **7 Isolated Virtual Environments** prevent any dependency conflicts
- **Centralized Model Management** eliminates storage duplication
- **Advanced Gradio Interface** for easy management
- **Production-Ready** with comprehensive error handling

## 🛠️ Supported WebUIs

| WebUI | Environment | Centralization | Risk Level | Notes |
|-------|-------------|----------------|------------|--------|
| **AUTOMATIC1111** | `diffusion_main` | CLI Args | Low | Original, most stable |
| **SD.Next** | `sdnext_env` | CLI Args | Low | Modern features |
| **Forge WebUI** | `forge_env` | CLI Args | Medium | Performance optimized |
| **InvokeAI** | `invokeai_env` | Config Files | Low | Professional workflows |
| **Fooocus** | `diffusion_main` | Config Files | Low | Simplified interface |
| **FaceFusion** | `face_tools_stable` | None | Medium | Face processing |
| **ROOP-FLOYD** | `face_tools_legacy` | None | High | Legacy face swapping |

## 🚀 Quick Start

### Prerequisites

- **Python 3.10** and **Python 3.11** installed
- **Git** for repository cloning
- **50GB+** free disk space
- **NVIDIA GPU** with CUDA support (recommended)

### 1. Automated Setup

```bash
# Download and run the setup script
curl -O https://raw.githubusercontent.com/your-repo/unified-webui-launcher/main/setup_environment.sh
chmod +x setup_environment.sh
./setup_environment.sh

2. Manual Setup

# Clone the repository
git clone https://github.com/your-repo/unified-webui-launcher.git
cd unified-webui-launcher

# Create launcher environment
python3 -m venv launcher_venv
source launcher_venv/bin/activate
pip install -r requirements-launcher.txt

# Setup all WebUI environments
python manage_venvs.py --setup-all

3. Launch the Interface

# Start the Jupyter notebook launcher
./launch_webui_manager.sh

# Or use the CLI directly
./manage_webuis.sh --list-tools
./manage_webuis.sh --launch automatic1111

📁 Directory Structure

/workspace/                          # Main workspace
├── unified-launcher/                # Launcher files
│   ├── unified_launcher.ipynb      # Main notebook interface
│   ├── manage_venvs.py             # Environment manager
│   ├── config.json                 # Configuration
│   └── launcher_venv/              # Launcher environment
├── automatic1111/                  # WebUI repositories
│   └── a1111_venv/                 # Isolated environment
├── sdnext/
│   └── sdnext_venv/
├── forge/
│   └── forge_venv/
├── ...                             # Other WebUIs
└── logs/                           # Application logs

/data/models/                        # Centralized models
├── Stable-diffusion/               # Checkpoint models
├── Lora/                           # LoRA models  
├── VAE/                            # VAE models
├── ControlNet/                     # ControlNet models
├── embeddings/                     # Text embeddings
└── ESRGAN/                         # Upscaler models

🎛️ Configuration
Hardware Profiles

The system includes predefined hardware profiles for optimal performance:

    High VRAM (16GB+): RTX 3090/4090, A100
    Medium VRAM (8-16GB): RTX 3070/4070, RTX 3080
    Low VRAM (<8GB): RTX 3060, GTX 1080
    CPU Only: No GPU acceleration

Centralization Methods

Three methods are used to centralize model storage:

    CLI Arguments (A1111, Forge, SD.Next): Uses command-line flags
    Config Files (InvokeAI, Fooocus): Modifies configuration files
    Symbolic Links (Universal): OS-level file system links

🔧 Command Line Usage

# Setup commands
./manage_webuis.sh --setup-all              # Setup all tools
./manage_webuis.sh --setup automatic1111    # Setup specific tool

# Launch commands  
./manage_webuis.sh --launch sdnext --profile high_vram
./manage_webuis.sh --launch forge --args "--cuda-stream --pin-shared-memory"

# Management commands
./manage_webuis.sh --status                 # Show system status
./manage_webuis.sh --stop automatic1111     # Stop specific tool
./manage_webuis.sh --list-tools             # List all available tools

💾 Storage Savings
Before (Duplicated Storage)

automatic1111/models/    ~20GB
sdnext/models/          ~20GB  
forge/models/           ~20GB
fooocus/models/         ~20GB
invokeai/models/        ~20GB
Total:                  ~100GB

After (Centralized Storage)

/data/models/           ~20GB
Total:                  ~20GB
Savings:                ~80GB (80% reduction)

🎨 Advanced Features
Gradio Interface Features

    Real-time Status Monitoring: Live status indicators with animations
    Centralized Configuration: Global settings for all WebUIs
    Batch Operations: Setup, update, or stop multiple tools at once
    Live Log Streaming: Real-time output from all running tools
    Hardware Profile Selection: Automatic optimization for your GPU
    Process Management: Graceful start/stop with proper cleanup

Safety Features

    Isolated Environments: Zero chance of dependency conflicts
    Graceful Shutdown: Proper process termination with timeouts
    Error Recovery: Comprehensive error handling and logging
    Backup Integration: Safe model directory management

🔬 Technical Details
Dependency Conflict Resolution

The system uses complete isolation to prevent conflicts:

# Each tool gets its own environment
environments = {
    "automatic1111": "Python 3.10.6 + gradio 3.41.2",
    "sdnext": "Python 3.11 + gradio 3.43.2", 
    "forge": "Python 3.11 + PyTorch 2.3.1+",
    "invokeai": "Python 3.11 + React UI",
    "fooocus": "Python 3.10 + stable packages",
    "facefusion": "Python 3.11 + ONNX runtime",
    "roop_floyd": "Python 3.10 + legacy packages"
}

Centralized Asset Management

Three flexible methods ensure compatibility:

# Method 1: CLI Arguments (A1111 family)
python launch.py \
    --ckpt-dir /data/models/Stable-diffusion \
    --vae-dir /data/models/VAE \
    --lora-dir /data/models/Lora

# Method 2: Config Files (InvokeAI)
# invokeai.yaml
InvokeAI:
  models_dir: /data/models

# Method 3: Symbolic Links (Universal)
ln -s /data/models/Stable-diffusion /workspace/tool/models/

🐛 Troubleshooting
Common Issues

Environment Setup Fails

# Check Python versions
python3.10 --version
python3.11 --version

# Recreate environment
rm -rf tool_name/venv_name
./manage_webuis.sh --setup tool_name

WebUI Won't Start

# Check logs
tail -f /workspace/logs/tool_name_*.log

# Verify environment
./manage_webuis.sh --status

Models Not Found

# Check centralization
ls -la /data/models/Stable-diffusion/

# Verify symlinks
ls -la /workspace/automatic1111/models/

Getting Help


4. Usage Workflow

For Users (Colab + GitHub):

    Open in Colab:

    https://colab.research.google.com/github/your-username/unified-webui-launcher/blob/main/colab_launcher.ipynb

    First Time Setup (Run once):
        Mount Google Drive → Creates persistent storage
        Auto-detect GPU → Optimizes for T4/V100/A100
        Setup WebUI → ~15 minutes, saved to Drive

    Daily Usage (Instant):
        Open notebook → Auto-restores from Drive
        Launch WebUI → Instant startup
        Create art → Full WebUI functionality

    Session Management:
        Disconnect: Everything saved to Google Drive
        Reconnect: Run restore cell, instantly ready
        Share: Send Colab link to others

5. Colab-Specific Optimizations

Storage Strategy:

Google Drive/AI_WebUIs/
├── workspace/           # WebUI installations (persistent)
├── models/             # Shared models (persistent) 
├── environments/       # Python environments (persistent)
├── sessions/          # Session state (persistent)
└── logs/              # Execution logs (persistent)

Bandwidth Optimization:

    Smart Caching: Only download what's changed
    Incremental Setup: Resume interrupted installations
    Model Sharing: Single model storage across WebUIs
    Session Restore: Zero re-download on reconnect

GPU Auto-Detection:

# Automatically detects and optimizes for:
T4 (Free/Pro)    → --medvram --opt-channelslast
V100 (Pro)       → --medvram --xformers  
A100 (Pro+)      → --always-high-vram

6. Repository Setup Instructions

For Repository Creators:

    Create GitHub Repository:

    git init unified-webui-launcher
    cd unified-webui-launcher

    # Add all files (colab_launcher.ipynb, manage_venvs.py, etc.)
    git add .
    git commit -m "Initial Colab-optimized WebUI launcher"
    git push origin main

Add Colab Badge to README:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/your-username/unified-webui-launcher/blob/main/colab_launcher.ipynb)

    Enable GitHub Pages (optional):
        Settings → Pages → Deploy from branch main
        Creates documentation site

For Users:

    One-Click Launch: Click the Colab badge
    Fork for Customization: Fork repo for personal modifications
    Star for Updates: Get notified of improvements

This Colab + GitHub combo provides the ultimate accessibility - users get a production-ready multi-WebUI system with zero local installation, persistent storage, and automatic GPU optimization, all from a single click! 🚀

    Check logs: All output is logged to /workspace/logs/
    Verify setup: Use --status command to check system state
    Reset environment: Delete venv folder and re-run setup
    Check disk space: Ensure adequate storage for models

🔮 Future Enhancements

    Docker Containerization: Complete isolation with Docker Compose
    API Orchestration: Unified API layer across all WebUIs
    Cloud Integration: Direct integration with cloud storage providers
    Model Management: Automatic downloading and organization
    Performance Analytics: Resource usage monitoring and optimization

📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
🤝 Contributing

Contributions are welcome! Please read CONTRIBUTING.md for guidelines.
🙏 Acknowledgments

    All the amazing developers of the individual WebUI projects
    The Stable Diffusion community for continuous innovation
    Contributors and testers who helped refine this system
