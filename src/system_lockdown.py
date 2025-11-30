import psutil
import os
import stat
from typing import List, Dict, Tuple

def audit_open_ports() -> List[Dict[str, str]]:
    """
    Lists all currently open ports on the system.

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing port info.
    """
    open_ports = []
    # Loop over all connections
    for conn in psutil.net_connections(kind='inet'):
        if conn.status == psutil.CONN_LISTEN:
            # We found a listening port
            port_info = {
                "ip": conn.laddr.ip,
                "port": str(conn.laddr.port),
                "pid": str(conn.pid) if conn.pid else "Unknown",
                "process": "Unknown"
            }

            # Try to get process name
            if conn.pid:
                try:
                    proc = psutil.Process(conn.pid)
                    port_info["process"] = proc.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            open_ports.append(port_info)
    return open_ports

def check_insecure_permissions(directory: str = ".") -> List[str]:
    """
    Scans a directory for world-writable files (security risk).

    Args:
        directory (str): The directory to scan.

    Returns:
        List[str]: A list of file paths that are world-writable.
    """
    insecure_files = []
    for root, dirs, files in os.walk(directory):
        # Skip virtual environment and git directories to reduce noise
        if ".venv" in root or ".git" in root or "__pycache__" in root:
            continue

        for name in files:
            filepath = os.path.join(root, name)
            try:
                st = os.stat(filepath)
                # Check if other (world) has write permission (S_IWOTH)
                if st.st_mode & stat.S_IWOTH:
                    insecure_files.append(filepath)
            except OSError:
                # Could not stat file, skip
                continue
    return insecure_files
