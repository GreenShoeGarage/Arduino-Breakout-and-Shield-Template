# UNO R4 stack enclosure • Revision A

Print one **UNO-R4-Stack-Base.stl** and one **UNO-R4-Stack-Bezel.stl** from the fabrication folder. Import both in millimeters. Each part sits flat in its saved orientation. The assembled plastic measures **132 × 120 × 43 mm**. The open bezel lifts off for service and admits tall components on the upper shield.

## Fit

The bottom board is a bare Arduino UNO R4 Minima (ABX00080) or UNO R4 WiFi (ABX00087). Above it sits the 106 × 98 mm Green Shoe Garage UNO R4 Rev A bench breakout. The upper position accepts either the 180-hole companion prototyping shield or the blank component shield from this project. The case uses different mounting patterns for the Arduino and the breakout. The shield seats on the nine male jumper rows.

The large opening at the USB end takes both USB-C and barrel-power cables. The sides accept horizontal wire entry to TB1–TB9. Through the bezel, a screwdriver reaches all 61 screws, and the shield solder pads, the four original pass-through header banks and the breakout’s auxiliary connectors remain available. The WiFi Qwiic cable also has a low side exit. Fit model-specific cables under the shield before closing the stack. When the shield is fitted, its underside sockets occupy H1–H9 and the same signals are available at the matching P pad rows. The Arduino reset switch is accessible with a slim nonconductive probe from above. The shield itself covers part of the Arduino; the case provides access to the stacked assembly through its breakout connections.

## Print and assemble

Use the illustrated guide in the drawings folder. PETG, a 0.4 mm nozzle, 0.20 mm layers and four walls are suggested starting settings for this geometry. Check the bridges above the side-loaded bezel nuts in your slicer, and clear pocket openings after printing. The external base face and either flat bezel face sit on the print bed. Print scale is 100%.

- **Arduino** — three M2 × 10 mm socket-head screws, maximum head diameter 3.8 mm, and three M2 nuts with 4 mm flats. The front screw bore is deliberately offset 0.35 mm away from the barrel jack within the Arduino's 3.2 mm mounting hole. Fit the boards loosely before final tightening.
- **Breakout** — four M3 × 30 mm fully threaded nylon screws, head diameter up to 6.2 mm and head height up to 3.1 mm. Fit three 5.5 mm across-flats M3 nylon nuts to each screw. One nut locks the stud to the floor pedestal, one supports the seated board, and one retains the board. Trim the nylon tip to within 0.5 mm above the retaining nut before fitting the shield.
- **Bezel** — four M3 × 8 mm machine screws and four 5.5 mm across-flats M3 nuts up to 2.5 mm thick. Insert each nut from the inside face of its corner tower and start all four screws before tightening.

Level the breakout supports at the height set by the fully seated Arduino and ICSP connectors. The fit analysis covers 21.1–24.6 mm from the outside bottom of the case to the breakout underside. The 11.05 mm nominal breakout-to-shield gap comes from the specified mating headers. Check lead lengths, actual plugs, wiring and ground clearance before applying power.

## Design and inspection

- **fabrication/** — two printable STLs.
- **drawings/** — three-page print, hardware, dimension and assembly guide.
- **previews/** — installed and empty-interior renders. Connector bodies and fasteners in the installed rendering are illustrative. The case, PCBs and mounting coordinates come from CAD.
- **cad/** — exact solid STEP files for base and bezel. The bezel is saved in print orientation. Move it to Z 40 mm to assemble.
- **source/** — millimeter-native parametrized CadQuery model and interface data extracted from the released PCB files and Arduino layouts. Use Python with CadQuery 2.7, ezdxf, and NumPy. Run `python source/enclosure.py` to regenerate both STLs and STEP files. `python source/check_print_sections.py` checks the saved mesh contours. The optional stack audit accepts three STEP files via `--wifi-step`, `--blank-step` and `--proto-step`.
- **checks/** — solid and mesh round-trip reports, stack and access measurements, and section checks.
- **setup/** — proposed print setup and outstanding physical checks.

Mesh geometry and CAD fit were verified. Each STL contains one closed connected surface. The models have not been physically printed or tested with actual boards and plugs. Slicer profiles, printer calibration, line clearances, first-article fit and any components added to the shield should be checked on the user's setup.

## Mechanical references

- [Arduino UNO R4 WiFi drawings, CAD and STEP](https://docs.arduino.cc/hardware/uno-r4-wifi/)
- [Arduino UNO R4 Minima drawings and CAD](https://docs.arduino.cc/hardware/uno-r4-minima/)
- [Phoenix Contact MPT 2.54 mm terminal](https://www.phoenixcontact.com/en-us/products/printed-circuit-board-terminal-mpt-0510-254-1725737)
- [Bambu Lab H2S specifications](https://store.bblcdn.com/s7/default/3f91ec86de1a4ce28fe8fb660b95cd3e/h2s.pdf)

Board coordinates and mechanical references checked 24 November 2026. Source archive identifiers are represented by SHA-256 in source/interfaces.json.
