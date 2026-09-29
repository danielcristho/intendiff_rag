"""Guard that sample analysis runs in a container started with --network none."""
import sys
from pathlib import Path

NET = Path("/sys/class/net")


# network_interfaces lists interfaces other than loopback; --network none leaves none.
def network_interfaces(net=NET):
    if not net.exists():
        return []
    return sorted(entry.name for entry in net.iterdir() if entry.name != "lo")


def require_offline(net=NET):
    found = network_interfaces(net)
    if found:
        sys.exit(f"refusing to analyse samples with network interfaces {found}; "
                 "run this step through its make target (docker --network none)")
