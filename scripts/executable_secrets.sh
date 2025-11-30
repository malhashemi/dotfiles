#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  secrets - On-demand Bitwarden secrets sync                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────────
SECRETS_FILE="$HOME/.secrets"
BW_ITEM_NAME="dotfiles-secrets"
VERBOSE=false

# ─────────────────────────────────────────────────────────────────────────────────
# Colors & Styling (Catppuccin-inspired)
# ─────────────────────────────────────────────────────────────────────────────────
readonly RESET='\033[0m'
readonly BOLD='\033[1m'
readonly DIM='\033[2m'

readonly RED='\033[38;5;210m'
readonly GREEN='\033[38;5;151m'
readonly YELLOW='\033[38;5;223m'
readonly BLUE='\033[38;5;117m'
readonly MAGENTA='\033[38;5;183m'
readonly CYAN='\033[38;5;159m'
readonly WHITE='\033[38;5;255m'
readonly GRAY='\033[38;5;245m'

# Symbols
readonly ICON_KEY="🔑"
readonly ICON_LOCK="🔒"
readonly ICON_UNLOCK="🔓"
readonly ICON_CHECK="✓"
readonly ICON_CROSS="✗"
readonly ICON_PLUS="+"
readonly ICON_CHANGE="~"
readonly ICON_ARROW="→"
readonly ICON_SPARKLE="✨"

# ─────────────────────────────────────────────────────────────────────────────────
# Output Functions
# ─────────────────────────────────────────────────────────────────────────────────
print_header() {
    echo ""
    echo -e "${MAGENTA}${BOLD}  ╔═══════════════════════════════════════════════════════╗${RESET}"
    echo -e "${MAGENTA}${BOLD}  ║${RESET}  ${ICON_KEY} ${WHITE}${BOLD}Secrets Sync${RESET}                                    ${MAGENTA}${BOLD}║${RESET}"
    echo -e "${MAGENTA}${BOLD}  ╚═══════════════════════════════════════════════════════╝${RESET}"
    echo ""
}

print_status() {
    local icon="$1"
    local color="$2"
    local message="$3"
    echo -e "  ${color}${icon}${RESET}  ${message}"
}

print_success() {
    print_status "${ICON_CHECK}" "${GREEN}" "$1"
}

print_error() {
    print_status "${ICON_CROSS}" "${RED}" "$1"
}

print_info() {
    print_status "${ICON_ARROW}" "${CYAN}" "$1"
}

print_warning() {
    print_status "!" "${YELLOW}" "$1"
}

print_divider() {
    echo -e "  ${DIM}─────────────────────────────────────────────────────────${RESET}"
}

# ─────────────────────────────────────────────────────────────────────────────────
# Spinner Functions
# ─────────────────────────────────────────────────────────────────────────────────
SPINNER_PID=""
SPINNER_FRAMES=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")

spinner_start() {
    local message="$1"
    
    # Hide cursor
    tput civis 2>/dev/null || true
    
    (
        local i=0
        while true; do
            local frame="${SPINNER_FRAMES[$i]}"
            printf "\r  ${MAGENTA}%s${RESET}  %s" "$frame" "$message" >&2
            i=$(( (i + 1) % ${#SPINNER_FRAMES[@]} ))
            sleep 0.08
        done
    ) &
    SPINNER_PID=$!
}

spinner_stop() {
    local success="${1:-true}"
    local message="${2:-}"
    
    # Kill spinner process
    if [[ -n "$SPINNER_PID" ]]; then
        kill "$SPINNER_PID" 2>/dev/null || true
        wait "$SPINNER_PID" 2>/dev/null || true
        SPINNER_PID=""
    fi
    
    # Show cursor
    tput cnorm 2>/dev/null || true
    
    # Clear line and print result
    printf "\r\033[K" >&2
    
    if [[ -n "$message" ]]; then
        if [[ "$success" == true ]]; then
            print_success "$message"
        else
            print_warning "$message"
        fi
    fi
}

# Cleanup spinner on exit
cleanup() {
    if [[ -n "$SPINNER_PID" ]]; then
        kill "$SPINNER_PID" 2>/dev/null || true
    fi
    tput cnorm 2>/dev/null || true
}
trap cleanup EXIT

# ─────────────────────────────────────────────────────────────────────────────────
# Secret Display Functions
# ─────────────────────────────────────────────────────────────────────────────────
mask_value() {
    local value="$1"
    local len=${#value}
    
    if [[ $len -le 4 ]]; then
        echo "****"
    elif [[ $len -le 8 ]]; then
        echo "****${value: -2}"
    else
        echo "****${value: -4}"
    fi
}

print_secret_added() {
    local name="$1"
    local value="$2"
    
    if [[ "$VERBOSE" == true ]]; then
        local masked
        masked=$(mask_value "$value")
        echo -e "    ${GREEN}${ICON_PLUS}${RESET}  ${GREEN}${name}${RESET} ${DIM}= ${masked}${RESET} ${DIM}(new)${RESET}"
    else
        echo -e "    ${GREEN}${ICON_PLUS}${RESET}  ${GREEN}${name}${RESET} ${DIM}(new)${RESET}"
    fi
}

print_secret_changed() {
    local name="$1"
    local value="$2"
    
    if [[ "$VERBOSE" == true ]]; then
        local masked
        masked=$(mask_value "$value")
        echo -e "    ${YELLOW}${ICON_CHANGE}${RESET}  ${YELLOW}${name}${RESET} ${DIM}= ${masked}${RESET} ${DIM}(updated)${RESET}"
    else
        echo -e "    ${YELLOW}${ICON_CHANGE}${RESET}  ${YELLOW}${name}${RESET} ${DIM}(updated)${RESET}"
    fi
}

print_secret_unchanged() {
    local name="$1"
    local value="$2"
    
    if [[ "$VERBOSE" == true ]]; then
        local masked
        masked=$(mask_value "$value")
        echo -e "    ${DIM}${ICON_CHECK}  ${name} = ${masked}${RESET}"
    else
        echo -e "    ${DIM}${ICON_CHECK}  ${name}${RESET}"
    fi
}

print_summary() {
    local added="$1"
    local changed="$2"
    local total="$3"
    
    echo ""
    print_divider
    echo ""
    
    if [[ $added -eq 0 && $changed -eq 0 ]]; then
        echo -e "  ${ICON_SPARKLE} ${WHITE}${BOLD}All ${total} secrets up to date${RESET}"
    else
        local parts=()
        [[ $added -gt 0 ]] && parts+=("${GREEN}${added} added${RESET}")
        [[ $changed -gt 0 ]] && parts+=("${YELLOW}${changed} updated${RESET}")
        
        # Join with comma
        local summary=""
        for i in "${!parts[@]}"; do
            [[ $i -gt 0 ]] && summary+=", "
            summary+="${parts[$i]}"
        done
        
        echo -e "  ${ICON_SPARKLE} ${WHITE}${BOLD}Synced ${total} secrets${RESET} ${DIM}(${summary}${DIM})${RESET}"
    fi
    echo ""
}

# ─────────────────────────────────────────────────────────────────────────────────
# Error Handling
# ─────────────────────────────────────────────────────────────────────────────────
error_exit() {
    local message="$1"
    local hint="${2:-}"
    
    echo ""
    print_error "${RED}${BOLD}Error:${RESET} ${message}"
    
    if [[ -n "$hint" ]]; then
        echo ""
        echo -e "  ${CYAN}${BOLD}Hint:${RESET} ${hint}"
    fi
    
    if [[ -f "$SECRETS_FILE" ]]; then
        echo ""
        print_warning "Existing ${SECRETS_FILE} preserved"
    fi
    
    echo ""
    exit 1
}

# ─────────────────────────────────────────────────────────────────────────────────
# Bitwarden Functions
# ─────────────────────────────────────────────────────────────────────────────────
check_bw_installed() {
    if ! command -v bw &> /dev/null; then
        error_exit "Bitwarden CLI (bw) not found" \
            "Install with: brew install bitwarden-cli (macOS) or download from bitwarden.com/download"
    fi
    
    if ! command -v jq &> /dev/null; then
        error_exit "jq not found (required for JSON parsing)" \
            "Install with: brew install jq (macOS) or apt install jq (Linux)"
    fi
}

check_bw_status() {
    local status
    status=$(bw status 2>/dev/null | jq -r '.status' 2>/dev/null) || status="unauthenticated"
    echo "$status"
}

unlock_vault() {
    print_info "Unlocking Bitwarden vault..."
    echo ""
    
    local session
    if ! session=$(bw unlock --raw 2>&1); then
        error_exit "Failed to unlock vault" \
            "Check your master password and try again"
    fi
    
    export BW_SESSION="$session"
    
    echo ""
    print_success "Vault unlocked ${ICON_UNLOCK}"
}

login_vault() {
    print_info "Logging into Bitwarden..."
    echo ""
    
    if ! bw login; then
        error_exit "Failed to login to Bitwarden" \
            "Check your credentials and internet connection"
    fi
    
    echo ""
    print_success "Logged in successfully"
}

sync_vault() {
    spinner_start "Syncing vault..."
    if ! bw sync &>/dev/null; then
        spinner_stop false "Sync failed (continuing with cached data)"
    else
        spinner_stop true "Vault synced"
    fi
}

fetch_secrets() {
    local item_json
    
    spinner_start "Fetching secrets from '${BW_ITEM_NAME}'..."
    
    if ! item_json=$(bw get item "$BW_ITEM_NAME" 2>&1); then
        spinner_stop false ""
        error_exit "Failed to fetch item '${BW_ITEM_NAME}'" \
            "Ensure the item exists in your Bitwarden vault with custom fields"
    fi
    
    # Extract fields as name=value pairs (tab-separated for safety)
    local fields
    fields=$(echo "$item_json" | jq -r '.fields[]? | "\(.name)\t\(.value)"' 2>/dev/null)
    
    if [[ -z "$fields" ]]; then
        spinner_stop false ""
        error_exit "No custom fields found in '${BW_ITEM_NAME}'" \
            "Add custom fields to the Bitwarden item (use 'Hidden field' type for sensitive values)"
    fi
    
    spinner_stop true "Fetched secrets from '${BW_ITEM_NAME}'"
    
    echo "$fields"
}

# ─────────────────────────────────────────────────────────────────────────────────
# Secrets File Management
# ─────────────────────────────────────────────────────────────────────────────────
get_existing_secrets() {
    if [[ -f "$SECRETS_FILE" ]]; then
        # Extract name=value pairs from existing file
        grep -E '^export [A-Za-z_][A-Za-z0-9_]*=' "$SECRETS_FILE" 2>/dev/null | \
            sed 's/^export //' | \
            sed 's/="/\t/' | \
            sed 's/"$//' || true
    fi
}

generate_secrets_file() {
    local secrets="$1"
    local tmp_file
    tmp_file=$(mktemp)
    
    # Write header
    cat > "$tmp_file" << 'EOF'
#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  Secret Environment Variables                                                 ║
# ║  Auto-generated by 'secrets' command - Source: Bitwarden                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# DO NOT EDIT THIS FILE DIRECTLY
#
# To add/update secrets:
#   1. Edit in Bitwarden (item: "dotfiles-secrets")
#   2. Run: secrets
#

EOF
    
    # Add timestamp
    echo "# Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$tmp_file"
    echo "" >> "$tmp_file"
    
    # Write exports (secrets is tab-separated: name\tvalue)
    while IFS=$'\t' read -r name value; do
        [[ -z "$name" ]] && continue
        # Escape any double quotes in value
        value="${value//\"/\\\"}"
        echo "export ${name}=\"${value}\"" >> "$tmp_file"
    done <<< "$secrets"
    
    # Atomic move to final location
    mv "$tmp_file" "$SECRETS_FILE"
    chmod 600 "$SECRETS_FILE"
}

# ─────────────────────────────────────────────────────────────────────────────────
# Diff & Comparison
# ─────────────────────────────────────────────────────────────────────────────────
compare_and_display() {
    local new_secrets="$1"
    local added=0
    local changed=0
    local unchanged=0
    local total=0
    local has_changes=false
    
    echo ""
    print_info "Comparing secrets..."
    echo ""
    
    # Build associative array of existing secrets
    declare -A existing_values
    while IFS=$'\t' read -r name value; do
        [[ -z "$name" ]] && continue
        existing_values["$name"]="$value"
    done < <(get_existing_secrets)
    
    # Compare each new secret
    while IFS=$'\t' read -r name value; do
        [[ -z "$name" ]] && continue
        ((total++))
        
        if [[ -z "${existing_values[$name]+x}" ]]; then
            # New secret
            print_secret_added "$name" "$value"
            ((added++))
            has_changes=true
        elif [[ "${existing_values[$name]}" != "$value" ]]; then
            # Changed secret
            print_secret_changed "$name" "$value"
            ((changed++))
            has_changes=true
        else
            # Unchanged
            print_secret_unchanged "$name" "$value"
            ((unchanged++))
        fi
    done <<< "$new_secrets"
    
    print_summary "$added" "$changed" "$total"
    
    # Return whether anything changed
    $has_changes
}

# ─────────────────────────────────────────────────────────────────────────────────
# Usage & Help
# ─────────────────────────────────────────────────────────────────────────────────
print_usage() {
    echo ""
    echo -e "${WHITE}${BOLD}Usage:${RESET} secrets [OPTIONS]"
    echo ""
    echo -e "${WHITE}${BOLD}Options:${RESET}"
    echo -e "  ${CYAN}-v, --verbose${RESET}    Show masked secret values"
    echo -e "  ${CYAN}-h, --help${RESET}       Show this help message"
    echo ""
    echo -e "${WHITE}${BOLD}Description:${RESET}"
    echo "  Syncs secrets from Bitwarden to ~/.secrets"
    echo "  Handles login, unlock, and vault sync automatically"
    echo ""
    echo -e "${WHITE}${BOLD}Setup:${RESET}"
    echo "  1. Create a Bitwarden item named 'dotfiles-secrets'"
    echo "  2. Add custom fields for each secret"
    echo "  3. Run: secrets"
    echo ""
}

# ─────────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────────
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                print_usage
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${RESET}"
                print_usage
                exit 1
                ;;
        esac
    done
    
    print_header
    
    # Check prerequisites
    check_bw_installed
    
    # Check vault status
    spinner_start "Checking vault status..."
    local status
    status=$(check_bw_status)
    spinner_stop true ""
    
    case "$status" in
        "unlocked")
            print_success "Vault is unlocked ${ICON_UNLOCK}"
            ;;
        "locked")
            print_warning "Vault is locked ${ICON_LOCK}"
            unlock_vault
            ;;
        "unauthenticated")
            print_warning "Not logged in"
            login_vault
            unlock_vault
            ;;
        *)
            error_exit "Unknown vault status: $status" \
                "Try running: bw status"
            ;;
    esac
    
    # Sync vault
    sync_vault
    
    # Fetch secrets
    local secrets
    secrets=$(fetch_secrets)
    
    # Compare and display changes
    if compare_and_display "$secrets"; then
        # Generate new file
        spinner_start "Writing secrets file..."
        generate_secrets_file "$secrets"
        spinner_stop true "Secrets file updated: ${SECRETS_FILE}"
    else
        print_info "No changes needed"
    fi
    
    echo ""
}

main "$@"
