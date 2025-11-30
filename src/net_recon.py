import socket
import logging
from typing import List, Tuple
from scapy.all import IP, ICMP, Ether, Raw
from scapy.packet import Packet

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def scan_ports(target: str, ports: List[int]) -> List[Tuple[int, bool]]:
    """
    Scans a list of ports on a target IP address using TCP Connect scan.

    Args:
        target (str): The target IP address or hostname.
        ports (List[int]): List of ports to scan.

    Returns:
        List[Tuple[int, bool]]: A list of tuples (port, is_open).
    """
    results = []
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((target, port))
        is_open = result == 0
        results.append((port, is_open))
        if is_open:
            logger.info(f"Port {port} is OPEN on {target}")
        else:
            logger.debug(f"Port {port} is CLOSED on {target}")
        sock.close()
    return results

def craft_icmp_packet(target_ip: str, message: str = "Echo Request") -> Packet:
    """
    Crafts a custom ICMP Echo Request packet using Scapy.

    Args:
        target_ip (str): The destination IP address.
        message (str): The payload message.

    Returns:
        Packet: The constructed Scapy packet.
    """
    # Constructing packet: IP Layer + ICMP Layer + Payload
    packet = IP(dst=target_ip) / ICMP() / Raw(load=message)
    logger.info(f"Crafted ICMP packet for {target_ip} with payload '{message}'")
    return packet

def summary_packet(packet: Packet) -> str:
    """Returns a summary string of the packet."""
    return packet.summary()
