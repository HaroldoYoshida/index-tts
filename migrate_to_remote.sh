#!/bin/bash
# Migration Script: WSL to Remote Server 10.41.80.17
# User: vmadmin

set -e

REMOTE_HOST="10.41.80.17"
REMOTE_USER="vmadmin"
REMOTE_PASS="mudemeja"

echo "=== WSL to Remote Server Migration ==="
echo "Target: ${REMOTE_USER}@${REMOTE_HOST}"

# Step 1: Generate SSH key if not exists
if [ ! -f ~/.ssh/id_ed25519 ]; then
    echo "[1/6] Generating SSH key..."
    ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -C "vmadmin@wsl-migration"
else
    echo "[1/6] SSH key already exists"
fi

# Step 2: Copy SSH key to remote server
echo "[2/6] Copying SSH key to remote server..."
sshpass -p "${REMOTE_PASS}" ssh-copy-id -o StrictHostKeyChecking=no -i ~/.ssh/id_ed25519.pub ${REMOTE_USER}@${REMOTE_HOST}

# Step 3: Configure passwordless sudo on remote
echo "[3/6] Configuring passwordless sudo..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "echo '${REMOTE_PASS}' | sudo -S bash -c 'echo \"${REMOTE_USER} ALL=(ALL) NOPASSWD:ALL\" > /etc/sudoers.d/${REMOTE_USER}'"

# Step 4: Install Tailscale
echo "[4/6] Installing Tailscale on remote server..."
ssh ${REMOTE_USER}@${REMOTE_HOST} << 'TAILSCALE_INSTALL'
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --authkey=tskey-auth-kCXnqeWjiQ11CNTRL-Bp6FvN8CUBBGb21BWA8VBBTtuAUGAgga
TAILSCALE_INSTALL

# Step 5: Sync home directory
echo "[5/6] Syncing home directory to remote..."
rsync -avz --progress \
    --exclude='.cache' \
    --exclude='.local/share/Trash' \
    --exclude='node_modules' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.git/objects' \
    ~/ ${REMOTE_USER}@${REMOTE_HOST}:~/

# Step 6: Sync projects
echo "[6/6] Syncing projects..."
rsync -avz --progress \
    --exclude='node_modules' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.git/objects' \
    --exclude='*.pyc' \
    ~/projects/ ${REMOTE_USER}@${REMOTE_HOST}:~/projects/

echo ""
echo "=== Migration Complete ==="
echo "Connect with: ssh ${REMOTE_USER}@${REMOTE_HOST}"
echo "Tailscale should be active on the remote server"
