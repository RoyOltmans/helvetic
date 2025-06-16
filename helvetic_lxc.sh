#!/bin/bash
set -e

# ---- CONFIGURATION ----
LXC_ID=125
LXC_NAME="example-container"
LXC_HOSTNAME="example-container"
TEMPLATE_STORAGE="local"
ROOTFS_STORAGE="local-zfs"
ROOTFS_SIZE="4"                          # In GB
LXC_IP="10.0.0.25/24"
LXC_GATEWAY="10.0.0.1"
LXC_DNS="10.0.0.2"
LXC_DNS_SEARCH="lan.example"
LXC_MAC="AA:BB:CC:11:22:33"
LXC_BRIDGE="vmbr0"
LXC_CPU="1"
LXC_MEM="512"
LXC_PWD="example_password"

# ---- 1. Find latest Debian 12 template ----
LXC_TEMPLATE=$(pveam available | awk '/debian-12-standard/ {print $2}' | sort -V | tail -n1)
if [[ -z "$LXC_TEMPLATE" ]]; then
    echo "No Debian 12 template found in Proxmox repositories!"
    exit 1
fi

# ---- 2. Download template if missing ----
if ! pveam list $TEMPLATE_STORAGE | grep -q "$LXC_TEMPLATE"; then
    echo "Downloading Debian template $LXC_TEMPLATE to $TEMPLATE_STORAGE..."
    pveam download $TEMPLATE_STORAGE $LXC_TEMPLATE
else
    echo "Template $LXC_TEMPLATE already present in $TEMPLATE_STORAGE."
fi

# ---- 3. Create the LXC container ----
if pct status $LXC_ID &>/dev/null; then
    echo "Container $LXC_ID already exists. Skipping creation."
else
    echo "Creating LXC $LXC_ID ($LXC_NAME)..."
    pct create $LXC_ID $TEMPLATE_STORAGE:vztmpl/$LXC_TEMPLATE \
        --hostname $LXC_HOSTNAME \
        --cores $LXC_CPU --memory $LXC_MEM \
        --net0 name=eth0,bridge=$LXC_BRIDGE,ip=$LXC_IP,gw=$LXC_GATEWAY,hwaddr=$LXC_MAC \
        --password $LXC_PWD \
        --rootfs $ROOTFS_STORAGE:$ROOTFS_SIZE \
        --features nesting=1 \
        --unprivileged 1 \
        --nameserver $LXC_DNS \
        --searchdomain $LXC_DNS_SEARCH
fi

# ---- 4. Start and wait for network ----
pct start $LXC_ID
echo "Waiting for network in LXC $LXC_ID..."
pct exec $LXC_ID -- bash -c "until ping -c1 1.1.1.1 >/dev/null 2>&1; do sleep 1; done"
echo "Network up in LXC $LXC_ID."

# ---- 5. (Optional) Set root password interactively after creation ----
echo "You can set the root password manually by running:"
echo "  pct passwd $LXC_ID"

# ---- 6. Provision helvetic and nginx ----
pct exec $LXC_ID -- bash -c "
set -e
apt-get update
apt-get install -y python3 python3-pip git nginx
pip3 install --break-system-packages bottle crcmod python-dotenv
git clone https://github.com/RoyOltmans/helvetic.git /opt/helvetic

cat >/etc/systemd/system/helvetic.service <<EOF
[Unit]
Description=Helvetic Testserver
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/helvetic/mvp/server.py 0.0.0.0 8000
WorkingDirectory=/opt/helvetic
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl enable helvetic
systemctl start helvetic

cat >/etc/nginx/sites-available/helvetic <<EONGX
server {
    listen 80 default_server;
    server_name _;
    location / {
        proxy_pass http://127.0.0.1:8000;
        mirror /mirror_fitbit;
        mirror_request_body on;
    }
    location = /mirror_fitbit {
        internal;
        proxy_pass http://api.fitbit.com\$request_uri;
        proxy_set_header Host api.fitbit.com;
    }
}
EONGX

ln -sf /etc/nginx/sites-available/helvetic /etc/nginx/sites-enabled/helvetic
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx
"

echo "======================================================"
echo "LXC $LXC_ID ($LXC_NAME) created and configured."
echo "IP address: $LXC_IP"
echo "Nginx is listening on port 80 (mirrors to Fitbit)."
echo "Helvetic testserver running on port 8000."
echo "Set password: pct passwd $LXC_ID"
echo "Enter: pct enter $LXC_ID"
echo "======================================================"
