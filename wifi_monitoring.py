import json
import os
import subprocess
import time
from colorama import init, Fore
from scapy.all import *
# from send_toast import ToastMessage
from threading import Thread


NETWORK = "192.168.1.1"
INTERVAL = 10

UNKNOWN = Fore.RED  # "\033[1;37;41m"
CONNECTED = Fore.GREEN  # "\033[1;32;49m"
DISCONNECTED = Fore.RESET  # "\033[1;33;49m"
RESET = Fore.RESET  # "\033[1;39;49m"


class NetworkMonitor:

    def __init__(self):
        self.devices = self.get_devices()

    def get_devices(self):
        with open("network_devices.json", "r") as fr:
            return json.loads(fr.read())

    def scan(self, ip):
        macs = set()
        arp_request = ARP(pdst=ip)
        broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request_broadcast = broadcast / arp_request
        answered_list = srp(arp_request_broadcast, timeout=1, verbose=False)[0]

        if answered_list and answered_list[0] and answered_list[0][0]:
            host = answered_list[0][0]
            net_id = {
                "ip address": host[0].psrc,
                "mac address": host[0].src
            }
            macs.add(json.dumps(net_id))

        for host in answered_list:
            if host[1].psrc != NETWORK:
                net_id = {
                    "ip address": host[1].psrc,
                    "mac address": host[1].src
                }
                macs.add(json.dumps(net_id))

        return macs

    def json_to_dict(self, json_data):
        return dict(json.loads(json_data))

    def connection_change(self, hosts, action, notify=False):
        if action not in ("Online", "Offline"):
            raise ValueError(f"invalid action: {action}")

        title = ""
        message = ""
        duration = 10  # seconds

        for host in hosts:
            host_mac = self.json_to_dict(host)["mac address"]
            host_ip = self.json_to_dict(host)["ip address"]

            if host_mac in [device["mac address"] for device in self.devices]:
                for device in self.devices:
                    if host_mac == device["mac address"]:
                        device["ip address"] = host_ip
                        device["status"] = action

                        # if action.lower() == "online":
                        #     title = f"Wi-Fi User"
                        #     message = f'{device["alias"]} is now {action}'

                        # persist notification for "Unknown Device"
                        if device["alias"].lower() == "unknown device" and action.lower() == "online":
                            title = f"* * * Unknown Wi-Fi User * * *"
                            message = f"Unknown Device is now {action}."
                            duration = 300  # 5mins
                            # self.send_notification(title, message, duration)
                            # os.system(f"say {message}")
                            # create a daemon thread that prevent unknown devices to have internet connection
                            self.stop_internet_connection(host_ip, host_mac)
                            title = ""
                            message = ""
            else:
                unknown_device = {
                    "mac address": host_mac,
                    "ip address": host_ip,
                    "alias": "Unknown Device",
                    "status": action
                }
                self.devices.append(unknown_device)
                title = f"* * * Unknown Wi-Fi User * * *"
                message = f"New Unknown Device detected."
                duration = 300  # 5mins

                # os.system(f"say {message}")
                # create a daemon thread that prevent unknown devices to have internet connection
                self.stop_internet_connection(host_ip, host_mac)

            # if notify and title and message:
            # self.send_notification(title, message, duration)

        self.show()

    def send_notification(self, title, message, duration=10):
        notification = ToastMessage()

        # if title and message:
        #     notif_thread = Thread(target=notification.send_toast, args=(title, message, duration,))
        #     notif_thread.setDaemon(True)
        #     notif_thread.start()

    def stop_internet_connection(self, target_ip, target_mac):

        def _prevent_connection():
            print(
                f"{Fore.LIGHTRED_EX} Preventing {target_ip} from accessing the internet...{RESET}\n")
            while True:
                # (by assigning host's ip address with invalid mac address)
                self.poison(target_ip, target_mac)
                time.sleep(0.5)

        kill_unknown_device_thread = Thread(target=_prevent_connection)
        kill_unknown_device_thread.setDaemon(True)
        kill_unknown_device_thread.start()

    def show(self):
        os.system("clear")
        print("\n")
        for device in sorted(self.devices, key=lambda device: device["status"], reverse=True):
            alias = device["alias"]
            mac = device["mac address"]
            ip = f'({device["ip address"] if device["ip address"] else "Undefined"})'
            status = device["status"]

            status_color = CONNECTED if status.lower() == "online" else DISCONNECTED
            if status.lower() == 'online' and alias.lower() == "unknown device":
                print(f"{UNKNOWN} {alias.ljust(20)} {mac.ljust(18)}" +
                      f"{status_color} {status}")
                print(f"{UNKNOWN} {ip.rjust(38)}  {RESET}")
                # create a daemon thread that prevent unknown devices to have internet connection
                self.stop_internet_connection(device["ip address"], mac)
                print("-" * 50)
            else:
                if status.lower() == "online":
                    print(
                        f"{status_color} {alias.ljust(20)} {RESET} {mac.ljust(18)} " + f"{status_color}{status}")
                    print(f"{status_color} {ip.rjust(38)}   {RESET}")
                    print("-" * 50)

    def poison(self, victim_ip, victim_mac):
        # Send the victim an ARP packet pairing the gateway ip with the wrong
        packet = ARP(op=2, psrc=victim_ip, hwsrc='12:34:56:78:9A:BG',
                     pdst=victim_ip, hwdst=victim_mac)
        sendp(packet, verbose=0)

    def restore(self, victim_ip, victim_mac, gateway_ip, gateway_mac):
        # Send the victim an ARP packet pairing the gateway ip with the correct
        # mac address
        packet = ARP(op=2, psrc=gateway_ip, hwsrc=gateway_mac,
                     pdst=victim_ip, hwdst=victim_mac)
        send(packet, verbose=0)

    def main(self):
        try:
            # autoreset color coding of texts to normal
            init(autoreset=True)

            old_macs = self.scan(f"{NETWORK}/24")
            self.connection_change(old_macs, "Online")
            time.sleep(INTERVAL)

            while True:
                macs = self.scan(f"{NETWORK}/24")
                new = macs - old_macs
                self.connection_change(new, "Online", notify=True)

                left = old_macs - macs
                self.connection_change(left, "Offline")

                time.sleep(INTERVAL)
                old_macs = macs

        except Exception as ex:
            print(f"Main Exception: {str(ex)}\n\nRestarting Wi-Fi Manager...")
            time.sleep(5)
            self.main()


if __name__ == "__main__":
    network_monitor = NetworkMonitor()
    network_monitor.main()
