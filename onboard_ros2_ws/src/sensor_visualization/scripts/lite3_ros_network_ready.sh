#!/usr/bin/env bash
set -eo pipefail

# NetworkManager's online target can fire in the same scheduling instant in
# which interfaces become usable. Wait for one routable host interface, then
# give DDS a stable-interface window before constructing participants. Robot
# Ethernet is deliberately not mandatory here: LiDAR/localization startup must
# not be permanently blocked when the physical robot is powered after the PC.
timeout 45 nm-online -s -q
for _ in $(seq 1 40); do
    if ip -4 -o addr show up scope global | grep -q 'inet ' && \
       ip -4 route show default | grep -q '^default '; then
        sleep 5
        echo 'Lite3 ROS network ready: routable interface stable'
        if ip route get 192.168.1.120 2>/dev/null | grep -q 'dev eno1'; then
            echo 'Lite3 robot route available via eno1'
        else
            echo 'Lite3 robot route not yet available; robot runtime will wait safely'
        fi
        exit 0
    fi
    sleep 1
done
echo 'Lite3 ROS network not ready: no stable routable interface' >&2
exit 1
