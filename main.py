#!/usr/bin/env python3
"""
WiFi RSSI-based Heartbeat Detection
Main CLI entry point
"""

import click
import json
from datetime import datetime
from pathlib import Path
from heartbeat_detector import HeartbeatDetector
from wifi_scanner import WiFiScanner
import config
from tabulate import tabulate
import sys


class StateManager:
    """Manages CLI state across commands"""
    def __init__(self):
        self.scanner = WiFiScanner()
        self.detector = HeartbeatDetector()


state = StateManager()


@click.group()
def cli():
    """WiFi Heartbeat Detection System
    
    Detect and analyze heartbeat patterns using WiFi RSSI signals.
    """
    pass


@cli.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
def scan(verbose):
    """Scan for available WiFi networks"""
    click.echo("\n📡 Scanning for WiFi networks...\n")

    try:
        networks = state.scanner.scan()

        if not networks:
            click.echo("❌ No networks found")
            return

        # Format for display
        table_data = []
        for net in networks:
            signal = net.get('signal', 'N/A')
            if isinstance(signal, (int, float)):
                signal_str = f"{int(signal)} dBm"
                if signal > -70:
                    signal_bar = "████ Excellent"
                elif signal > -80:
                    signal_bar = "███░ Good"
                elif signal > -90:
                    signal_bar = "██░░ Fair"
                else:
                    signal_bar = "█░░░ Weak"
            else:
                signal_str = str(signal)
                signal_bar = "N/A"

            table_data.append([
                net.get('ssid', '[Hidden]'),
                signal_str,
                signal_bar,
                net.get('bssid', 'N/A'),
                net.get('channel', 'N/A')
            ])

        headers = ['SSID', 'Signal', 'Quality', 'BSSID', 'Channel']
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
        click.echo(f"\n✓ Found {len(networks)} network(s)\n")

    except PermissionError:
        click.echo("❌ Permission denied. Try running with sudo:")
        click.echo("   sudo python main.py scan\n")
    except Exception as e:
        click.echo(f"❌ Error scanning networks: {e}\n")


@cli.command()
@click.option('--network', '-n', help='Target WiFi network SSID')
@click.option('--duration', '-d', type=int, default=config.DEFAULT_DURATION,
              help=f'Capture duration in seconds (default: {config.DEFAULT_DURATION})')
@click.option('--sensitivity', '-s', type=float, default=0.7,
              help='Detection sensitivity 0-1 (default: 0.7)')
@click.option('--visualize', '-v', is_flag=True, help='Show real-time visualization')
@click.option('--output', '-o', help='Save results to file (JSON/CSV)')
def detect(network, duration, sensitivity, visualize, output):
    """Detect heartbeat on a WiFi network"""

    # If network not specified, ask user
    if not network:
        click.echo("\n📡 Available networks:\n")
        try:
            networks = state.scanner.scan()
            if not networks:
                click.echo("❌ No networks found")
                return

            for i, net in enumerate(networks, 1):
                ssid = net.get('ssid', '[Hidden]')
                signal = net.get('signal', 'N/A')
                click.echo(f"{i}. {ssid} ({signal} dBm)")

            choice = click.prompt('Select network number', type=int)
            if 1 <= choice <= len(networks):
                network = networks[choice - 1].get('ssid')
            else:
                click.echo("Invalid selection")
                return
        except Exception as e:
            click.echo(f"Error getting networks: {e}")
            return

    # Validate parameters
    if not (0.1 <= sensitivity <= 1.0):
        click.echo("❌ Sensitivity must be between 0.1 and 1.0")
        return

    if duration < 5 or duration > config.MAX_DURATION:
        click.echo(f"❌ Duration must be between 5 and {config.MAX_DURATION} seconds")
        return

    try:
        # Run detection
        result = state.detector.detect_on_network(network, duration, sensitivity)

        if not result['success']:
            click.echo(f"❌ {result.get('error', 'Detection failed')}")
            return

        # Display results
        click.echo("\n" + "="*50)
        click.echo("DETECTION RESULTS")
        click.echo("="*50)

        # Heartbeat results
        if result['heartbeat']['detected']:
            bpm = result['heartbeat']['bpm']
            confidence = result['heartbeat']['confidence']
            freq = result['heartbeat']['frequency_hz']
            click.echo(f"\n❤️  HEARTBEAT DETECTED")
            click.echo(f"   BPM: {bpm:.1f}")
            if 'smoothed_bpm' in result['heartbeat']:
                click.echo(f"   Smoothed BPM: {result['heartbeat']['smoothed_bpm']:.1f}")
            click.echo(f"   Frequency: {freq:.2f} Hz")
            click.echo(f"   Confidence: {confidence:.1%}")
            click.echo(f"   SNR: {result['heartbeat']['snr']:.2f}")
        else:
            click.echo("\n❌ No heartbeat detected")
            click.echo(f"   (Confidence threshold: {result['heartbeat']['confidence']:.1%})")

        # Breathing results
        if result['breathing']['detected']:
            bpm = result['breathing']['breaths_per_minute']
            click.echo(f"\n🫁 Breathing: {bpm:.1f} breaths/min (confidence: {result['breathing']['confidence']:.1%})")

        # Signal quality
        quality = result['signal_quality']
        click.echo(f"\n📊 Signal Quality: {quality['quality'].upper()}")
        click.echo(f"   Mean RSSI: {quality['mean_rssi']:.1f} dBm")
        click.echo(f"   Std Dev: ±{quality['std_rssi']:.1f}")
        click.echo(f"   SNR: {quality['snr']:.2f}")
        click.echo(f"   Stability: {quality['stability']:.1%}")

        click.echo(f"\nSamples: {result['samples_collected']}")
        click.echo(f"Timestamp: {result['timestamp']}")
        click.echo("="*50 + "\n")

        # Save results if requested
        if output:
            _save_results(result, output)
            click.echo(f"✓ Results saved to {output}\n")

    except KeyboardInterrupt:
        click.echo("\n\nDetection cancelled by user.")
    except Exception as e:
        click.echo(f"❌ Error during detection: {e}\n")


@cli.command()
@click.option('--network', '-n', help='Target WiFi network SSID')
@click.option('--interval', '-i', type=int, default=30,
              help='Detection interval in seconds (default: 30)')
@click.option('--max-duration', '-m', type=int, help='Maximum total duration (seconds)')
def monitor(network, interval, max_duration):
    """Continuously monitor heartbeat"""
    if not network:
        click.echo("Please specify network with -n/--network")
        return

    try:
        results = state.detector.continuous_detection(network, interval, max_duration)
        
        # Show statistics
        click.echo("\n" + "="*50)
        click.echo("MONITORING SUMMARY")
        click.echo("="*50)
        stats = state.detector.get_statistics()
        click.echo(f"Total runs: {stats['total_detections']}")
        click.echo(f"Successful detections: {stats['successful_detections']}")
        if 'bpm_statistics' in stats:
            bpm_stats = stats['bpm_statistics']
            click.echo(f"\nBPM Statistics:")
            click.echo(f"  Mean: {bpm_stats['mean']:.1f}")
            click.echo(f"  Std Dev: ±{bpm_stats['std']:.1f}")
            click.echo(f"  Range: {bpm_stats['min']:.0f} - {bpm_stats['max']:.0f}")
            click.echo(f"  Median: {bpm_stats['median']:.1f}")
        click.echo("="*50 + "\n")

    except KeyboardInterrupt:
        click.echo("\n\nMonitoring stopped by user.")
    except Exception as e:
        click.echo(f"❌ Error during monitoring: {e}\n")


@cli.command()
def config_show():
    """Show current configuration"""
    click.echo("\n❤️  Current Configuration\n")
    click.echo("Signal Processing:")
    click.echo(f"  Sample Rate: {config.SAMPLE_RATE} Hz")
    click.echo(f"  Window Size: {config.WINDOW_SIZE}")
    click.echo(f"  FFT Overlap: {config.FFT_OVERLAP}%")
    
    click.echo("\nFrequency Ranges:")
    click.echo(f"  Heartbeat: {config.HEARTBEAT_MIN_FREQ}-{config.HEARTBEAT_MAX_FREQ} Hz ")
    click.echo(f"           ({int(config.HEARTBEAT_MIN_FREQ*60)}-{int(config.HEARTBEAT_MAX_FREQ*60)} BPM)")
    click.echo(f"  Breathing: {config.BREATHING_MIN_FREQ}-{config.BREATHING_MAX_FREQ} Hz")
    
    click.echo("\nDetection:")
    click.echo(f"  Confidence Threshold: {config.CONFIDENCE_THRESHOLD:.1%}")
    click.echo(f"  Min Signal Duration: {config.MIN_SIGNAL_DURATION}s")
    click.echo(f"  Noise Threshold: {config.NOISE_THRESHOLD} dB")
    click.echo()


def _save_results(result, filepath):
    """Save detection results to file"""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    if filepath.endswith('.json'):
        with open(filepath, 'w') as f:
            json.dump(result, f, indent=2)
    elif filepath.endswith('.csv'):
        # Simple CSV export
        with open(filepath, 'w') as f:
            f.write('parameter,value\n')
            if result['heartbeat']['detected']:
                f.write(f"bpm,{result['heartbeat']['bpm']:.1f}\n")
                f.write(f"frequency_hz,{result['heartbeat']['frequency_hz']:.2f}\n")
                f.write(f"confidence,{result['heartbeat']['confidence']:.3f}\n")


if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n\nExiting...")
        sys.exit(0)
