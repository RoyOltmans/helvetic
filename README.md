# helvetic

*helvetic* is an application that replaces the web service for the FitBit Aria.

The software is a work-in-progress, and runs as a Django application.  It also includes a bare-bones implementation of the protocol for testing, which uses bottle.py (and stores no data).

It requires local DNS spoofing in order to intercept requests originally bound for `fitbit.com`.

## Currently implemented

* Recording data
* Sending preferences and 1-2 user profiles to Aria
* Registering new device

## Partially implemented

* Viewing data (through Django Admin)
* Configuration manager (through Django Admin)
* Profile manager (through Django Admin)
* Sending more than 1 user profile to Aria

## Docker deployment for Django helv_test

In the root of the project:
```sh
docker-compose up -d --build
```
It includes a nginx for rerouting, never got that to work. For now working on LXC on proxmox

# Example Proxmox LXC Appliance Deployment

This script automates the creation and provisioning of a Debian-based LXC container on Proxmox, running a sample Python web application behind Nginx.

---

## Prerequisites

- **Proxmox VE host** (tested on Proxmox 7/8)
- **Root SSH access** or console access to your Proxmox node
- **Storage pools**:
  - `local` (for container templates)
  - `local-zfs` (default for rootfs; change in script if you use another pool)
- **Internet access** from your Proxmox host (for image and package downloads)
- **Sufficient disk space** (at least 4GB free on the target storage pool)

---

## What the Script Does

- Downloads the latest Debian 12 LXC template if needed
- Creates a new LXC container with static network settings, custom MAC, and hostname
- Installs Python, pip, git, nginx, and Python packages
- Clones a sample Python web app repository
- Sets up a systemd service and nginx reverse proxy for the app

---

## Quick Start

1. **Copy the script to your Proxmox host** (e.g. as `create_example_lxc.sh`).
2. **Make the script executable:**
   ```bash
   chmod +x helvetic_lxc.sh

You can execute this in proxmox
```sh
bash helvetic_lxc.sh
```

## Planned

* WiFi connection setup & complete registration flow
* Replacing bits that depend on Django Admin
* User management
* Data access
* Graphs

## See also

* `protocol.md` - Contains information about the FitBit Aria protocol (version 3)
* `firmware.md` - Notes on the firmware
* `gfit.md` - Plans/notes on implementing [Google Fit](https://fit.google.com) support

