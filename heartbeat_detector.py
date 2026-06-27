"""
Heartbeat detection engine
Combines WiFi scanning and signal processing to detect heartbeat patterns
"""

import numpy as np
from typing import Dict, List, Optional
from signal_processor import SignalProcessor
from wifi_scanner import WiFiScanner
import config
import time
from datetime import datetime
import json


class HeartbeatDetector:
    """Main heartbeat detection engine"""

    def __init__(self, sample_rate: int = config.SAMPLE_RATE):
        self.signal_processor = SignalProcessor(sample_rate)
        self.wifi_scanner = WiFiScanner()
        self.sample_rate = sample_rate
        self.bpm_history = []
        self.detection_history = []

    def detect_on_network(self, ssid: str, duration: int = config.DEFAULT_DURATION,
                         sensitivity: float = 0.7) -> Dict:
        """Detect heartbeat on a specific WiFi network
        
        Args:
            ssid: Target WiFi network SSID
            duration: Detection duration in seconds
            sensitivity: Sensitivity level (0.0-1.0)
            
        Returns:
            Detection results with BPM, confidence, etc.
        """
        print(f"\n📡 Starting heartbeat detection on '{ssid}'...")
        print(f"Duration: {duration}s | Sample rate: {self.sample_rate} Hz")
        print(f"Sensitivity: {sensitivity:.1%}\n")

        # Collect RSSI samples
        print("Collecting RSSI samples...")
        rssi_values = self.wifi_scanner.get_rssi_for_network(ssid, duration)

        if not rssi_values:
            return {
                'success': False,
                'error': f'No RSSI data collected for network "{ssid}"',
                'timestamp': datetime.now().isoformat()
            }

        print(f"✓ Collected {len(rssi_values)} RSSI samples\n")

        # Adjust detection sensitivity
        adjusted_confidence_threshold = config.CONFIDENCE_THRESHOLD * (2 - sensitivity)

        # Analyze signal
        print("Analyzing signal...")
        rssi_array = np.array(rssi_values)

        # Detect heartbeat
        heartbeat_result = self.signal_processor.detect_heartbeat_frequency(rssi_array)

        # Detect breathing (as reference)
        breathing_result = self.signal_processor.detect_breathing(rssi_array)

        # Signal quality assessment
        quality = self.signal_processor.analyze_signal_quality(rssi_array)

        # Build results
        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'network': ssid,
            'duration': duration,
            'samples_collected': len(rssi_values),
            'sample_rate': self.sample_rate,
            'sensitivity': sensitivity,
            'signal_quality': quality,
        }

        # Heartbeat detection
        if heartbeat_result['detected']:
            frequency = heartbeat_result['frequency']
            bpm = self.signal_processor.frequency_to_bpm(frequency)
            self.bpm_history.append(bpm)

            result['heartbeat'] = {
                'detected': True,
                'frequency_hz': float(frequency),
                'bpm': float(bpm),
                'confidence': float(heartbeat_result['confidence']),
                'snr': float(heartbeat_result['snr']),
                'magnitude': float(heartbeat_result['magnitude'])
            }

            # Calculate average BPM from recent history
            if len(self.bpm_history) > 1:
                smoothed_bpm = self.signal_processor.smooth_bpm(
                    self.bpm_history,
                    window_size=min(5, len(self.bpm_history))
                )
                result['heartbeat']['smoothed_bpm'] = float(smoothed_bpm)
        else:
            result['heartbeat'] = {
                'detected': False,
                'confidence': 0.0
            }

        # Breathing detection
        if breathing_result['detected']:
            result['breathing'] = {
                'detected': True,
                'frequency_hz': float(breathing_result['frequency']),
                'breaths_per_minute': float(breathing_result['breaths_per_minute']),
                'confidence': float(breathing_result['confidence'])
            }
        else:
            result['breathing'] = {'detected': False}

        # Store detection history
        self.detection_history.append(result)

        return result

    def continuous_detection(self, ssid: str, interval: int = 30,
                            max_duration: Optional[int] = None) -> List[Dict]:
        """Run continuous heartbeat detection
        
        Args:
            ssid: Target WiFi network
            interval: Detection interval in seconds
            max_duration: Maximum total duration (None = unlimited)
            
        Returns:
            List of detection results over time
        """
        results = []
        start_time = time.time()

        try:
            iteration = 0
            while True:
                if max_duration and (time.time() - start_time) > max_duration:
                    break

                iteration += 1
                print(f"\n--- Detection Run #{iteration} ({datetime.now().strftime('%H:%M:%S')}) ---")

                result = self.detect_on_network(ssid, duration=interval)
                results.append(result)

                # Display results
                if result['success'] and result['heartbeat']['detected']:
                    bpm = result['heartbeat']['bpm']
                    confidence = result['heartbeat']['confidence']
                    print(f"❤️  Heartbeat: {bpm:.1f} BPM (confidence: {confidence:.1%})")
                else:
                    print("❌ No heartbeat detected")

                # Wait before next detection
                if max_duration and (time.time() - start_time) < max_duration:
                    print(f"Waiting {interval}s for next detection...")
                    time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\nDetection stopped by user.")

        return results

    def batch_analysis(self, rssi_file: str) -> Dict:
        """Analyze RSSI data from a file
        
        Args:
            rssi_file: Path to CSV file with RSSI data
            
        Returns:
            Analysis results
        """
        try:
            rssi_values = np.loadtxt(rssi_file, delimiter=',')
        except Exception as e:
            return {'error': f'Failed to load file: {e}'}

        rssi_array = np.array(rssi_values)
        heartbeat_result = self.signal_processor.detect_heartbeat_frequency(rssi_array)
        quality = self.signal_processor.analyze_signal_quality(rssi_array)

        return {
            'file': rssi_file,
            'samples': len(rssi_values),
            'heartbeat': heartbeat_result,
            'quality': quality
        }

    def get_statistics(self) -> Dict:
        """Get statistics from detection history
        
        Returns:
            Statistics summary
        """
        if not self.bpm_history:
            return {'message': 'No detection history'}

        bpm_array = np.array(self.bpm_history)
        return {
            'total_detections': len(self.detection_history),
            'successful_detections': sum(
                1 for d in self.detection_history if d.get('heartbeat', {}).get('detected')
            ),
            'bpm_statistics': {
                'mean': float(np.mean(bpm_array)),
                'std': float(np.std(bpm_array)),
                'min': float(np.min(bpm_array)),
                'max': float(np.max(bpm_array)),
                'median': float(np.median(bpm_array))
            },
            'history': self.bpm_history[-20:]  # Last 20 measurements
        }
