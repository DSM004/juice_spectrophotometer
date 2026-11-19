# AS7343 channel table

Sensor: ams OSRAM AS7343 (Adafruit breakout ADA6477), I²C address 0x39.
Source: ams OSRAM AS7343 datasheet, Section 6 (Optical Characteristics), typical values. Real parts vary slightly between batches, so the wavelengths are checked against the lab spectrophotometer (test plan, T6).

The sensor has 12 colour channels, plus a clear (VIS) channel and a flicker channel. Each one is a photodiode behind its own interference filter, so each channel measures one band of light instead of a continuous spectrum.

## Channels (sorted by wavelength)

| Channel | Peak λ (nm) | FWHM (nm) | Colour | SMUX cycle | Light from | Use in this project |
|---|---|---|---|---|---|---|
| F1 | 405 | 30 | Violet | 3 | 405 nm LED | Brown pigments absorb strongly here, so it's a browning/ageing signal |
| F2 | 425 | 22 | Violet-blue | 2 | 405 nm LED (tail) + white | **Main browning channel**: closest to the 420 nm browning index; narrowest band, so the most selective |
| FZ | 450 | 55 | Blue | 1 | White | Carotenoids (orange juice colour) absorb here |
| F3 | 475 | 30 | Blue-cyan | 2 | White | Carotenoids, second band; narrow, so good for quantification |
| F4 | 515 | 40 | Green | 2 | White | Food-colouring tests (depends on the dye colour); general colour |
| F5 | 550 | 35 | Green-yellow | 3 | White | General colour; overlaps FY |
| FY | 555 | 100 | Yellow-green | 1 | White | Very wide band: overall brightness, less use for chemistry |
| FXL | 600 | 80 | Orange | 1 | White | General colour; wide band |
| F6 | 640 | 50 | Red | 2 | White | Red juices or dyes; little absorption in apple juice |
| F7 | 690 | 55 | Deep red | 3 | White (weak) | Low absorption in most juices, so it's a reference channel |
| F8 | 745 | 60 | Near-IR edge | 3 | White tail / 850 nm LED | Almost no pigment absorption; losses here are mostly scattering |
| NIR | 855 | 54 | Near-infrared | 1 | 850 nm LED | **Scattering baseline:** subtract A(NIR) from the visible channels for cloudy juices (test plan, T9) |
| VIS (clear) | broadband | – | All visible | 1, 2, 3 | All | Total light. Read in every cycle, so it checks the LED stayed stable between cycles |
| FD | – | – | – | – | – | Flicker detection. Not used |

Notes:
- The bands overlap (e.g. F5 and FY), so neighbouring channels are not independent measurements.
- White LEDs emit little below about 430 nm or above about 700 nm. That is why the 405 nm and 850 nm LEDs are added: without them, F1, F2 and NIR would be noisy, from low signal rather than anything in the sample.
- Check the white LED's actual spectrum on the lab spectrophotometer, or from its datasheet, and note any channel with a weak signal.

## Which channels to use for what
| Task | Best channels | Why |
|---|---|---|
| Concentration (T7) | Narrow channels where the juice absorbs strongly: F2, F3, F1 (orange: FZ/F3) | Narrow bands follow Beer–Lambert better (see below) |
| Juice type (T8) | All 12, normalised (spectral shape) | The shape differs between juices; normalising removes the effect of concentration |
| Cloudiness (T9) | F8, NIR + TSL2591 | Little pigment absorption, so the loss is mainly scattering |
| Browning/freshness (T10) | F1, F2 (relative to F7) | 420 nm browning index; the ratio cancels some drift |
| LED stability | VIS (clear) | Same light measured in all three cycles |

## Finite-bandwidth caution
Beer–Lambert assumes a single wavelength. Each channel averages over its FWHM, so where the sample's absorption changes across the band, the calibration curve **bends below the straight line at high absorbance** (negative deviation). Expect the wide channels (FY 100 nm, FXL 80 nm) to be the least linear and F2 (22 nm) the most. This is a predicted limitation to test in T3/T7 and to discuss in the evaluation.

## How it reads: SMUX
The chip has only 6 ADCs (converters), so it can't read all its channels at once. A switch matrix (SMUX) routes the photodiodes to the ADCs in batches. In 18-channel mode (`auto_smux = 3`, the library default) it runs three cycles:
- cycle 1: FZ, FY, FXL, NIR
- cycle 2: F2, F3, F4, F6
- cycle 3: F1, F5, F7, F8

The clear channel is read in every cycle. A full spectrum therefore takes about 3 × the integration time.

## Settings
**Integration time** (the exposure time, like a camera shutter):
t_int = (ATIME + 1) × (ASTEP + 1) × 2.78 µs
ATIME is 0–255 and ASTEP is 0–65534 (they can't both be 0).
Full-scale count = (ATIME + 1) × (ASTEP + 1), capped at 65535.

**Gain** (signal amplification, like ISO): 0.5×, 1×, 2×, 4× … 2048× (13 steps). The default is 256×.

| Setting | Starting value | Why |
|---|---|---|
| ATIME | 59 | |
| ASTEP | 999 | |
| → t_int | ≈ 167 ms per cycle, ≈ 0.5 s per full spectrum | Long enough to reduce noise; fast enough for a benchtop measurement |
| → full scale | 60 000 counts | Uses almost the whole 16-bit range (better resolution) |
| Gain | Start at 4× and adjust | The LED shines straight at the sensor, so 256× will saturate it |

**Tuning rule:** with the water blank in place and the LED on, adjust the gain until the brightest channel reads about 50–80 % of full scale (30 000–48 000 counts). Then **fix the gain and integration time for every measurement in a series**. Changing them between the blank and the sample breaks the absorbance calculation.

If one LED makes some channels saturate while others are too dim, measure each LED separately (white, then 405 nm, then 850 nm), each with its own fixed gain and its own blank.

## Settings log (fill in as you tune)
| Date | LED(s) on | LED current (mA) | Gain | ATIME | ASTEP | Brightest channel, blank (counts) | Notes |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

## Why this matters
Absorbance for each channel: A = −log₁₀[(I_sample − I_dark) / (I_blank − I_dark)]
The peak wavelengths in this table are the x-axis of every spectrum plot in the report.
