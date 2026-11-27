# Arduino MKR and UNO R4 breakout boards and prototyping shields

Six PCB designs from Green Shoe Garage cover two Arduino families. Each family includes a base board, a prototyping shield with a solder grid, and a blank shield for custom components. Each base board brings Arduino pins out to headers and 2.54 mm screw terminals. Both shield variants plug into the headers on their matching base board.

| Family | Base board | Prototyping shield | Blank workspace shield |
| --- | --- | --- | --- |
| Arduino MKR | [MKR Terminal Carrier](boards/mkr/terminal-carrier/) breaks out the two 14-pin rows, using the MKR WiFi 1010 as its reference. | [MKR Carrier ProtoShield](boards/mkr/protoshield/) has a 7 × 25 prototyping grid. Its underside sockets J1 and J2 mate with carrier headers J3 and J4, respectively. | [MKR Blank Shield](boards/mkr/blank-shield/) leaves the center open for component footprints and routing. It retains the two 14-pin underside sockets and two M3 mounting holes. |
| Arduino UNO R4 | [UNO R4 Bench Breakout](boards/uno-r4/bench-breakout/) exposes the standard headers and ICSP, with auxiliary banks marked for the WiFi and Minima variants. | [UNO R4 Companion Shield](boards/uno-r4/companion-shield/) has underside sockets for the breakout headers, labeled solder rows, and a 12 × 15 prototyping grid. | [UNO R4 Blank Shield](boards/uno-r4/blank-shield/) leaves the prototyping area open for component footprints and routing. It retains the nine underside socket banks and their labeled solder rows. |

## Open a board

Download or clone the repository. In KiCad 9, open the `.kicad_pro` file in the chosen board directory, then launch the Schematic Editor or PCB Editor from the project window. Keep the whole directory together when copying a board or packaging it individually. The symbol and footprint tables resolve paths relative to the project.

All three MKR projects and both UNO R4 shield projects include local STEP models. The UNO R4 Bench Breakout references the standard KiCad 9 model library through `KICAD9_3DMODEL_DIR` for its 3D view.

## View PCB files on GitHub

Gerber Viewer for GitHub adds an interactive preview above GitHub's file content. It supports this repository's native KiCad PCB and schematic files through the embedded KiCanvas viewer.

1. Install and enable the Chrome extension. [Gerber Viewer for GitHub](https://chromewebstore.google.com/detail/gerber-viewer-for-github/kjempphffigplmkbpjamikbfgpmdfbfn)
2. Open this repository on GitHub in that browser, then select a PCB or schematic link below to visit its file page.
3. Use the embedded viewer to zoom and pan. For PCB layouts, toggle layers to inspect copper routing, silkscreen, and the board outline.

For a new GitHub repository, upload or commit the extracted project folders so each PCB and schematic has its own file page.

| Board | PCB layout | Schematic |
| --- | --- | --- |
| MKR Terminal Carrier | [View PCB](boards/mkr/terminal-carrier/MKR-Terminal-Carrier.kicad_pcb) | [View schematic](boards/mkr/terminal-carrier/MKR-Terminal-Carrier.kicad_sch) |
| MKR Carrier ProtoShield | [View PCB](boards/mkr/protoshield/MKR-Carrier-ProtoShield.kicad_pcb) | [View schematic](boards/mkr/protoshield/MKR-Carrier-ProtoShield.kicad_sch) |
| MKR Blank Shield | [View PCB](boards/mkr/blank-shield/MKR-Blank-Shield.kicad_pcb) | [View schematic](boards/mkr/blank-shield/MKR-Blank-Shield.kicad_sch) |
| UNO R4 Bench Breakout | [View PCB](boards/uno-r4/bench-breakout/UNO-R4-Breakout.kicad_pcb) | [View schematic](boards/uno-r4/bench-breakout/UNO-R4-Breakout.kicad_sch) |
| UNO R4 Companion Shield | [View PCB](boards/uno-r4/companion-shield/UNO-R4-Companion-Shield.kicad_pcb) | [View schematic](boards/uno-r4/companion-shield/UNO-R4-Companion-Shield.kicad_sch) |
| UNO R4 Blank Shield | [View PCB](boards/uno-r4/blank-shield/UNO-R4-Blank-Shield.kicad_pcb) | [View schematic](boards/uno-r4/blank-shield/UNO-R4-Blank-Shield.kicad_sch) |

The extension also previews Gerber and Excellon drill files, folders containing Gerber layers, and ZIP archives containing Gerber layers committed to GitHub.

## Routing verification

The supplied November 26, 2026 verification packages cover all six Rev A boards. The UNO R4 editable projects match the repository byte for byte, and the three MKR PCB hashes match the supplied audit. The reports record digital routing, rule, and pin-mapping checks. Physical assemblies await bench measurement.

| Family | Verification report | Continuity checklist | Complete verification package |
| --- | --- | --- | --- |
| MKR | [Routing verification (PDF)](boards/mkr/verification/MKR-Routing-Verification.pdf) | [Pin continuity (CSV)](boards/mkr/verification/MKR-Pin-Continuity.csv) | [Reports, netlists, and audit](boards/mkr/verification/) |
| UNO R4 | [Routing verification](boards/uno-r4/verification/README.md) | [Pin continuity (CSV)](boards/uno-r4/verification/UNO-R4-Pin-Continuity.csv) | [Evidence, audited inputs, and replay scripts](boards/uno-r4/verification/) |

Each UNO R4 board folder includes the supplied Gerber and drill files in `fabrication/` and connection tables in `pin-tables/`. The complete UNO R4 verification package retains its input archives and directory structure for the replay instructions.

## Board gallery

Select a 3D view or PCB layout to open the full-size image.

### Arduino MKR

| Board | 3D view | PCB layout |
| --- | --- | --- |
| [MKR Terminal Carrier](boards/mkr/terminal-carrier/) | [![MKR Terminal Carrier 3D view](docs/images/mkr/terminal-carrier/3d.png)](docs/images/mkr/terminal-carrier/3d.png) | [![MKR Terminal Carrier PCB layout](docs/images/mkr/terminal-carrier/layout.png)](docs/images/mkr/terminal-carrier/layout.png) |
| [MKR Carrier ProtoShield](boards/mkr/protoshield/) | [![MKR Carrier ProtoShield 3D view](docs/images/mkr/protoshield/3d.png)](docs/images/mkr/protoshield/3d.png) | [![MKR Carrier ProtoShield PCB layout](docs/images/mkr/protoshield/layout.png)](docs/images/mkr/protoshield/layout.png) |
| [MKR Blank Shield](boards/mkr/blank-shield/) | [![MKR Blank Shield 3D view](docs/images/mkr/blank-shield/3d.png)](docs/images/mkr/blank-shield/3d.png) | [![MKR Blank Shield PCB layout](docs/images/mkr/blank-shield/layout.png)](docs/images/mkr/blank-shield/layout.png) |

<details>
<summary>MKR Blank Shield layout with millimeter scale</summary>

[![MKR Blank Shield PCB outline on the Flux millimeter grid](docs/images/mkr/blank-shield/layout-with-scale.png)](docs/images/mkr/blank-shield/layout-with-scale.png)

</details>

### Arduino UNO R4

| Board | 3D view | PCB layout |
| --- | --- | --- |
| [UNO R4 Bench Breakout](boards/uno-r4/bench-breakout/) | [![UNO R4 Bench Breakout 3D view](docs/images/uno-r4/bench-breakout/3d.png)](docs/images/uno-r4/bench-breakout/3d.png) | [![UNO R4 Bench Breakout PCB layout](docs/images/uno-r4/bench-breakout/layout.png)](docs/images/uno-r4/bench-breakout/layout.png) |
| [UNO R4 Companion Shield](boards/uno-r4/companion-shield/) | [![UNO R4 Companion Shield 3D view](docs/images/uno-r4/companion-shield/3d.png)](docs/images/uno-r4/companion-shield/3d.png) | [![UNO R4 Companion Shield PCB layout](docs/images/uno-r4/companion-shield/layout.png)](docs/images/uno-r4/companion-shield/layout.png) |
| [UNO R4 Blank Shield](boards/uno-r4/blank-shield/) | [![UNO R4 Blank Shield 3D view](docs/images/uno-r4/blank-shield/3d.png)](docs/images/uno-r4/blank-shield/3d.png) | [![UNO R4 Blank Shield PCB layout](docs/images/uno-r4/blank-shield/layout.png)](docs/images/uno-r4/blank-shield/layout.png) |

## Stack enclosures

Both enclosures accept the prototyping shield or blank shield for their matching board family. The dimensions below are nominal. Both designs await a physical fit test.

| MKR stack enclosure | UNO R4 stack enclosure |
| --- | --- |
| [![MKR stack with the access lid installed](docs/images/mkr/stack-enclosure.png)](docs/images/mkr/stack-enclosure.png) | [![UNO R4 stack with the open bezel installed](docs/images/uno-r4/stack-enclosure.jpg)](docs/images/uno-r4/stack-enclosure.jpg) |
| **98 × 130 × 37.2 mm.** Print the base and one lid. The access lid exposes the prototyping area. The covered lid shelters it. | **132 × 120 × 43 mm.** Print the base and open bezel. The bezel lifts off to reach the shield. |
| [Printable STLs](enclosures/mkr/fabrication/) · [Assembly guide (PDF)](enclosures/mkr/drawings/MKR-Stack-Assembly-Guide.pdf) · [CAD and source](enclosures/mkr/) | [Printable STLs](enclosures/uno-r4/fabrication/) · [Assembly guide (PDF)](enclosures/uno-r4/drawings/UNO-R4-Stack-Assembly.pdf) · [CAD and source](enclosures/uno-r4/) |

## Source and licenses

The six board directories preserve the contents of the supplied Flux-labeled KiCad project archives. The accompanying KiCad library license notices are included in their original locations.
