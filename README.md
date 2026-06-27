# WiFi RSSI-Based Heartbeat Detection

A Python application that detects and visualizes heartbeat patterns using WiFi RSSI (Received Signal Strength Indicator) variations. Works on any desktop PC with standard WiFi adapter.

## How It Works

WiFi signals are affected by the human body's micro-movements:
- **Heartbeat** causes small chest cavity changes (~60-100 BPM = 1-1.7 Hz)
- **Breathing** causes larger movements (~12-20 BPM = 0.2-0.33 Hz)
- **Other motion** creates higher frequency variations

This app:
1. Captures RSSI fluctuations from WiFi signals
2. Applies signal processing (noise filtering, FFT analysis)
3. Detects periodic patterns in the heartbeat frequency range (0.8-2.0 Hz)
4. Displays real-time visualization of detected signals

## Features

- ✅ **Cross-platform**: Works on Windows, macOS, Linux
- ✅ **No special hardware**: Uses standard WiFi adapter
- ✅ **Real-time visualization**: Live graphs of signal strength and detected frequencies
- ✅ **Heartbeat detection**: Identifies cardiac rhythm patterns
- ✅ **CLI & GUI options**: Command-line or dashboard interface
- ✅ **Configurable parameters**: Adjust sensitivity, frequency ranges, filtering

## Requirements

- Python 3.9+
- WiFi adapter (any standard adapter)
- Administrator/sudo privileges (for WiFi scanning on some systems)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/shahidhafiz/wifi-heartbeat-sensing.git
cd wifi-heartbeat-sensing
```

### 2. Create virtual environment (recommended)

```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### Platform-Specific Setup

#### Linux
```bash
# Install system packages
sudo apt-get install python3-dev libffi-dev libssl-dev wireless-tools
```

#### macOS
```bash
# Install via Homebrew
brew install libffi openssl
```

#### Windows
- Install Python 3.9+ from python.org
- May need to run as Administrator for WiFi scanning
- Optional: Install `npcap` or `WinPcap` for enhanced packet capture

## Quick Start

### 1. Run the WiFi scanner

```bash
python main.py --scan
```

This will list nearby WiFi networks and their current RSSI values.

### 2. Start heartbeat detection (interactive mode)

```bash
python main.py --detect
```

The app will:
- Capture RSSI from a target network (you select which one)
- Process the signal in real-time
- Display detected frequencies and confidence scores
- Show heartbeat BPM estimate if detected

### 3. Run the visualization dashboard

```bash
python visualizer.py
```

Opens an interactive dashboard with:
- Real-time RSSI signal graph
- Frequency spectrum (FFT)
- Heartbeat detection confidence
- Current BPM estimate

## CLI Options

```bash
python main.py --help

Options:
  --scan                Show available WiFi networks
  --detect              Start heartbeat detection
  --network SSID        Target WiFi network (default: auto-select)
  --duration SECONDS    How long to capture (default: 60)
  --sample-rate HZ      Signal sampling rate (default: 10 Hz)
  --sensitivity LEVEL   Detection sensitivity 0-1 (default: 0.7)
  --visualize           Show live graphs during detection
  --output FILE         Save results to CSV/JSON file
```

## Configuration

Edit `config.py` to customize:

```python
# Heartbeat frequency range (Hz)
HEARTBEAT_MIN_FREQ = 0.8      # 48 BPM
HEARTBEAT_MAX_FREQ = 2.0      # 120 BPM

# Signal processing
SAMPLE_RATE = 10               # Hz (measurements per second)
WINDOW_SIZE = 100              # samples for FFT
NOISE_THRESHOLD = 0.5          # dB

# Detection parameters
CONFIDENCE_THRESHOLD = 0.6     # minimum confidence to report
MIN_SIGNAL_DURATION = 3        # seconds of sustained signal
```

## Understanding the Output

### Heartbeat Detection Report

```
╔══════════════════════════════════════╗
║     WiFi Heartbeat Detection         ║
╠══════════════════════════════════════╣
║ Status: HEARTBEAT DETECTED           ║
║ BPM: 72 ± 3                          ║
║ Confidence: 85%                      ║
║ Primary Frequency: 1.2 Hz            ║
║ Harmonics Detected: 2 (breathing)    ║
║ Signal Quality: Good                 ║
╚══════════════════════════════════════╝
```

**Interpretation:**
- **BPM**: Estimated beats per minute (typically 60-100 for adults)
- **Confidence**: How sure the algorithm is (higher = more reliable)
- **Primary Frequency**: The dominant frequency in heartbeat range
- **Harmonics**: Other detected frequencies (breathing, etc.)
- **Signal Quality**: Overall signal-to-noise ratio

## Limitations & Considerations

⚠️ **Important Notes:**

1. **Distance**: Works best within 5-10 meters of the detection target
2. **Line of sight**: More reliable with clear line of sight (through walls attenuates signal)
3. **Accuracy**: Not medical-grade; for research/educational purposes
4. **Environment**: Crowded WiFi environments or heavy interference reduce accuracy
5. **Privacy**: This app is educational. Use responsibly and ethically. Detecting someone's biometrics without consent raises privacy concerns.
6. **Variability**: Results depend on:
   - WiFi adapter sensitivity
   - Router power settings
   - Environmental interference
   - Target position & movement

## How to Improve Accuracy

1. **Position**: Place target closer to the WiFi router/device
2. **Stability**: Minimize other movement (sit still, breathe normally)
3. **Duration**: Longer capture periods (60+ seconds) improve detection
4. **Channel**: Try different WiFi channels for less interference
5. **Sensitivity**: Adjust `--sensitivity` parameter (0.5-1.0)
6. **Multiple samples**: Take multiple readings and average results

## Project Structure

```
wifi-heartbeat-sensing/
├── main.py                 # Core heartbeat detection engine
├── visualizer.py           # Real-time dashboard
├── config.py               # Configuration parameters
├── signal_processor.py      # FFT, filtering, signal analysis
├── wifi_scanner.py         # WiFi network scanning
├── heartbeat_detector.py    # Heartbeat pattern recognition
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── examples/              # Example usage scripts
├── data/                  # Sample data & results
└── docs/                  # Additional documentation
```

## Example Usage

### Basic Detection

```bash
# Scan networks and pick one
python main.py --scan

# Run detection on selected network for 120 seconds
python main.py --detect --network "MyWiFi" --duration 120 --visualize
```

### Batch Analysis

```bash
# Run multiple detections and save results
for i in {1..5}; do
  python main.py --detect --duration 60 --output results_sample_$i.csv
  sleep 30
done
```

### Advanced: Custom Processing

See `examples/custom_signal_processing.py` for using the signal processor directly.

## Troubleshooting

### "Permission denied" or "No networks found"

**Linux/macOS:**
```bash
sudo python main.py --scan
```

**Windows:**
- Run Command Prompt/PowerShell as Administrator
- Then run the script

### "No heartbeat detected"

1. Ensure target is within 5-10m and reasonably still
2. Increase duration: `--duration 120`
3. Lower sensitivity: `--sensitivity 0.5`
4. Try different WiFi networks
5. Check signal quality with `--scan`

### High CPU usage

- Reduce sample rate: `--sample-rate 5`
- Disable visualization: remove `--visualize`
- Close other applications

### Import errors

```bash
# Verify all packages installed
pip list | grep -E "scapy|numpy|scipy|matplotlib"

# Reinstall if needed
pip install --upgrade -r requirements.txt
```

## Research & References

This project is based on academic research in WiFi-based sensing:

- "Through-Wall Human Pose Estimation Using Radio Signals" - MIT CSAIL
- "Gait Recognition via Disentangled Representation Learning" - WiFi CSI research
- "Breath Detection with WiFi Signals" - Multiple academic papers
- IEEE 802.11bf WiFi Sensing standard

## Contributing

Contributions welcome! Areas for improvement:

- [ ] Improve heartbeat detection accuracy
- [ ] Multi-target detection
- [ ] Gesture recognition
- [ ] Real-time web dashboard (FastAPI)
- [ ] Mobile app integration
- [ ] Machine learning model training

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - See [LICENSE](LICENSE) file

## Disclaimer

**This project is for educational and research purposes only.** 

Unauthorized use of this technology to monitor individuals without their knowledge or consent may be illegal in your jurisdiction. Always:
- ✅ Get explicit consent before detecting anyone's biometrics
- ✅ Be aware of privacy laws in your area
- ✅ Use ethically and responsibly
- ✅ Respect others' privacy

## Support

For issues, questions, or ideas:
- Open a GitHub Issue
- Check existing issues first
- Include platform info, Python version, and error messages

---

**Happy detecting! 📡❤️**
