#!/usr/bin/env python3
"""
Enhanced Multi-Environment Manager for Stable Diffusion WebUIs
Solves dependency conflicts through complete isolation
"""

import os
import sys
import subprocess
import json
import shutil
import logging
import psutil
import threading
import time
import signal
import queue
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import yaml

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('venv_manager.log')
    ]
)
logger = logging.getLogger(__name__)

class EnhancedMultiVenvManager:
    """Enhanced manager for multiple isolated virtual environments"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.load_config()
        self.workspace_dir = Path(self.config['workspace_settings']['workspace_dir'])
        self.models_dir = Path(self.config['workspace_settings']['models_dir'])
        self.processes: Dict[str, Dict[str, Any]] = {}
        self.log_queues: Dict[str, queue.Queue] = {}
        self.monitoring_active = False
        self.setup_base_structure()
        
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file {self.config_path} not found")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise
    
    def setup_base_structure(self):
        """Create base directory structure"""
        directories = [
            self.workspace_dir,
            self.workspace_dir / 'logs',
            self.models_dir
        ]
        
        # Create model subdirectories
        for category in self.config['model_categories'].keys():
            directories.append(self.models_dir / category)
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
        logger.info(f"Base structure created at {self.workspace_dir}")
        self._create_model_readmes()
    
    def _create_model_readmes(self):
        """Create README files in model directories"""
        for category, info in self.config['model_categories'].items():
            readme_path = self.models_dir / category / "README.txt"
            if not readme_path.exists():
                content = f"""
{category} Models Directory
{'=' * (len(category) + 16)}

{info['description']}

Supported formats: {', '.join(info['extensions'])}
Estimated size per model: ~{info['size_estimate_gb']} GB

This directory is shared across all compatible WebUIs to prevent duplication.
Place your {category.lower()} files here to make them available to all tools.
"""
                readme_path.write_text(content)
    
    def get_python_executable(self, version: str) -> str:
        """Get Python executable for specific version"""
        executables = [
            f"python{version}",
            f"python{version[:3]}", 
            "python3",
            "python"
        ]
        
        for exe in executables:
            if shutil.which(exe):
                try:
                    result = subprocess.run(
                        [exe, "--version"], 
                        capture_output=True, 
                        text=True,
                        timeout=10
                    )
                    ### FIXED ###: Change from exact match `in` to `startswith` for flexibility
                    if result.stdout.strip().startswith(f"Python {version}"):
                        return exe
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    continue
        
        raise RuntimeError(f"Python {version} not found. Please install it first.")
    
    def clone_repository(self, tool_id: str) -> bool:
        """Clone repository for specific tool"""
        tool_config = self.config['tools'][tool_id]
        tool_dir = self.workspace_dir / tool_config['dir']
        
        if tool_dir.exists():
            logger.info(f"Repository for {tool_config['name']} already exists")
            return True
        
        try:
            logger.info(f"Cloning {tool_config['name']} repository...")
            cmd = [
                "git", "clone", "--depth", "1", 
                tool_config['repo'], str(tool_dir)
            ]
            
            subprocess.run(cmd, check=True, timeout=300)
            logger.info(f"✅ Repository cloned for {tool_config['name']}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Timeout cloning repository for {tool_config['name']}")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to clone repository for {tool_config['name']}: {e}")
            return False
    
    def create_virtual_environment(self, tool_id: str) -> bool:
        """Create virtual environment for specific tool"""
        tool_config = self.config['tools'][tool_id]
        tool_dir = self.workspace_dir / tool_config['dir']
        venv_dir = tool_dir / tool_config['venv_name']
        
        if venv_dir.exists():
            logger.info(f"Virtual environment for {tool_config['name']} already exists")
            return True
        
        try:
            python_exe = self.get_python_executable(tool_config['python_version'])
            logger.info(f"Creating venv for {tool_config['name']} using {python_exe}")
            
            # Create virtual environment
            subprocess.run([
                python_exe, "-m", "venv", str(venv_dir)
            ], check=True, timeout=120)
            
            ### FIXED ###: Ensure pip exists to prevent exit code 127
            logger.info("Ensuring pip is available in the new venv...")
            subprocess.run([
                str(python_exe), "-m", "ensurepip", "--upgrade"
            ], check=True, timeout=120)
            
            # Upgrade pip using the venv's python
            venv_python_exe = venv_dir / "bin" / "python"
            subprocess.run([
                str(venv_python_exe), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"
            ], check=True, timeout=300)
            
            logger.info(f"✅ Virtual environment created for {tool_config['name']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create venv for {tool_config['name']}: {e}")
            return False
    
    # ... The rest of the file (install_dependencies, launch_tool, etc.) remains the same ...
    # (The following code is the same as before, no changes needed)
    
    def install_dependencies(self, tool_id: str) -> bool:
        """Install dependencies for specific tool"""
        tool_config = self.config['tools'][tool_id]
        tool_dir = self.workspace_dir / tool_config['dir']
        venv_dir = tool_dir / tool_config['venv_name']
        
        if os.name == 'nt':  # Windows
            pip_exe = venv_dir / "Scripts/pip.exe"
            python_exe = venv_dir / "Scripts/python.exe"
        else:  # Unix/Linux
            pip_exe = venv_dir / "bin/pip"
            python_exe = venv_dir / "bin/python"
        
        try:
            # Execute install command
            install_cmd = tool_config['install_cmd'].format(
                pip=str(pip_exe),
                python=str(python_exe)
            )
            
            logger.info(f"Installing dependencies for {tool_config['name']}")
            logger.info(f"Command: {install_cmd}")
            
            # Run in tool directory
            subprocess.run(
                install_cmd,
                shell=True,
                cwd=str(tool_dir),
                check=True,
                timeout=1800  # 30 minutes max
            )
            
            logger.info(f"✅ Dependencies installed for {tool_config['name']}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Timeout installing dependencies for {tool_config['name']}")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install dependencies for {tool_config['name']}: {e}")
            return False
    
    def apply_centralized_config(self, tool_id: str) -> bool:
        """Apply centralized model configuration"""
        tool_config = self.config['tools'][tool_id]
        method = tool_config.get('centralization_method', 'none')
        
        if method == 'none':
            logger.info(f"{tool_config['name']} uses specialized models - skipping centralization")
            return True
        
        elif method == 'cli_args':
            # CLI arguments will be added during launch
            logger.info(f"CLI centralization configured for {tool_config['name']}")
            return True
            
        elif method == 'config_files':
            return self._create_config_file(tool_id)
        
        else:
            logger.warning(f"Unknown centralization method: {method}")
            return False
    
    def _create_config_file(self, tool_id: str) -> bool:
        """Create configuration file for centralized models"""
        tool_config = self.config['tools'][tool_id]
        tool_dir = self.workspace_dir / tool_config['dir']
        
        if 'config_file' not in tool_config or 'config_template' not in tool_config:
            logger.warning(f"No config template defined for {tool_id}")
            return False
        
        config_path = tool_dir / tool_config['config_file']
        config_data = tool_config['config_template'].copy()
        
        # Replace model directory placeholders
        def replace_placeholders(obj):
            if isinstance(obj, dict):
                return {k: replace_placeholders(v) for k, v in obj.items()}
            elif isinstance(obj, str):
                return obj.format(models_dir=str(self.models_dir))
            else:
                return obj
        
        config_data = replace_placeholders(config_data)
        
        try:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                with open(config_path, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
            else:
                with open(config_path, 'w') as f:
                    json.dump(config_data, f, indent=2)
            
            logger.info(f"Configuration file created: {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create config file for {tool_id}: {e}")
            return False
    
    def setup_tool(self, tool_id: str) -> bool:
        """Complete setup for a single tool"""
        if tool_id not in self.config['tools']:
            logger.error(f"Unknown tool: {tool_id}")
            return False
        
        tool_config = self.config['tools'][tool_id]
        logger.info(f"🚀 Setting up {tool_config['name']}...")
        
        steps = [
            ("Clone repository", lambda: self.clone_repository(tool_id)),
            ("Create virtual environment", lambda: self.create_virtual_environment(tool_id)),
            ("Install dependencies", lambda: self.install_dependencies(tool_id)),
            ("Apply centralized config", lambda: self.apply_centralized_config(tool_id))
        ]
        
        for step_name, step_func in steps:
            logger.info(f"  {step_name}...")
            if not step_func():
                logger.error(f"❌ {tool_config['name']} setup failed at: {step_name}")
                return False
        
        logger.info(f"✅ {tool_config['name']} setup complete!")
        return True
    
    def setup_all_tools(self) -> Dict[str, bool]:
        """Setup all tools and return status"""
        results = {}
        
        logger.info("🚀 Starting batch setup of all tools...")
        
        for tool_id in self.config['tools'].keys():
            results[tool_id] = self.setup_tool(tool_id)
        
        # Summary
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        logger.info(f"📊 Setup Summary: {success_count}/{total_count} tools successful")
        
        return results
    
    def get_launch_command(self, tool_id: str, custom_args: List[str] = None,
                          hardware_profile: str = None) -> List[str]:
        """Generate launch command for specific tool"""
        tool_config = self.config['tools'][tool_id]
        tool_dir = self.workspace_dir / tool_config['dir']
        venv_dir = tool_dir / tool_config['venv_name']
        
        if os.name == 'nt':  # Windows
            python_exe = venv_dir / "Scripts/python.exe"
        else:  # Unix/Linux
            python_exe = venv_dir / "bin/python"
        
        # Base command
        cmd = [str(python_exe), tool_config['script']]
        
        # Add default arguments
        cmd.extend(tool_config.get('default_args', []))
        
        # Add hardware profile arguments
        if hardware_profile and hardware_profile in self.config['hardware_profiles']:
            profile_args = self.config['hardware_profiles'][hardware_profile]['args']
            cmd.extend(profile_args)
        
        # Add centralized model arguments (for CLI method)
        if tool_config.get('centralization_method') == 'cli_args':
            central_args = tool_config.get('centralization_args', [])
            formatted_args = [
                arg.format(models_dir=str(self.models_dir)) for arg in central_args
            ]
            cmd.extend(formatted_args)
        
        # Add custom arguments
        if custom_args:
            cmd.extend(custom_args)
        
        return cmd
    
    def launch_tool(self, tool_id: str, custom_args: List[str] = None,
                   hardware_profile: str = None) -> bool:
        """Launch a tool in its isolated environment"""
        if tool_id not in self.config['tools']:
            raise ValueError(f"Unknown tool: {tool_id}")
        
        tool_config = self.config['tools'][tool_id]
        tool_dir = self.workspace_dir / tool_config['dir']
        
        if not tool_dir.exists():
            raise RuntimeError(f"{tool_config['name']} is not installed. Run setup first.")
        
        cmd = self.get_launch_command(tool_id, custom_args, hardware_profile)
        
        # Setup logging
        log_queue = queue.Queue(maxsize=1000)
        self.log_queues[tool_id] = log_queue
        
        # Create log file
        log_dir = self.workspace_dir / 'logs'
        log_file = log_dir / f"{tool_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        try:
            logger.info(f"🚀 Launching {tool_config['name']}...")
            logger.info(f"Command: {' '.join(cmd)}")
            
            # Launch process
            process = subprocess.Popen(
                cmd,
                cwd=str(tool_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Store process info
            self.processes[tool_id] = {
                'process': process,
                'pid': process.pid,
                'start_time': datetime.now(),
                'status': 'starting',
                'log_file': log_file,
                'command': ' '.join(cmd),
                'tool_config': tool_config
            }
            
            # Start output monitoring
            monitor_thread = threading.Thread(
                target=self._monitor_process_output,
                args=(tool_id, process, log_queue, log_file)
            )
            monitor_thread.daemon = True
            monitor_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to launch {tool_id}: {e}")
            return False
    
    def _monitor_process_output(self, tool_id: str, process: subprocess.Popen,
                               log_queue: queue.Queue, log_file: Path):
        """Monitor process output and update logs"""
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                for line in iter(process.stdout.readline, ''):
                    if line:
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        log_entry = f"[{timestamp}] {line.strip()}"
                        
                        # Write to file
                        f.write(log_entry + '\n')
                        f.flush()
                        
                        # Add to queue (non-blocking)
                        try:
                            log_queue.put(log_entry, timeout=0.1)
                        except queue.Full:
                            pass  # Skip if queue is full
                        
                        # Update status based on output
                        self._parse_status_from_output(tool_id, line)
        
        except Exception as e:
            logger.error(f"Error monitoring output for {tool_id}: {e}")
        
        finally:
            # Process finished
            if tool_id in self.processes:
                self.processes[tool_id]['status'] = 'stopped'
    
    def _parse_status_from_output(self, tool_id: str, line: str):
        """Parse status from process output"""
        line_lower = line.lower()
        
        if any(phrase in line_lower for phrase in [
            'running on', 'server started', 'listening on', 'model loaded'
        ]):
            if tool_id in self.processes:
                self.processes[tool_id]['status'] = 'running'
        
        elif any(phrase in line_lower for phrase in [
            'error', 'failed', 'exception', 'traceback'
        ]):
            if tool_id in self.processes:
                self.processes[tool_id]['status'] = 'error'
    
    def stop_tool(self, tool_id: str) -> bool:
        """Stop a running tool"""
        if tool_id not in self.processes:
            return False
        
        process_info = self.processes[tool_id]
        process = process_info['process']
        
        if process.poll() is None:  # Still running
            try:
                # Graceful termination
                if os.name == 'nt':  # Windows
                    process.terminate()
                else:  # Unix/Linux
                    process.send_signal(signal.SIGTERM)
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill
                    process.kill()
                    process.wait()
                
                process_info['status'] = 'stopped'
                logger.info(f"🛑 {process_info['tool_config']['name']} stopped")
                return True
                
            except Exception as e:
                logger.error(f"Error stopping {tool_id}: {e}")
                return False
        
        return True
    
    def get_process_status(self, tool_id: str) -> Dict[str, Any]:
        """Get current status of a process"""
        if tool_id not in self.processes:
            return {'status': 'not_started'}
        
        process_info = self.processes[tool_id]
        process = process_info['process']
        
        # Update status based on process state
        if process.poll() is None:
            # Process still running
            if process_info['status'] == 'starting':
                elapsed = (datetime.now() - process_info['start_time']).seconds
                if elapsed > 30:  # Assume running after 30 seconds
                    process_info['status'] = 'running'
        else:
            # Process finished
            process_info['status'] = 'stopped'
        
        return process_info
    
    def get_logs(self, tool_id: str, max_lines: int = 50) -> List[str]:
        """Get recent log lines"""
        if tool_id not in self.log_queues:
            return []
        
        log_queue = self.log_queues[tool_id]
        logs = []
        
        while not log_queue.empty() and len(logs) < max_lines:
            try:
                log_entry = log_queue.get_nowait()
                logs.append(log_entry)
            except queue.Empty:
                break
        
        return logs[-max_lines:]
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        total_tools = len(self.config['tools'])
        running_tools = sum(1 for tool_id in self.processes.keys()
                           if self.get_process_status(tool_id)['status'] == 'running')
        
        # Calculate model storage info
        total_size_gb = 0
        model_counts = {}
        
        for category in self.config['model_categories'].keys():
            category_dir = self.models_dir / category
            if category_dir.exists():
                files = list(category_dir.glob("*"))
                model_files = [f for f in files if f.is_file() and 
                             f.suffix in self.config['model_categories'][category]['extensions']]
                model_counts[category] = len(model_files)
                
                # Estimate total size
                for f in model_files:
                    try:
                        total_size_gb += f.stat().st_size / (1024**3)
                    except OSError:
                        pass
        
        return {
            'total_tools': total_tools,
            'running_tools': running_tools,
            'total_models': sum(model_counts.values()),
            'total_size_gb': round(total_size_gb, 2),
            'model_counts': model_counts,
            'workspace_dir': str(self.workspace_dir),
            'models_dir': str(self.models_dir)
        }

def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Multi-Environment WebUI Manager")
    parser.add_argument("--config", default="config.json", help="Configuration file")
    parser.add_argument("--setup-all", action="store_true", help="Setup all tools")
    parser.add_argument("--setup", help="Setup specific tool")
    parser.add_argument("--launch", help="Launch specific tool")
    parser.add_argument("--stop", help="Stop specific tool")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--list-tools", action="store_true", help="List available tools")
    parser.add_argument("--args", nargs="*", help="Custom launch arguments")
    parser.add_argument("--profile", help="Hardware profile to use")
    
    args = parser.parse_args()
    
    try:
        manager = EnhancedMultiVenvManager(args.config)
        
        if args.list_tools:
            print("\n📋 Available Tools:")
            for tool_id, config in manager.config['tools'].items():
                print(f"  {config['icon']} {tool_id}: {config['name']}")
                print(f"     {config['description']}")
        
        elif args.setup_all:
            results = manager.setup_all_tools()
            print("\n📊 Setup Results:")
            for tool_id, success in results.items():
                status = "✅" if success else "❌"
                tool_name = manager.config['tools'][tool_id]['name']
                print(f"  {status} {tool_name}")
        
        elif args.setup:
            success = manager.setup_tool(args.setup)
            tool_name = manager.config['tools'][args.setup]['name']
            if success:
                print(f"✅ {tool_name} setup complete")
            else:
                print(f"❌ {tool_name} setup failed")
        
        elif args.launch:
            success = manager.launch_tool(args.launch, args.args, args.profile)
            tool_name = manager.config['tools'][args.launch]['name']
            if success:
                print(f"🚀 {tool_name} launched")
            else:
                print(f"❌ {tool_name} launch failed")
        
        elif args.stop:
            success = manager.stop_tool(args.stop)
            tool_name = manager.config['tools'][args.stop]['name']
            if success:
                print(f"🛑 {tool_name} stopped")
            else:
                print(f"❌ Failed to stop {tool_name}")
        
        elif args.status:
            status = manager.get_system_status()
            print(f"\n📊 System Status:")
            print(f"  Tools: {status['running_tools']}/{status['total_tools']} running")
            print(f"  Models: {status['total_models']} total ({status['total_size_gb']} GB)")
            print(f"  Workspace: {status['workspace_dir']}")
            print(f"  Models Dir: {status['models_dir']}")
        
        else:
            parser.print_help()
    
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
