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

    def _parse_iw_output(self, output: str) -> List[Dict]:
        """Parse iw scan output"""
        networks = []
        current_network = {}

        for line in output.split('\n'):
            line = line.strip()

            if line.startswith('BSS '):
                if current_network:
                    networks.append(current_network)
                current_network = {'bssid': line.split()[1]}

            elif 'SSID:' in line:
                current_network['ssid'] = line.split('SSID: ')[1]

            elif 'signal:' in line:
                try:
                    signal = int(line.split('signal:')[1].split()[0])
                    current_network['signal'] = signal
                except:
                    pass

            elif 'Frequency:' in line:
                try:
                    freq = float(line.split('Frequency:')[1].split()[0])
                    current_network['frequency'] = freq
                except:
                    pass

        if current_network:
            networks.append(current_network)

        return networks

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
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 7:
                        try:
                            network = {
                                'bssid': parts[0],
                                'ssid': parts[1],
                                'signal': int(parts[2]),
                                'channel': int(parts[3]),
                                'ht': parts[4],
                                'cc': parts[5],
                                'security': ' '.join(parts[6:]) if len(parts) > 6 else 'Open'
                            }
                            networks.append(network)
                        except:
                            pass
        except Exception as e:
            print(f"macOS scan failed: {e}")

        return networks

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
            print(f"Windows scan failed: {e}")

        return networks

    def _parse_netsh_output(self, output: str) -> List[Dict]:
        """Parse netsh WiFi output - handles Windows format with SSID # and nested BSSIDs"""
        networks = []
        seen_ssids = {}  # Track SSIDs and their best signal strength
        
        lines = output.split('\n')
        current_ssid = None
        
        for line in lines:
            line_stripped = line.strip()
            
            # Look for "SSID X :" pattern
            ssid_match = re.match(r'SSID\s+\d+\s*:\s*(.+)', line_stripped)
            if ssid_match:
                current_ssid = ssid_match.group(1).strip()
                if current_ssid:
                    seen_ssids[current_ssid] = {'ssid': current_ssid, 'signal': -100, 'bssid': 'N/A', 'channel': 'N/A'}
            
            # Look for "Signal             : XX%"
            if 'Signal' in line and '%' in line and current_ssid:
                signal_match = re.search(r'(\d+)\s*%', line)
                if signal_match:
                    signal_percent = int(signal_match.group(1))
                    signal_dbm = -100 + (signal_percent / 2)
                    
                    # Store the best (highest) signal for this SSID
                    if signal_dbm > seen_ssids[current_ssid]['signal']:
                        seen_ssids[current_ssid]['signal'] = signal_dbm
                        seen_ssids[current_ssid]['signal_percent'] = signal_percent
            
            # Look for BSSID
            if 'BSSID' in line and ':' in line and not line.startswith('    '):
                bssid_match = re.search(r'([0-9a-f]{2}(?::[0-9a-f]{2}){5})', line, re.IGNORECASE)
                if bssid_match and current_ssid:
                    seen_ssids[current_ssid]['bssid'] = bssid_match.group(1)
            
            # Look for Channel
            if 'Channel' in line and ':' in line and current_ssid:
                channel_match = re.search(r'Channel\s*:\s*(\d+)', line)
                if channel_match:
                    seen_ssids[current_ssid]['channel'] = int(channel_match.group(1))
        
        # Convert to list and sort by signal strength
        networks = list(seen_ssids.values())
        networks.sort(key=lambda x: x['signal'], reverse=True)
        
        return networks

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
                        return {'ssid': line.split('ESSID:')[1].strip('"')}

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
            print(f"Error getting connected network: {e}")

        return None

    def get_rssi_for_network(self, ssid: str, duration: int = 10, sample_interval: float = 0.1) -> List[float]:
        """Continuously monitor RSSI for a specific network
        
        Args:
            ssid: Network SSID to monitor
            duration: Duration to monitor in seconds
            sample_interval: Time between samples in seconds
            
        Returns:
            List of RSSI values (dBm)
        """
        rssi_values = []
        start_time = time.time()
        sample_count = 0
        
        print(f"📡 Scanning for network '{ssid}' for {duration} seconds...")
        
        while time.time() - start_time < duration:
            try:
                networks = self.scan()
                
                # Find matching network
                for network in networks:
                    if network.get('ssid') == ssid:
                        rssi = network.get('signal')
                        if rssi is not None and rssi != 0 and rssi < 0:  # Valid RSSI should be negative
                            rssi_values.append(rssi)
                            sample_count += 1
                            
                            # Print progress every 10 samples
                            if sample_count % 10 == 0:
                                print(f"  ✓ Collected {len(rssi_values)} samples (Signal: {rssi:.1f} dBm)")
                        break
                
            except Exception as e:
                print(f"Error scanning: {e}")

            time.sleep(sample_interval)
        
        print(f"✓ Collection complete: {len(rssi_values)} valid RSSI samples collected\n")
        
        return rssi_values
