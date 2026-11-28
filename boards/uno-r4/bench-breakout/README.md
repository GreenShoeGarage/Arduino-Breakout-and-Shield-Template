# UNO R4 direct-stack breakout · Rev B

Select the underside hardware for the Arduino that will sit below the breakout. The four UNO edge header banks and ICSP mate directly on both models. ESP service, OFF/RTC and the dedicated Qwiic bus connect on WiFi. The rigid riser picks up the ten SWD connector positions on Minima. Either upper shield plugs into H1–H9.

- [Assembly guide and first-article checks](drawings/UNO-R4-Direct-Assembly.pdf)
- [Variant assembly BOM](Assembly-BOM.csv)
- [Every host contact, terminal and shield destination](pin-tables/Arduino-to-terminal.csv)
- [Electrical schematic](drawings/schematic.pdf)
- [Two-layer fabrication archive](UNO-R4-Direct-Breakout-RevB-OSH-Park.zip)
- [Minima riser](../minima-swd-riser/)
- [KiCad, Gerber and host contact verification](../verification/)

The two variants share the same PCB. Build one population per Arduino model. Leave the other model’s underside parts unpopulated and mark the build on the board. Model-specific banks without a matching host remain inactive. KiCad’s master view contains the alternate footprints. The carrier underside illustration shows the WiFi components. Generic connector 3D models illustrate placement. Use the MPNs and assembly dimensions for fabrication.

Import the individual zipped project from ../flux-import/ in Flux under **Import → Project**. The checked design of record is the included KiCad 9 project and its Gerbers. A live Flux import and a physical first article are pending.
