#!/usr/bin/env bash
set -u

section() { printf '\n[%s]\n' "$1"; }

section identity
date -Is
hostnamectl
printf 'boot_id='; cat /proc/sys/kernel/random/boot_id
printf 'uptime='; cat /proc/uptime
last -x --time-format iso | head -30
journalctl --list-boots --no-pager

section resources
cat /proc/loadavg
free -h
df -hT /
df -i /
cat /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io
ps -eo pid,ppid,stat,comm,%cpu,%mem,rss,etimes --sort=-%cpu | head -25

section thermal
for zone in /sys/class/thermal/thermal_zone*; do
    [[ -r "$zone/temp" ]] || continue
    printf '%s type=%s temp_mC=%s\n' "${zone##*/}" \
        "$(cat "$zone/type" 2>/dev/null)" "$(cat "$zone/temp")"
done

section storage
lsblk -o NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS
findmnt -no SOURCE,FSTYPE,OPTIONS /

section network
ip -brief address
ip -s link
ip route
nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device status 2>/dev/null || true
nmcli -t -f GENERAL.STATE,GENERAL.CONNECTION,IP4.ADDRESS,IP4.GATEWAY device show 2>/dev/null || true
cat /proc/net/wireless 2>/dev/null || true

section services
systemctl --no-pager --failed
systemctl show ssh.service -p ActiveState -p SubState -p NRestarts -p ExecMainStatus
systemctl show lite3-high-level-runtime.service lite3-lidar.service \
    lite3-localization.service lite3-nav2.service \
    -p Id -p ActiveState -p SubState -p NRestarts -p MemoryCurrent -p CPUUsageNSec

section current_kernel_priority
journalctl -k -b 0 -p warning..alert --no-pager -o short-iso | tail -300

section previous_kernel_priority
journalctl -k -b -1 -p warning..alert --no-pager -o short-iso | tail -500

section failure_signatures_all_boots
journalctl -b 0 --no-pager -o short-iso | \
    grep -Ei 'oom|out of memory|killed process|segfault|panic|watchdog|hung task|blocked for more than|thermal|thrott|overheat|mce|hardware error|i/o error|nvme|ext4.*error|read-only file system|wlp|wifi|disconnect|deauth|link is down|sshd.*(fail|error|maxstartups)' | tail -500

section previous_failure_signatures
journalctl -b -1 --no-pager -o short-iso | \
    grep -Ei 'oom|out of memory|killed process|segfault|panic|watchdog|hung task|blocked for more than|thermal|thrott|overheat|mce|hardware error|i/o error|nvme|ext4.*error|read-only file system|wlp|wifi|disconnect|deauth|link is down|sshd.*(fail|error|maxstartups)' | tail -500

section ssh_current
journalctl -b 0 -u ssh.service --no-pager -o short-iso | tail -200

section network_current
journalctl -b 0 -u NetworkManager.service --no-pager -o short-iso | tail -300
