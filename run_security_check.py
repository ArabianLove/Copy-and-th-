from src.system_lockdown import audit_open_ports, check_insecure_permissions

def print_security_report():
    print("=== SECURITY STATUS REPORT ===")
    print("\n[+] Checking Open Ports...")
    ports = audit_open_ports()
    if not ports:
        print("    No listening ports found. (Stealth Mode: ON)")
    else:
        for p in ports:
            print(f"    ALERT: Port {p['port']} is OPEN on {p['ip']} (PID: {p['pid']}, Proc: {p['process']})")

    print("\n[+] Checking File Permissions...")
    insecure = check_insecure_permissions(".")
    if not insecure:
        print("    No insecure (world-writable) files found.")
    else:
        for f in insecure:
            print(f"    WARNING: World-writable file found: {f}")

    print("\n=== END REPORT ===")

if __name__ == "__main__":
    print_security_report()
