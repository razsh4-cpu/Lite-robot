#!/usr/bin/env bash
# Run only with local/onsite access: this intentionally restarts networking.
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
    echo "Run as root" >&2
    exit 2
fi

readonly profile=RobotDawg5.0
readonly station=wlxc03a55d2991a
readonly ap_iface=wlxc23a55d2991a
readonly backup="/var/backups/lite3-network-$(date +%Y%m%d-%H%M%S)"

journalctl -k -b 0 --no-pager | grep -q "$station: renamed from wlan0"
journalctl -k -b 0 --no-pager | grep -q "$ap_iface: renamed from ap0"
nmcli -g NAME connection show "$profile" | grep -qx "$profile"

install -d -m 0700 "$backup"
cp -a /etc/NetworkManager/system-connections "$backup/"
cp -a /etc/NetworkManager/conf.d "$backup/"

cat > /etc/NetworkManager/conf.d/90-rtl8851bu-ap-unmanaged.conf <<EOF
[keyfile]
unmanaged-devices=interface-name:${ap_iface}
EOF

nmcli connection modify "$profile" \
    connection.interface-name "$station" \
    802-11-wireless.powersave 2 \
    802-11-wireless.mac-address-randomization 1 \
    802-11-wireless.cloned-mac-address permanent \
    ipv4.method manual \
    ipv4.addresses 192.168.2.32/24 \
    ipv4.gateway 192.168.2.1 \
    ipv4.dns 192.168.2.1

systemctl restart NetworkManager.service
sleep 3
nmcli connection up "$profile" ifname "$station"

echo "RTL8851BU STATION/AP NETWORK FIX APPLIED"
echo "Backup: $backup"
echo "Expected management IP: 192.168.2.32"
