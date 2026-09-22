# Version, Repair, and Updates

Display the installed release and verify managed files:

```bash
codynick-version
```

The report identifies the overall version, component versions, installation stage,
and any managed files that are modified, missing, or unexpected.

Use the same command for a supported first installation, upgrade, or repair:

```bash
wget -O /tmp/codynick-setup.sh https://raw.githubusercontent.com/Sohaware/rpi/main/setup.sh && sudo bash /tmp/codynick-setup.sh
```

Do not reboot while background installation is running. Follow its progress with:

```bash
sudo journalctl -fu codynick-install
```

Success ends with `CodyNick <version>: READY`.

