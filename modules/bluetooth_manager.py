import subprocess
import os
import time

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def bluetooth_on():
    print(run_cmd("bluetoothctl power on"))

def bluetooth_off():
    print(run_cmd("bluetoothctl power off"))

def check_adapter():
    output = run_cmd("bluetoothctl show")
    if "Powered: no" in output:
        print("Bluetooth is off. Turning it on...")
        bluetooth_on()
    elif "Powered: yes" in output:
        print("Bluetooth is on.")
    else:
        print("No Bluetooth adapter found or not supported.")

def scan_on(duration=10):
    print(f"🔍 Scanning for devices for {duration} seconds...\n")
    process = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    process.stdin.write("scan on\n")
    process.stdin.flush()

    try:
        for _ in range(duration):
            line = process.stdout.readline()
            if line:
                print(line.strip())
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        process.stdin.write("scan off\n")
        process.stdin.flush()
        process.stdin.close()
        process.terminate()
        print("\n✅ Scan completed.")

def scan_off():
    print(run_cmd("bluetoothctl scan off"))

def list_devices():
    output = run_cmd("bluetoothctl devices")
    print("📡 Discovered Devices:")
    print(output or "No devices found. Try scanning first.")

def list_paired():
    output = run_cmd("bluetoothctl paired-devices")
    print("🤝 Paired Devices:")
    print(output or "No devices paired.")

def pair_device():
    mac = input("🔗 Enter MAC address to pair: ").strip()
    print(f"Attempting to pair with {mac}...")

    process = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    process.stdin.write(f"pair {mac}\n")
    process.stdin.flush()
    time.sleep(5)

    for _ in range(10):
        line = process.stdout.readline()
        if not line:
            break
        print(line.strip())
        if "Pairing successful" in line:
            print("✅ Pairing successful!")
            break
        elif "Failed" in line:
            print("❌ Pairing failed.")
            break

    process.stdin.close()
    process.terminate()

def connect_device():
    mac = input("🔌 Enter MAC address to connect: ").strip()
    print(run_cmd(f"bluetoothctl connect {mac}"))

def disconnect_device():
    mac = input("❌ Enter MAC address to disconnect: ").strip()
    print(run_cmd(f"bluetoothctl disconnect {mac}"))

def trust_device():
    mac = input("✅ Enter MAC address to trust: ").strip()
    print(run_cmd(f"bluetoothctl trust {mac}"))

def untrust_device():
    mac = input("🚫 Enter MAC address to untrust: ").strip()
    print(run_cmd(f"bluetoothctl untrust {mac}"))

def remove_device():
    mac = input("🗑️ Enter MAC address to remove: ").strip()
    print(run_cmd(f"bluetoothctl remove {mac}"))

def make_discoverable():
    print(run_cmd("bluetoothctl discoverable on"))

def make_non_discoverable():
    print(run_cmd("bluetoothctl discoverable off"))

def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")

def menu():
    check_adapter()
    while True:
        clear_screen()
        print("=== 🧿 Bluetooth Manager ===")
        print("1. Power ON Bluetooth")
        print("2. Power OFF Bluetooth")
        print("3. Scan for Devices")
        print("4. Stop Scan")
        print("5. List Available Devices")
        print("6. List Paired Devices")
        print("7. Pair Device")
        print("8. Connect Device")
        print("9. Disconnect Device")
        print("10. Trust Device")
        print("11. Untrust Device")
        print("12. Remove Device")
        print("13. Make Discoverable")
        print("14. Make Non-Discoverable")
        print("0. Exit")
        choice = input("\nEnter your choice: ").strip()

        if choice == "1": bluetooth_on()
        elif choice == "2": bluetooth_off()
        elif choice == "3": scan_on()
        elif choice == "4": scan_off()
        elif choice == "5": list_devices()
        elif choice == "6": list_paired()
        elif choice == "7": pair_device()
        elif choice == "8": connect_device()
        elif choice == "9": disconnect_device()
        elif choice == "10": trust_device()
        elif choice == "11": untrust_device()
        elif choice == "12": remove_device()
        elif choice == "13": make_discoverable()
        elif choice == "14": make_non_discoverable()
        elif choice == "0":
            print("👋 Exiting Bluetooth Manager.")
            break
        else:
            print("Invalid choice. Try again.")

        input("\nPress Enter to continue...")

if __name__ == "__main__":
    menu()

