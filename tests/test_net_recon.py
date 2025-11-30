import pytest
from unittest.mock import patch, MagicMock
from src.net_recon import scan_ports, craft_icmp_packet, summary_packet
from scapy.all import IP, ICMP

def test_scan_ports_open():
    """Test the port scanner with a mocked open port."""
    with patch("socket.socket") as mock_socket:
        mock_instance = mock_socket.return_value
        # connect_ex returns 0 for success (open port)
        mock_instance.connect_ex.return_value = 0

        results = scan_ports("127.0.0.1", [80])

        assert len(results) == 1
        assert results[0] == (80, True)
        mock_instance.connect_ex.assert_called_with(("127.0.0.1", 80))

def test_scan_ports_closed():
    """Test the port scanner with a mocked closed port."""
    with patch("socket.socket") as mock_socket:
        mock_instance = mock_socket.return_value
        # connect_ex returns 111 (or any non-zero) for connection refused
        mock_instance.connect_ex.return_value = 111

        results = scan_ports("127.0.0.1", [22])

        assert len(results) == 1
        assert results[0] == (22, False)

def test_craft_icmp_packet():
    """Test that Scapy correctly constructs a packet."""
    target = "192.168.1.1"
    msg = "TestPayload"
    pkt = craft_icmp_packet(target, msg)

    # Verify layers
    assert pkt.haslayer(IP)
    assert pkt.haslayer(ICMP)
    assert pkt[IP].dst == target
    assert msg.encode() in pkt.load if hasattr(pkt, 'load') else True

def test_packet_summary():
    """Test the packet summary function."""
    pkt = IP(dst="8.8.8.8") / ICMP()
    summary = summary_packet(pkt)
    assert "8.8.8.8" in summary
    assert "ICMP" in summary
