# UNO R4 routing verification · Rev B

KiCad 9.0.2 ERC, all-severity DRC and schematic-to-PCB parity passed on the carrier, rigid riser and both shields. Gerber copper geometry and plated drill annuli were checked separately against the netlists. All 61 carrier nets form one continuous copper island per net. No opens, shorts, orphan islands or dangling track ends were found on any board.

The continuity CSV follows 51 WiFi and 48 Minima physical connector positions into the carrier screw terminals and both shields. Minima J2.6 is reserved by Arduino. Every H pin aligns with its female socket in each shield. The 180 prototype islands intentionally remain isolated. Shared signals that join on the Arduino keep separate board branches where the hardware calls for that.

- [Model-specific terminal and shield-pad checklist](UNO-R4-Direct-Continuity.csv)
- [Digital results and editable PCB hashes](system-result.json)
- [Nominal assembly and shell clearance](direct-stack-fit.json)
- [Qwiic strikes against Arduino copper and mask Gerbers](official-Qwiic-targets.json)

The four board subdirectories contain reports, netlists and extracted geometry. A nominal check on populated host STEP geometry found no collision for the selected underside pickup envelopes. Physical contact resistance, tolerance accumulation, powered behavior, live Flux import and supplier order preview remain untested.

To reproduce the electrical checks, install KiCad 9 with its pcbnew Python module plus gerbonara 1.6.3 and Shapely 2.x in the calling Python. In a terminal run `python replay/recheck.py /path/to/new-results`. An optional `--pcb-python` argument selects the interpreter with pcbnew. The script writes results into a new output directory and compares regenerated copper/drill files with the released artwork. The official Arduino source zip digests are in official-Qwiic-targets.json.

## Reference drawings

- [Arduino UNO R4 WiFi CAD and pinout](https://docs.arduino.cc/hardware/uno-r4-wifi/)
- [Arduino UNO R4 Minima CAD and pinout](https://docs.arduino.cc/hardware/uno-r4-minima/)
- [Harwin P13-0123 probe](https://www.harwin.com/products/P13-0123)
- [Harwin S13-503 sleeve](https://www.harwin.com/products/S13-503)
- [Harwin M50-3000545 socket](https://www.harwin.com/products/M50-3000545)
- [Flux project import](https://docs.flux.ai/Introduction/layout--kicad-to-flux-)
