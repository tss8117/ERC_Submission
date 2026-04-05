# Corrupted Transmission Recovery

## Stage 1: Looking at the corrupted signal

In this stage, I:
- loaded the WAV file
- normalized it
- plotted the time-domain waveform
- computed and plotted the FFT

The time-domain plot alone was not enough to identify the corruption clearly, but the FFT showed that the useful content was not in the expected baseband region.

---

## Stage 2: Undoing the frequency shift

From the FFT, I estimated that the useful signal had been shifted to around 7.3 kHz.

To correct this, I multiplied the signal by a complex exponential at the opposite frequency. This shifted the spectrum back down to baseband. After that, I took the real part of the result and checked the FFT again.

This second FFT looked much more like normal audio. Most of the useful content was now sitting in the lower frequency range where speech usually lies.

So my conclusion here was that the original signal had been frequency shifted, and this step reversed that effect.

---

## Stage 3: Removing the unwanted tones

After shifting the signal back, I plotted the FFT again to see what was still left.

At this stage, I could see a few narrow, sharp spikes in the spectrum. These did not look like natural audio components. They looked like added interference tones.

The main spikes were around:
- 1200 Hz
- 2200 Hz
- 4100 Hz

To remove them, I used notch filters centered at those frequencies.

There was also a small DC / low-frequency component after demodulation, so I removed that using a high-pass filter.

After these filtering steps, the audio became cleaner and the FFT looked much more reasonable.

---

## Final understanding

Based on the plots and the recovery process, my understanding is:

1. The original audio was shifted upward in frequency.
2. Some narrowband interference tones were added.
3. By shifting the signal back down and removing those tones, the useful audio could be recovered.

---
