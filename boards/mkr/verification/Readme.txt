MKR Rev A routing verification • November 26, 2026

The PDF shows the carrier copper and the end-to-end pin table. The CSV is the same map for a bench checklist. For physical continuity, disconnect power and remove the Arduino before checking the carrier. Fit a single shield when testing its contacts.

For each PCB, ERC.json and DRC.json are fresh KiCad 9.0.2 reports, netlist.xml is the schematic netlist, and bare-board-test.d356 is the PCB test netlist. The separate CAD and released Gerber/drill fingerprints are in audit.json.

Each electrical result was obtained by merging copper polygons on each layer, removing all drill holes, joining front and back solely around plated holes, and comparing each connected group to the schematic and the expected physical endpoints. The Arduino EAGLE pin coordinates and board orientation anchored the module-side map. Both underside shield sockets matched the component-side carrier male headers by position and net. A second check regenerated both copper and both drill files from the repository and compared them against the three fabrication archives, ignoring only generation timestamps. All 12 matched. The three Flux import packages contained the same PCB, schematic and KiCad project bytes as the repository.

All results describe released digital files. Live Flux workspaces and physically fabricated assemblies were outside the measurements.
