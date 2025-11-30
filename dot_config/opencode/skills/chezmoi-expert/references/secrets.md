# Managing Secrets Securely

This guide covers secure secret management in chezmoi using password managers and encryption.

## Password Manager Integration

chezmoi provides built-in template functions for major password managers. Secrets are retrieved at apply time, never stored in the repository.

### 1Password

```go
{{/* Read specific field by reference */}}
{{ onepasswordRead "op://Personal/GitHub/token" }}
{{ onepasswordRead "op://Work/AWS/access_key_id" }}

{{/* Get entire item as JSON object */}}
{{ $github := onepassword "GitHub" }}
{{ $github.password }}
{{ $github.username }}

{{/* Access custom fields */}}
{{ $item := onepassword "MyService" }}
{{ $item.fields.api_key }}

{{/* Get document content */}}
{{ onepasswordDocument "SSH-Key" }}
{{ onepasswordDocument "SSL-Certificate" }}

{{/* Specify account */}}
{{ onepasswordRead "op://Personal/item/field" "my.1password.com" }}
```

**Setup**:
```bash
# Install 1Password CLI
brew install --cask 1password-cli

# Sign in
op signin

# Configure in chezmoi (optional)
[onepassword]
  command = "op"
```

### Bitwarden

```go
{{/* Get item */}}
{{ $item := bitwarden "item" "GitHub" }}
{{ $item.login.password }}
{{ $item.login.username }}

{{/* Get notes */}}
{{ (bitwarden "item" "SSH-Key").notes }}

{{/* Get custom fields */}}
{{ $item := bitwarden "item" "MyApp" }}
{{ range $item.fields }}
  {{ if eq .name "api_key" }}{{ .value }}{{ end }}
{{ end }}

{{/* Get attachment */}}
{{ bitwardenAttachment "filename.txt" "ItemName" }}
```

**Setup**:
```bash
# Install Bitwarden CLI
brew install bitwarden-cli

# Login
bw login

# Unlock session
bw unlock

# Set session key
export BW_SESSION="session_key"
```

### Pass (password-store)

```go
{{/* Get password */}}
{{ pass "github/token" }}
{{ pass "work/aws/access_key" }}

{{/* Get specific field */}}
{{ passFields "service/credentials" }}
{{ (passFields "github/api").api_key }}
```

**Setup**:
```bash
# Install pass
brew install pass

# Initialize store
pass init "GPG-KEY-ID"
```

### LastPass

```go
{{/* Get password */}}
{{ (lastpass "GitHub").password }}
{{ (lastpass "AWS").username }}

{{/* Get note */}}
{{ (lastpass "SSH-Key").note }}

{{/* Raw output */}}
{{ lastpassRaw "ItemName" }}
```

**Setup**:
```bash
# Install LastPass CLI
brew install lastpass-cli

# Login
lpass login username@example.com
```

### HashiCorp Vault

```go
{{/* Read secret */}}
{{ $secret := vault "secret/data/github" }}
{{ $secret.data.token }}
{{ $secret.data.username }}

{{/* Different mount points */}}
{{ $db := vault "database/creds/readonly" }}
{{ $db.username }}
{{ $db.password }}
```

**Setup**:
```bash
# Install Vault
brew install vault

# Set address
export VAULT_ADDR='https://vault.example.com'

# Authenticate
vault login
```

**Configure in chezmoi**:
```toml
[vault]
  command = "vault"
```

## File Encryption

For files that must be stored in the repository, use encryption.

### Age Encryption

**Initial Setup**:
```bash
# Generate encryption key
chezmoi age decrypt --generate > ~/.config/chezmoi/key.txt

# Get recipient (public key)
age-keygen -y ~/.config/chezmoi/key.txt
# age1abcd1234...
```

**Configure**:
```toml
# ~/.config/chezmoi/chezmoi.toml
encryption = "age"
[age]
  identity = "~/.config/chezmoi/key.txt"
  recipient = "age1abcd1234..."  # Public key from above
```

**Add Encrypted Files**:
```bash
# Add new encrypted file
chezmoi add --encrypt ~/.ssh/id_rsa

# Convert existing to encrypted
chezmoi chattr +encrypted ~/.netrc

# File will be named: encrypted_private_dot_ssh/encrypted_private_id_rsa.age
```

**Edit Encrypted Files**:
```bash
# chezmoi decrypts automatically
chezmoi edit ~/.ssh/id_rsa

# Apply decrypts and sets correct permissions
chezmoi apply
```

### GPG Encryption

**Configure**:
```toml
# ~/.config/chezmoi/chezmoi.toml
encryption = "gpg"
[gpg]
  recipient = "your-email@example.com"
  # Or use key ID
  recipient = "ABCD1234"
  
  # Multiple recipients
  recipient = ["email1@example.com", "email2@example.com"]
  
  # Symmetric encryption (password-based)
  symmetric = true
```

**Add Encrypted Files**:
```bash
# Add encrypted file
chezmoi add --encrypt ~/.netrc

# File will be named: encrypted_dot_netrc.asc
```

**Best Practices**:
- Keep GPG key secure and backed up
- Use long, strong passphrase
- Consider using a subkey for encryption

## Combining Encryption and Templates

Encrypt template files to include machine-specific secrets:

```bash
# Add encrypted template
chezmoi add --encrypt --template ~/.aws/credentials
```

**File**: `encrypted_dot_aws/encrypted_credentials.tmpl.asc`

**Content** (before encryption):
```ini
[default]
aws_access_key_id = {{ onepasswordRead "op://Work/AWS/access_key_id" }}
aws_secret_access_key = {{ onepasswordRead "op://Work/AWS/secret_access_key" }}
region = {{ .aws.region }}
```

## Secret Storage Best Practices

### 1. Never Commit Plaintext Secrets

```bash
# ❌ BAD: Plaintext secret in repository
echo "SECRET_TOKEN=abc123" > .env
chezmoi add .env

# ✅ GOOD: Encrypted
chezmoi add --encrypt .env

# ✅ BETTER: Reference from password manager
# In .env.tmpl
SECRET_TOKEN={{ onepasswordRead "op://vault/app/token" }}
```

### 2. Use .chezmoiignore for Local Config

```bash
# .chezmoiignore
.chezmoi.toml  # If it contains secrets
```

Then set secrets in each machine's local config:
```toml
# ~/.config/chezmoi/chezmoi.toml (not in repo)
[data.secrets]
  api_key = "local_secret"
```

### 3. Separate Secret Data from Templates

**Good pattern**:
```toml
# .chezmoi.toml.tmpl (committed)
[data]
  api_endpoint = "https://api.example.com"
  # Secret referenced, not stored
  api_key = {{ onepasswordRead "op://vault/api/key" | quote }}
```

**Alternative pattern**:
```toml
# .chezmoidata.toml (committed)
api_endpoint = "https://api.example.com"

# ~/.config/chezmoi/chezmoi.toml (local only, ignored)
[data]
  api_key = "secret_value"
```

### 4. Audit Repository for Secrets

```bash
# Search for potential secrets before committing
chezmoi cd
git log -p | grep -i "password\|secret\|token\|key"

# Use tools like gitleaks or trufflehog
gitleaks detect --source .
```

### 5. Rotate Secrets

When secrets are compromised:
```bash
# 1. Update secret in password manager
op item edit "GitHub" token="new_token"

# 2. Re-apply to update local files
chezmoi apply

# 3. For encrypted files, edit and re-encrypt
chezmoi edit ~/.netrc
# Saves automatically encrypted
```

## Common Patterns

### Environment Variables

```bash
# dot_zshrc.tmpl
{{ if lookPath "op" -}}
export GITHUB_TOKEN="{{ onepasswordRead "op://Personal/GitHub/token" }}"
{{ end -}}
```

### SSH Keys

```bash
# Encrypted private key
chezmoi add --encrypt ~/.ssh/id_rsa

# Public key (no encryption needed)
chezmoi add ~/.ssh/id_rsa.pub

# SSH config with secrets
# private_dot_ssh/config.tmpl
Host github.com
  User git
  IdentityFile ~/.ssh/id_rsa
  {{ if eq .machine_class "work" -}}
  ProxyCommand nc -X connect -x {{ onepasswordRead "op://Work/Proxy/host" }} %h %p
  {{ end -}}
```

### API Credentials

```bash
# encrypted_dot_config/app/credentials.toml.tmpl
[github]
token = "{{ onepasswordRead "op://Personal/GitHub/token" }}"

[aws]
access_key = "{{ onepasswordRead "op://Work/AWS/access_key_id" }}"
secret_key = "{{ onepasswordRead "op://Work/AWS/secret_access_key" }}"
region = "{{ .aws.region }}"
```

### Database Credentials

```bash
# encrypted_dot_env.tmpl
DATABASE_URL="postgresql://{{ (vault "database/creds/app").username }}:{{ (vault "database/creds/app").password }}@localhost/mydb"
```

## Troubleshooting

### Password Manager Not Found

```bash
# Error: executable file not found
# Solution: Install and configure password manager CLI

# Check if command exists
which op    # 1Password
which bw    # Bitwarden
which pass  # pass

# Check if authenticated
op account list
bw unlock
```

### Decryption Fails

```bash
# Error: failed to decrypt
# Solution: Check encryption key/recipient

# For age:
cat ~/.config/chezmoi/key.txt  # Verify identity exists
chezmoi doctor                 # Check configuration

# For GPG:
gpg --list-secret-keys        # Verify key exists
```

### Permission Issues

```bash
# Error: permission denied
# Solution: Ensure proper file permissions

# Age key should be private
chmod 600 ~/.config/chezmoi/key.txt

# SSH keys should be private
chmod 600 ~/.ssh/id_rsa
```

## Migration Strategies

### From Plaintext to Encrypted

```bash
# 1. Add to password manager
op item create --category login \
  --title "GitHub" \
  token="current_plaintext_value"

# 2. Convert template to use password manager
chezmoi edit ~/.gitconfig  # Remove plaintext, add template function

# 3. Remove plaintext from history (if already committed)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch sensitive_file" \
  --prune-empty --tag-name-filter cat -- --all
```

### From Password Manager to Encryption

```bash
# If password manager becomes unavailable
# 1. Get current value
CURRENT_VALUE=$(chezmoi execute-template '{{ onepasswordRead "op://vault/item" }}')

# 2. Create encrypted file
echo "$CURRENT_VALUE" | chezmoi add --encrypt /path/to/file

# 3. Update templates to reference file instead
```
