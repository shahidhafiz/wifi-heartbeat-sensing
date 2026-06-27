"""
WiFi network scanning module
Detects available WiFi networks and their RSSI values
"""

import subprocess
import re
import platform
import os
from typing import List, Dict, Optional
import time
import warnings
import json

warnings.filterwarnings('ignore')


class WiFiScanner:
    """Handles WiFi network scanning across different platforms"""

    def __init__(self):
        self.system = platform.system()
        self.networks = []
        self.adapter = self._find_adapter()

    def _find_adapter(self) -> Optional[str]:
        """Find available WiFi adapter"""
        try:
            if self.system == 'Linux':
                result = subprocess.run(
                    ['ip', 'link', 'show'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                # Look for wireless interfaces
                for line in result.stdout.split('\n'):
                    if 'wlan' in line or 'wlp' in line:
                        return line.split(':')[1].strip()
                return 'wlan0'

            elif self.system == 'Darwin':  # macOS
                return 'en0'  # Usually the main interface

            elif self.system == 'Windows':
                return None  # Windows uses different method

        except Exception as e:
            print(f"Error finding adapter: {e}")
            return None

    def scan(self) -> List[Dict]:
        """Scan for available WiFi networks
        
        Returns:
            List of networks with SSID, BSSID, signal strength, etc.
        """
        if self.system == 'Linux':
            return self._scan_linux()
        elif self.system == 'Darwin':
            return self._scan_macos()
        elif self.system == 'Windows':
            return self._scan_windows()
        else:
            raise NotImplementedError(f"Scanning not supported on {self.system}")

    def _scan_linux(self) -> List[Dict]:
        """Scan WiFi on Linux using nmcli or iw"""
        networks = []
        
        try:
            # Try nmcli first (NetworkManager)
            result = subprocess.run(
                ['nmcli', 'dev', 'wifi', 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    # Parse nmcli output
                    for line in lines[1:]:
                        parts = line.split()
                        if len(parts) >= 7:
                            network = {
                                'ssid': parts[1],
                                'bssid': parts[0],
                                'mode': parts[2],
                                'channel': int(parts[3]),
                                'signal': int(parts[4]),
                                'bars': parts[5],
                                'security': ' '.join(parts[6:]) if len(parts) > 6 else 'Unknown'
                            }
                            networks.append(network)
        except Exception as e:
            print(f"nmcli scan failed: {e}")

        if not networks:
            # Fallback to iw command
            try:
                result = subprocess.run(
                    ['sudo', 'iw', self.adapter or 'wlan0', 'scan'],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                networks = self._parse_iw_output(result.stdout)
            except Exception as e:
                print(f"iw scan failed: {e}")

        return networks

    def _parse_iw_output(self, output: str) -> List[Dict]:\n        \"\"\"Parse iw scan output\"\"\"\n        networks = []\n        current_network = {}\n\n        for line in output.split('\n'):\n            line = line.strip()\n\n            if line.startswith('BSS '):\n                if current_network:\n                    networks.append(current_network)\n                current_network = {'bssid': line.split()[1]}\n\n            elif 'SSID:' in line:\n                current_network['ssid'] = line.split('SSID: ')[1]\n\n            elif 'signal:' in line:\n                try:\n                    signal = int(line.split('signal:')[1].split()[0])\n                    current_network['signal'] = signal\n                except:\n                    pass\n\n            elif 'Frequency:' in line:\n                try:\n                    freq = float(line.split('Frequency:')[1].split()[0])\n                    current_network['frequency'] = freq\n                except:\n                    pass\n\n        if current_network:\n            networks.append(current_network)\n\n        return networks

    def _scan_macos(self) -> List[Dict]:
        """Scan WiFi on macOS"""
        networks = []
        
        try:
            result = subprocess.run(
                ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/'
                 'Current/Resources/airport', '-s'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Skip header
                if line.strip():\n                    parts = line.split()\n                    if len(parts) >= 7:\n                        try:\n                            network = {\n                                'bssid': parts[0],\n                                'ssid': parts[1],\n                                'signal': int(parts[2]),\n                                'channel': int(parts[3]),\n                                'ht': parts[4],\n                                'cc': parts[5],\n                                'security': ' '.join(parts[6:]) if len(parts) > 6 else 'Open'\n                            }\n                            networks.append(network)\n                        except:\n                            pass
        except Exception as e:
            print(f\"macOS scan failed: {e}\")\n\n        return networks

    def _scan_windows(self) -> List[Dict]:
        """Scan WiFi on Windows using netsh with improved parsing"""
        networks = []
        
        try:
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'networks', 'mode=Bssid'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            networks = self._parse_netsh_output(result.stdout)
            
        except Exception as e:
            print(f\"Windows scan failed: {e}\")\n\n        return networks

    def _parse_netsh_output(self, output: str) -> List[Dict]:\n        \"\"\"Parse netsh WiFi output more robustly\"\"\"\n        networks = []\n        current_ssid = None\n        seen_ssids = set()\n\n        lines = output.split('\\n')\n        for i, line in enumerate(lines):\n            # Look for SSID line - handles both 'SSID' and 'SSID :' formats\n            if 'SSID' in line and ':' in line:\n                parts = line.split(':', 1)\n                if len(parts) > 1:\n                    ssid = parts[1].strip()\n                    # Filter out invalid SSIDs\n                    if ssid and ssid not in ['1', ''] and len(ssid) > 0:\n                        current_ssid = ssid\n\n            # Look for Signal line\n            if 'Signal' in line and '%' in line:\n                try:\n                    signal_match = re.search(r'(\\d+)\\s*%', line)\n                    if signal_match and current_ssid:\n                        signal_percent = int(signal_match.group(1))\n                        # Convert percentage to dBm (rough estimate)\n                        signal_dbm = -100 + (signal_percent / 2)\n                        \n                        # Avoid duplicates\n                        if current_ssid not in seen_ssids:\n                            networks.append({\n                                'ssid': current_ssid,\n                                'signal': signal_dbm,\n                                'signal_percent': signal_percent,\n                                'bssid': 'N/A',\n                                'channel': 'N/A'\n                            })\n                            seen_ssids.add(current_ssid)\n                except Exception as e:\n                    pass\n\n        return networks

    def get_connected_network(self) -> Optional[Dict]:
        """Get information about currently connected network"""
        try:
            if self.system == 'Linux':
                result = subprocess.run(
                    ['iwconfig'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                # Parse iwconfig output
                for line in result.stdout.split('\n'):
                    if 'ESSID' in line:
                        return {'ssid': line.split('ESSID:')[1].strip('\"')}

            elif self.system == 'Darwin':
                result = subprocess.run(
                    ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/'
                     'Current/Resources/airport', '-I'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                data = {}
                for line in result.stdout.split('\n'):
                    if ':' in line:
                        key, val = line.split(':', 1)
                        data[key.strip()] = val.strip()
                return data

            elif self.system == 'Windows':
                result = subprocess.run(
                    ['netsh', 'wlan', 'show', 'interfaces'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                data = {}
                for line in result.stdout.split('\n'):
                    if ':' in line:
                        key, val = line.split(':', 1)
                        data[key.strip()] = val.strip()
                return data
        except Exception as e:
            print(f\"Error getting connected network: {e}\")\n\n        return None

    def get_rssi_for_network(self, ssid: str, duration: int = 10) -> List[float]:
        """Continuously monitor RSSI for a specific network
        
        Args:
            ssid: Network SSID to monitor
            duration: Duration to monitor in seconds
            
        Returns:
            List of RSSI values (dBm)
        """
        rssi_values = []
        start_time = time.time()

        while time.time() - start_time < duration:
            try:
                networks = self.scan()
                for network in networks:
                    if network.get('ssid') == ssid or network.get('SSID') == ssid:
                        rssi = network.get('signal')
                        if rssi is not None:
                            rssi_values.append(rssi)
                        break
            except Exception as e:
                print(f\"Error scanning: {e}\")\n\n            time.sleep(0.1)  # Sample every 100ms\n\n        return rssi_values
