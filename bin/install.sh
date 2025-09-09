#!/bin/bash
# SD-Host CLI Installation Script (Bash)
# Cross-platform installer for Unix/Linux/macOS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Options
UNINSTALL=false
FORCE=false
QUIET=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--uninstall)
            UNINSTALL=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        -h|--help)
            echo "SD-Host CLI Installation Script"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -u, --uninstall    Remove SD-Host CLI from PATH"
            echo "  -f, --force        Force reinstallation"
            echo "  -q, --quiet        Quiet installation"
            echo "  -h, --help         Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Helper functions
print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

print_title() {
    echo -e "${BLUE}$1${NC}"
}

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BIN_DIR="$SCRIPT_DIR"

if [ "$QUIET" = false ]; then
    print_title "SD-Host CLI Installation Script"
    print_title "================================"
    echo ""
fi

# Detect platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="Linux"
elif [[ "$OSTYPE" == "freebsd"* ]]; then
    PLATFORM="FreeBSD"
else
    PLATFORM="Unix"
fi

MAIN_SCRIPT="sdh"

if [ "$QUIET" = false ]; then
    print_info "Platform: $PLATFORM"
    print_info "Project root: $PROJECT_ROOT"
    print_info "Bin directory: $BIN_DIR"
    echo ""
fi

# Function to check if directory is in PATH
is_in_path() {
    local dir="$1"
    echo "$PATH" | tr ':' '\n' | grep -Fx "$dir" > /dev/null 2>&1
}

# Function to add directory to PATH
add_to_path() {
    local dir="$1"
    local shell_profiles=()
    
    # Detect shell profiles
    [ -f "$HOME/.bashrc" ] && shell_profiles+=("$HOME/.bashrc")
    [ -f "$HOME/.zshrc" ] && shell_profiles+=("$HOME/.zshrc")
    [ -f "$HOME/.profile" ] && shell_profiles+=("$HOME/.profile")
    
    local export_line="export PATH=\"$dir:\$PATH\""
    local added=false
    
    for profile in "${shell_profiles[@]}"; do
        if ! grep -Fq "$dir" "$profile" 2>/dev/null; then
            echo "" >> "$profile"
            echo "# SD-Host CLI" >> "$profile"
            echo "$export_line" >> "$profile"
            print_success "Added to $profile"
            added=true
        fi
    done
    
    # If no profiles exist, create .profile
    if [ "$added" = false ] && [ ${#shell_profiles[@]} -eq 0 ]; then
        echo "# SD-Host CLI" >> "$HOME/.profile"
        echo "$export_line" >> "$HOME/.profile"
        print_success "Created and added to ~/.profile"
        added=true
    fi
    
    # Update current session
    export PATH="$dir:$PATH"
    print_success "Added to current session PATH"
    
    if [ "$QUIET" = false ]; then
        print_warning "Please restart your terminal or run: source ~/.bashrc (or ~/.zshrc)"
    fi
}

# Function to remove directory from PATH
remove_from_path() {
    local dir="$1"
    local shell_profiles=(
        "$HOME/.bashrc"
        "$HOME/.zshrc"
        "$HOME/.profile"
    )
    
    for profile in "${shell_profiles[@]}"; do
        if [ -f "$profile" ] && grep -Fq "$dir" "$profile"; then
            # Remove the export line and the comment above it
            sed -i.bak '/# SD-Host CLI/,+1d' "$profile" 2>/dev/null || true
            print_success "Removed from $profile"
        fi
    done
}

# Main installation logic
if [ "$UNINSTALL" = true ]; then
    if [ "$QUIET" = false ]; then
        print_info "Uninstalling SD-Host CLI..."
    fi
    
    if is_in_path "$BIN_DIR"; then
        remove_from_path "$BIN_DIR"
        print_success "SD-Host CLI removed from PATH"
    else
        print_warning "SD-Host CLI was not found in PATH"
    fi
    
    if [ "$QUIET" = false ]; then
        print_info "Uninstallation complete"
    fi
else
    if [ "$QUIET" = false ]; then
        print_info "Installing SD-Host CLI..."
    fi
    
    # Check if bin directory exists
    if [ ! -d "$BIN_DIR" ]; then
        print_error "Bin directory not found: $BIN_DIR"
        exit 1
    fi
    
    # Check if main script exists
    MAIN_SCRIPT_PATH="$BIN_DIR/$MAIN_SCRIPT"
    if [ ! -f "$MAIN_SCRIPT_PATH" ]; then
        print_error "Main script not found: $MAIN_SCRIPT_PATH"
        exit 1
    fi
    
    # Make sure script is executable
    chmod +x "$MAIN_SCRIPT_PATH"
    
    # Check if already in PATH
    if is_in_path "$BIN_DIR"; then
        if [ "$FORCE" = true ]; then
            if [ "$QUIET" = false ]; then
                print_info "Directory already in PATH, reinstalling..."
            fi
            remove_from_path "$BIN_DIR"
            add_to_path "$BIN_DIR"
        else
            print_warning "Directory already in PATH: $BIN_DIR"
            if [ "$QUIET" = false ]; then
                print_info "Use --force to reinstall"
            fi
            exit 0
        fi
    else
        add_to_path "$BIN_DIR"
    fi
    
    # Test the CLI
    if [ "$QUIET" = false ]; then
        print_info "Testing CLI installation..."
        if "$MAIN_SCRIPT_PATH" --version > /dev/null 2>&1; then
            print_success "CLI test successful"
        else
            print_warning "CLI test failed"
        fi
    fi
    
    print_success "SD-Host CLI installed successfully!"
    
    if [ "$QUIET" = false ]; then
        echo ""
        print_title "Quick Start:"
        echo "  $MAIN_SCRIPT --help          # Show help"
        echo "  $MAIN_SCRIPT --version       # Show version"
        echo "  $MAIN_SCRIPT service status  # Check service status"
        echo "  $MAIN_SCRIPT config show     # Show configuration"
        echo ""
    fi
fi
