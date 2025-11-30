import pytest
import os
import stat
from unittest.mock import patch, MagicMock
from src.system_lockdown import audit_open_ports, check_insecure_permissions

def test_audit_open_ports():
    """Test that open ports are detected."""
    # Mock psutil.net_connections
    with patch("psutil.net_connections") as mock_net:
        # Create a mock connection object
        mock_conn = MagicMock()
        mock_conn.status = "LISTEN"
        mock_conn.laddr.ip = "127.0.0.1"
        mock_conn.laddr.port = 8080
        mock_conn.pid = 1234

        mock_net.return_value = [mock_conn]

        with patch("psutil.Process") as mock_proc:
            mock_proc.return_value.name.return_value = "test_server"

            ports = audit_open_ports()
            assert len(ports) == 1
            assert ports[0]["port"] == "8080"
            assert ports[0]["process"] == "test_server"

def test_check_insecure_permissions(tmp_path):
    """Test that world-writable files are flagged."""
    # Create a secure file
    secure_file = tmp_path / "secure.txt"
    secure_file.write_text("secure")
    os.chmod(secure_file, 0o644) # rw-r--r--

    # Create an insecure file
    insecure_file = tmp_path / "insecure.txt"
    insecure_file.write_text("insecure")
    os.chmod(insecure_file, 0o666) # rw-rw-rw- (World Writable!)

    # Run check on tmp_path
    # Note: We need to convert tmp_path (Path object) to string
    insecure_files = check_insecure_permissions(str(tmp_path))

    # Should find exactly one insecure file
    assert len(insecure_files) == 1
    assert str(insecure_file) in insecure_files
