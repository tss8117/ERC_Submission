
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import butter, filtfilt, iirnotch

# ------------------------------------------------------------
# This script solves only Stage 1 to Stage 3 of the assignment.
# It does NOT include Stage 4.
# ------------------------------------------------------------

# Input and output paths
INPUT_FILE = "corrupted.wav"
OUTPUT_FILE = "recovered.wav"
PLOTS_DIR = "plots"
os.makedirs(PLOTS_DIR, exist_ok=True)

# ------------------------------------------------------------
# Helper function: convert any signal to float and normalize it
# so the amplitude stays in a clean range for processing.
# ------------------------------------------------------------
def normalize_signal(x):
    x = x.astype(np.float64)
    max_val = np.max(np.abs(x))
    if max_val > 0:
        x = x / max_val
    return x

# ------------------------------------------------------------
# Helper function: save a signal as 16-bit WAV audio.
# ------------------------------------------------------------
def save_wav(filename, fs, x):
    x = x / np.max(np.abs(x)) * 0.98
    wavfile.write(filename, fs, np.int16(x * 32767))

# ------------------------------------------------------------
# Helper function: compute the FFT and matching frequency axis.
# We use fftshift so that 0 Hz appears in the center of the plot.
# ------------------------------------------------------------
def get_fft(x, fs):
    X = np.fft.fftshift(np.fft.fft(x))
    f = np.fft.fftshift(np.fft.fftfreq(len(x), d=1/fs))
    mag = np.abs(X)
    return f, X, mag

# ------------------------------------------------------------
# Helper function: plot time-domain waveform.
# max_seconds is used so the waveform is readable.
# ------------------------------------------------------------
def plot_time(x, fs, title, filename, max_seconds=0.05):
    t = np.arange(len(x)) / fs
    limit = min(len(x), int(max_seconds * fs))
    plt.figure(figsize=(10, 4))
    plt.plot(t[:limit], x[:limit], linewidth=0.8)
    plt.title(title)
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename, dpi=180)
    plt.close()

# ------------------------------------------------------------
# Helper function: plot FFT magnitude.
# xlim is used to zoom into the important frequency region.
# ------------------------------------------------------------
def plot_fft(x, fs, title, filename, xlim=None):
    f, X, mag = get_fft(x, fs)
    plt.figure(figsize=(10, 4))
    plt.plot(f, mag, linewidth=0.8)
    plt.title(title)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude")
    if xlim is not None:
        plt.xlim(xlim)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename, dpi=180)
    plt.close()
    return f, X, mag

# ------------------------------------------------------------
# Stage 1: Load the corrupted audio file.
# If the file is stereo, convert it to mono by averaging channels.
# ------------------------------------------------------------
fs, x = wavfile.read(INPUT_FILE)
if x.ndim == 2:
    x = x.mean(axis=1)

# Convert to normalized float before doing any DSP.
x = normalize_signal(x)

# ------------------------------------------------------------
# Stage 1 plots:
# 1) time-domain view of the corrupted signal
# 2) FFT of the corrupted signal
# ------------------------------------------------------------
plot_time(
    x, fs,
    "Stage 1 - Corrupted signal in time domain",
    os.path.join(PLOTS_DIR, "stage1_time_domain.png")
)

f1, X1, mag1 = plot_fft(
    x, fs,
    "Stage 1 - FFT of corrupted signal",
    os.path.join(PLOTS_DIR, "stage1_fft.png"),
    xlim=(-12000, 12000)
)

# ------------------------------------------------------------
# Stage 2: Find where most energy is present in positive frequency.
# For this audio, the main band is centered around a carrier/shift.
# We estimate that shift using the largest positive-frequency peak.
# ------------------------------------------------------------
positive_mask = f1 > 0
fc = f1[positive_mask][np.argmax(mag1[positive_mask])]

# Create a sample index array for frequency shifting.
n = np.arange(len(x))

# ------------------------------------------------------------
# Shift the signal back down to baseband by multiplying with
# exp(-j*2*pi*fc*n/fs). Then take the real part.
# ------------------------------------------------------------
x_stage2 = np.real(x * np.exp(-1j * 2 * np.pi * fc * n / fs))

# Plot Stage 2 output in time domain and frequency domain.
plot_time(
    x_stage2, fs,
    "Stage 2 - Time domain after frequency shift correction",
    os.path.join(PLOTS_DIR, "stage2_time_after_shift.png")
)

f2, X2, mag2 = plot_fft(
    x_stage2, fs,
    "Stage 2 - FFT after frequency shift correction",
    os.path.join(PLOTS_DIR, "stage2_fft_after_shift.png"),
    xlim=(-6000, 6000)
)

# ------------------------------------------------------------
# Stage 3: Remove unwanted narrow spikes.
# From the FFT after Stage 2, the main narrow interference tones
# were observed near these frequencies.
# ------------------------------------------------------------
spike_freqs = [1200.15, 2199.90, 4100.10]

# Save the FFT before filtering with the spike positions marked.
plt.figure(figsize=(10, 4))
plt.plot(f2, mag2, linewidth=0.8)
for sf in spike_freqs:
    plt.axvline(sf, linestyle="--")
plt.title("Stage 3 - FFT before notch filtering")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")
plt.xlim(0, 5000)
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, "stage3_fft_pre_filter.png"), dpi=180)
plt.close()

# ------------------------------------------------------------
# Remove DC / very low-frequency leakage using a high-pass filter.
# This cleans up near-0 Hz residue caused by mixing.
# ------------------------------------------------------------
b_hp, a_hp = butter(4, 30/(fs/2), btype="high")
x_hp = filtfilt(b_hp, a_hp, x_stage2)

# ------------------------------------------------------------
# Apply notch filters one by one to remove narrow interference
# tones while preserving most of the audio band.
# Q=35 keeps the notch narrow.
# ------------------------------------------------------------
x_clean = x_hp.copy()
for f0 in spike_freqs:
    b_notch, a_notch = iirnotch(f0, 35, fs)
    x_clean = filtfilt(b_notch, a_notch, x_clean)

# Normalize before saving/listening.
x_clean = x_clean / np.max(np.abs(x_clean)) * 0.98

# Plot FFT after filtering so the removed spikes can be shown.
plot_fft(
    x_clean, fs,
    "Stage 3 - FFT after notch filtering",
    os.path.join(PLOTS_DIR, "stage3_fft_post_filter.png"),
    xlim=(0, 5000)
)

# Plot final time-domain signal.
plot_time(
    x_clean, fs,
    "Stage 3 - Time domain after filtering",
    os.path.join(PLOTS_DIR, "stage3_time_domain.png")
)

# ------------------------------------------------------------
# Save final recovered audio.
# ------------------------------------------------------------
save_wav(OUTPUT_FILE, fs, x_clean)

# Also print the main observations for quick reference.
print("Estimated frequency shift (carrier):", round(fc, 2), "Hz")
print("Removed narrow spikes at:", spike_freqs)
print("Recovered file saved as:", OUTPUT_FILE)
