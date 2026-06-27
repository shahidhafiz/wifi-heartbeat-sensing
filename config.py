"""
Configuration parameters for WiFi Heartbeat Detection
"""

# ============================================================================
# SIGNAL PROCESSING PARAMETERS
# ============================================================================

# Sampling rate (measurements per second)
# Higher = more accurate but more CPU intensive
SAMPLE_RATE = 10  # Hz

# Window size for FFT analysis (samples)
WINDOW_SIZE = 100

# FFT overlap percentage (0-100)
FFT_OVERLAP = 50

# ============================================================================
# HEARTBEAT DETECTION PARAMETERS
# ============================================================================

# Heartbeat frequency range (Hz)
# ~60 BPM = 1 Hz, ~120 BPM = 2 Hz
HEARTBEAT_MIN_FREQ = 0.8   # 48 BPM
HEARTBEAT_MAX_FREQ = 2.0   # 120 BPM

# Breathing frequency range (Hz)
BREATHING_MIN_FREQ = 0.15  # 9 BPM
BREATHING_MAX_FREQ = 0.5   # 30 BPM

# Motion/gesture frequency range (Hz)
MOTION_MIN_FREQ = 0.5
MOTION_MAX_FREQ = 5.0

# ============================================================================
# SIGNAL FILTERING
# ============================================================================

# Noise threshold (dB) - signals below this are filtered
NOISE_THRESHOLD = 0.5

# High-pass filter cutoff (Hz)
HP_FILTER_CUTOFF = 0.5

# Low-pass filter cutoff (Hz)
LP_FILTER_CUTOFF = 5.0

# ============================================================================
# DETECTION PARAMETERS
# ============================================================================

# Minimum confidence score (0-1) to report detection
CONFIDENCE_THRESHOLD = 0.6

# Minimum duration of sustained signal (seconds)
MIN_SIGNAL_DURATION = 3

# Peak prominence threshold (relative to background noise)
PEAK_PROMINENCE = 1.5

# Harmonic tolerance (Hz) - how close harmonics must be
HARMONIC_TOLERANCE = 0.1

# ============================================================================
# CAPTURE PARAMETERS
# ============================================================================

# Default capture duration (seconds)
DEFAULT_DURATION = 60

# Maximum capture duration (seconds)
MAX_DURATION = 300

# WiFi scan timeout (seconds)
WIFI_SCAN_TIMEOUT = 10

# ============================================================================
# VISUALIZATION
# ============================================================================

# Update interval for live plots (milliseconds)
VIZ_UPDATE_INTERVAL = 500

# Number of seconds to display in rolling window
VIZ_WINDOW_SECONDS = 30

# Enable/disable different plot types
PLOT_RAW_RSSI = True
PLOT_FILTERED_SIGNAL = True
PLOT_FFT_SPECTRUM = True
PLOT_HEARTBEAT_TRACE = True

# ============================================================================
# ADVANCED PARAMETERS
# ============================================================================

# Enable adaptive filtering
ADAPTIVE_FILTERING = True

# Enable harmonic detection and tracking
TRACK_HARMONICS = True

# Maximum number of harmonics to track
MAX_HARMONICS = 3

# Use multiple targets for averaging
USE_MULTIPLE_TARGETS = False
NUM_TARGETS = 3

# ============================================================================
# OUTPUT & LOGGING
# ============================================================================

# Output directory for results
OUTPUT_DIR = "./results"

# Enable logging to file
LOG_TO_FILE = True
LOG_FILE = "./logs/heartbeat_detection.log"

# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL = "INFO"

# Save raw data to CSV
SAVE_RAW_DATA = True

# ============================================================================
# PLATFORM-SPECIFIC
# ============================================================================

# Require sudo/admin for WiFi scanning
REQUIRE_ADMIN = True

# WiFi adapter to use (auto-detect if empty string)
WIFI_ADAPTER = ""

# ============================================================================
# EXPERIMENTAL FEATURES
# ============================================================================

# Enable machine learning model (if available)
USE_ML_MODEL = False
ML_MODEL_PATH = "./models/heartbeat_detector.pkl"

# Enable real-time BPM smoothing
BPM_SMOOTHING_WINDOW = 5  # seconds

# Kalman filter for BPM estimation
USE_KALMAN_FILTER = True
