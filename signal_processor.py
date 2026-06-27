"""
Signal processing module for WiFi heartbeat detection
Handles filtering, FFT analysis, and frequency extraction
"""

import numpy as np
from scipy import signal, fft
from scipy.signal import find_peaks, butter, filtfilt
import config
from typing import Tuple, List, Dict
import warnings

warnings.filterwarnings('ignore')


class SignalProcessor:
    """Processes WiFi RSSI signals for heartbeat detection"""

    def __init__(self, sample_rate: int = config.SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.hp_filter = self._create_butterworth_filter(
            config.HP_FILTER_CUTOFF, 'high'
        )
        self.lp_filter = self._create_butterworth_filter(
            config.LP_FILTER_CUTOFF, 'low'
        )
        self.signal_history = []

    def _create_butterworth_filter(self, cutoff: float, btype: str):
        """Create a Butterworth filter"""
        nyquist = self.sample_rate / 2
        normalized_cutoff = cutoff / nyquist
        
        # Ensure cutoff is in valid range
        normalized_cutoff = np.clip(normalized_cutoff, 0.01, 0.99)
        
        b, a = butter(4, normalized_cutoff, btype=btype)
        return b, a

    def preprocess_rssi(self, rssi_values: np.ndarray) -> np.ndarray:
        """Apply filtering to raw RSSI values
        
        Args:
            rssi_values: Array of RSSI measurements (dBm)
            
        Returns:
            Filtered signal
        """
        if len(rssi_values) < 10:
            return rssi_values

        # Remove DC offset
        signal_centered = rssi_values - np.mean(rssi_values)

        # Apply high-pass filter (remove slow drift)
        b_hp, a_hp = self.hp_filter
        if len(signal_centered) >= len(b_hp):
            signal_hp = filtfilt(b_hp, a_hp, signal_centered)
        else:
            signal_hp = signal_centered

        # Apply low-pass filter (remove high-frequency noise)
        b_lp, a_lp = self.lp_filter
        if len(signal_hp) >= len(b_lp):
            signal_filtered = filtfilt(b_lp, a_lp, signal_hp)
        else:
            signal_filtered = signal_hp

        return signal_filtered

    def compute_fft(self, signal_data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Compute FFT of the signal
        
        Args:
            signal_data: Filtered signal values
            
        Returns:
            frequencies (Hz), power spectrum
        """
        if len(signal_data) < 2:
            return np.array([]), np.array([])

        # Apply Hamming window to reduce spectral leakage
        windowed = signal_data * np.hamming(len(signal_data))

        # Compute FFT
        fft_values = fft.fft(windowed)
        power = np.abs(fft_values) ** 2
        
        # Only keep positive frequencies
        frequencies = fft.fftfreq(len(signal_data), 1 / self.sample_rate)
        positive_idx = frequencies >= 0
        
        frequencies = frequencies[positive_idx]
        power = power[positive_idx]

        return frequencies, power

    def detect_peaks_in_band(self, frequencies: np.ndarray, power: np.ndarray,
                            freq_min: float, freq_max: float,
                            prominence: float = config.PEAK_PROMINENCE) -> List[Dict]:
        """Detect peaks in a specific frequency band
        
        Args:
            frequencies: FFT frequencies
            power: FFT power spectrum
            freq_min: Minimum frequency (Hz)
            freq_max: Maximum frequency (Hz)
            prominence: Minimum peak prominence
            
        Returns:
            List of detected peaks with frequency and magnitude
        """
        # Filter to frequency band
        band_mask = (frequencies >= freq_min) & (frequencies <= freq_max)
        band_freqs = frequencies[band_mask]
        band_power = power[band_mask]

        if len(band_power) < 3:
            return []

        # Find peaks
        peaks, properties = find_peaks(band_power, prominence=prominence * np.median(band_power))

        # Sort by prominence (strength)
        peak_indices = peaks[np.argsort(properties['prominences'])[::-1]]

        results = []
        for idx in peak_indices:
            results.append({
                'frequency': band_freqs[idx],
                'power': band_power[idx],
                'magnitude': np.sqrt(band_power[idx])
            })

        return results

    def detect_heartbeat_frequency(self, rssi_values: np.ndarray) -> Dict:
        """Detect heartbeat frequency from RSSI signal
        
        Args:
            rssi_values: Array of RSSI measurements
            
        Returns:
            Dictionary with detected frequency and confidence
        """
        if len(rssi_values) < 20:
            return {'detected': False, 'frequency': None, 'confidence': 0.0}

        # Preprocess signal
        filtered = self.preprocess_rssi(rssi_values)

        # Compute FFT
        freqs, power = self.compute_fft(filtered)

        if len(freqs) == 0:
            return {'detected': False, 'frequency': None, 'confidence': 0.0}

        # Detect peaks in heartbeat band
        peaks = self.detect_peaks_in_band(
            freqs, power,
            config.HEARTBEAT_MIN_FREQ,
            config.HEARTBEAT_MAX_FREQ
        )

        if not peaks:
            return {'detected': False, 'frequency': None, 'confidence': 0.0}

        # Get strongest peak
        strongest = peaks[0]
        frequency = strongest['frequency']
        magnitude = strongest['magnitude']

        # Calculate confidence based on signal strength and SNR
        noise_floor = np.median(power)
        snr = magnitude / (noise_floor + 1e-10)
        confidence = min(1.0, snr / 10.0)  # Normalize to 0-1

        # Penalize if near band edges (unreliable)
        edge_penalty = 1.0
        if frequency < 0.9 or frequency > 1.9:
            edge_penalty = 0.7

        confidence *= edge_penalty

        return {
            'detected': confidence >= config.CONFIDENCE_THRESHOLD,
            'frequency': frequency,
            'confidence': confidence,
            'magnitude': magnitude,
            'snr': snr
        }

    def frequency_to_bpm(self, frequency: float) -> float:
        """Convert frequency (Hz) to beats per minute
        
        Args:
            frequency: Frequency in Hz
            
        Returns:
            BPM value
        """
        return frequency * 60

    def bpm_to_frequency(self, bpm: float) -> float:
        """Convert BPM to frequency (Hz)
        
        Args:
            bpm: Beats per minute
            
        Returns:
            Frequency in Hz
        """
        return bpm / 60

    def detect_breathing(self, rssi_values: np.ndarray) -> Dict:
        """Detect breathing pattern from RSSI signal
        
        Args:
            rssi_values: Array of RSSI measurements
            
        Returns:
            Dictionary with breathing frequency and confidence
        """
        if len(rssi_values) < 30:
            return {'detected': False, 'frequency': None, 'confidence': 0.0}

        filtered = self.preprocess_rssi(rssi_values)
        freqs, power = self.compute_fft(filtered)

        if len(freqs) == 0:
            return {'detected': False, 'frequency': None, 'confidence': 0.0}

        peaks = self.detect_peaks_in_band(
            freqs, power,
            config.BREATHING_MIN_FREQ,
            config.BREATHING_MAX_FREQ,
            prominence=0.8
        )

        if not peaks:
            return {'detected': False, 'frequency': None, 'confidence': 0.0}

        strongest = peaks[0]
        frequency = strongest['frequency']
        magnitude = strongest['magnitude']

        noise_floor = np.median(power)
        snr = magnitude / (noise_floor + 1e-10)
        confidence = min(1.0, snr / 5.0)

        return {
            'detected': confidence >= 0.4,
            'frequency': frequency,
            'confidence': confidence,
            'breaths_per_minute': frequency * 60
        }

    def smooth_bpm(self, bpm_history: List[float], window_size: int = 5) -> float:
        """Smooth BPM estimate using moving average
        
        Args:
            bpm_history: List of recent BPM estimates
            window_size: Number of samples for smoothing
            
        Returns:
            Smoothed BPM
        """
        if len(bpm_history) == 0:
            return 0.0

        window = bpm_history[-window_size:]
        return np.mean(window)

    def analyze_signal_quality(self, rssi_values: np.ndarray) -> Dict:
        """Assess overall signal quality and noise level
        
        Args:
            rssi_values: Array of RSSI measurements
            
        Returns:
            Signal quality metrics
        """
        if len(rssi_values) < 10:
            return {'quality': 'poor', 'snr': 0}

        # Calculate metrics
        mean_rssi = np.mean(rssi_values)
        std_rssi = np.std(rssi_values)
        peak_to_peak = np.max(rssi_values) - np.min(rssi_values)

        # Estimate SNR (rough approximation)
        snr = peak_to_peak / (2 * std_rssi) if std_rssi > 0 else 0

        # Quality assessment
        if snr > 5:
            quality = 'excellent'
        elif snr > 3:
            quality = 'good'
        elif snr > 1:
            quality = 'fair'
        else:
            quality = 'poor'

        return {
            'quality': quality,
            'snr': snr,
            'mean_rssi': mean_rssi,
            'std_rssi': std_rssi,
            'peak_to_peak': peak_to_peak,
            'stability': 1.0 - min(1.0, std_rssi / 20)  # 0-1 score
        }
