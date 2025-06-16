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

You can execute this in proxmox
```sh
helvetic_lxc.sh
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

