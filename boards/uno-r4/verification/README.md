# Arduino UNO R4 routing verification

**Passed.** Each of the 61 breakout input positions connects to its assigned male header pin and 2.54 mm screw terminal. Each matching underside shield socket connects to its assigned solder pad on both shield versions. All 38 direct mating positions match the UNO R4 Minima and UNO R4 WiFi layouts. The review covers the editable PCB sources and their released fabrication artwork. Physical assemblies and cables have yet to be measured.

## Board results

| Board | Numbered copper pads | Routed trace segments | Vias | Intended copper networks | Unexpected opens / shorts |
|---|---:|---:|---:|---:|---:|
| Bench breakout | 185 | 164 | 3 | 61 | 0 / 0 |
| Companion prototyping shield | 302 | 61 | 0 | 241 | 0 / 0 |
| Blank shield | 122 | 61 | 0 | 61 | 0 / 0 |

The breakout count includes both Qwiic connector mounting pads on Q_GND. The companion shield has 61 routed channels plus 180 individually isolated prototyping pads. The blank shield routes its 61 perimeter connections and leaves its work area free.

## Which connections reach the Arduino?

| Breakout inputs | Positions | Host connection |
|---|---:|---|
| J1–J4 | 32 | Long-tail headers plug into the digital, analog and power headers on either UNO R4. |
| J5 | 6 | The underside socket plugs into Minima J1 or WiFi J3, the 2×3 SPI header. |
| J6–J8 | 13 | WiFi only. Three jumpers from Arduino JOFF, six connections from the ESP header J6, and a four-wire Qwiic cable from J2. |
| J9 | 10 | Minima only. A ten-position, pin-1-to-pin-1 cable connects the Arduino's J2 debug header. Pin 6 is reserved and has no Arduino signal. |

The 61 positions cover both model configurations. The Minima has 48 accessible positions, including the reserved contact. The WiFi has 51. Rails, grounds and signals such as SDA/A4 may become common through the Arduino when it is installed. The carrier preserves each physical contact as its own route.

## Reading the continuity sheet

**UNO-R4-Pin-Continuity.csv** is sorted by breakout input. Each row gives the Arduino reference and pin on each applicable model, the breakout's input, screw terminal and male pin, and the shield's female socket and solder pad. A blank model column means that bank belongs to the other UNO R4. The last column is available for bench measurements with the assembly unpowered.

| Signal | Arduino contact | Breakout input | Screw terminal | Breakout male | Shield socket | Shield solder pad |
|---|---|---|---|---|---|---|
| D0 / RX, either model | JDIGITAL.1 | J2.8 | TB2.1 | H2.8 | J2.8 | P2.8 |
| SWDIO, Minima via cable | J2.2 | J9.2 | TB9.10 | H9.1 | J9.1 | P9.1 |
| Qwiic SCL1, WiFi via cable | J2.4 | J8.4 | TB8.1 | H8.4 | J8.4 | P8.4 |
| Reserved, Minima via cable | J2.6 | J9.6 | TB9.8 | H9.3 | J9.3 | P9.3 |

## Evidence

- All three released editable PCB and schematic files match their counterparts in the combined PCB repository byte for byte. The manifest identifies the source archives and their SHA-256 hashes. Each board passed a new KiCad 9.0.2 electrical and design rule check, including the unrouted-item and PCB-to-schematic parity checks.
- Both released copper layers and the Excellon drill data matched fresh fabrication exports after excluding timestamp metadata. The artwork audit reconstructed the conducting regions from drawn and flashed geometry. It subtracted the drill holes and joined layers through plated barrels. It then compared every numbered pad's physical connectivity with the independently exported schematic netlist. All copper islands belonged to an expected net.
- All 572 routed segment ends touch an assigned pad, via or another trace of the same net on the same layer. In two separate in-memory tests, removing a section of the D0 trace correctly reported an open and adding a bridge from D0 to D1 correctly reported a short.
- The connector pin numbers and nets were read from the original Arduino Altium layouts and checked against Arduino's published pinouts. Registering each host layout on the D0 header gave a maximum nominal direct-contact center error below 0.001 mm. All 61 breakout male pins coincided with the matching bottom socket centers on each shield. The front legend positions were also checked on all three boards. These are layout measurements.
- The evidence folder contains the KiCad reports, schematic netlists, pad inventories, copper tests and stack results. The inputs folder includes each audited editable project ZIP and the original complete fabrication ZIP plus its pin tables. The manifest identifies each fabrication archive by name and hash.

### Repeating the check

With KiCad CLI 9.0.2, its Python bindings, Gerbonara 1.6.3 and Shapely 2.2 available, run `python3 replay/replay.py /path/to/new-audit-directory`. Use `--pcb-python` to select the Python interpreter with KiCad bindings. By default the run uses the included Arduino header coordinates and nets. Supply `--arduino-dir /path/to/original-boards` containing `minima.PcbDoc` and `wifi.PcbDoc` to regenerate that reference from Arduino's layouts. Use the release's KiCad version for the metadata-normalized fabrication file comparison.

### Arduino references

- UNO R4 Minima ABX00080. [Official pinout](https://docs.arduino.cc/resources/pinouts/ABX00080-full-pinout.pdf) · [Schematic](https://docs.arduino.cc/resources/schematics/ABX00080-schematics.pdf) · [Hardware and CAD downloads](https://docs.arduino.cc/hardware/uno-r4-minima/)
- UNO R4 WiFi ABX00087. [Official pinout](https://docs.arduino.cc/resources/pinouts/ABX00087-full-pinout.pdf) · [Schematic](https://docs.arduino.cc/resources/schematics/ABX00087-schematics.pdf) · [Hardware and CAD downloads](https://docs.arduino.cc/hardware/uno-r4-wifi/)
