# Arduino MKR and UNO R4 breakout boards and prototyping shields

Six PCB designs from Green Shoe Garage cover two Arduino families. Each family includes a base board, a prototyping shield with a solder grid, and a blank shield for custom components. Each base board brings Arduino pins out to headers and 2.54 mm screw terminals. Both shield variants plug into the headers on their matching base board.

| Family | Base board | Prototyping shield | Blank workspace shield |
| --- | --- | --- | --- |
| Arduino MKR | [MKR Terminal Carrier](boards/mkr/terminal-carrier/) breaks out the two 14-pin rows, using the MKR WiFi 1010 as its reference. | [MKR Carrier ProtoShield](boards/mkr/protoshield/) has a 7 × 25 prototyping grid. Its underside sockets J1 and J2 mate with carrier headers J3 and J4, respectively. | [MKR Blank Shield](boards/mkr/blank-shield/) leaves the center open for component footprints and routing. It retains the two 14-pin underside sockets and two M3 mounting holes. |
| Arduino UNO R4 | [UNO R4 Bench Breakout](boards/uno-r4/bench-breakout/) exposes the standard headers and ICSP, with auxiliary banks marked for the WiFi and Minima variants. | [UNO R4 Companion Shield](boards/uno-r4/companion-shield/) has underside sockets for the breakout headers, labeled solder rows, and a 12 × 15 prototyping grid. | [UNO R4 Blank Shield](boards/uno-r4/blank-shield/) leaves the prototyping area open for component footprints and routing. It retains the nine underside socket banks and their labeled solder rows. |

## Open a board

Download or clone the repository. In KiCad 9, open the `.kicad_pro` file in the chosen board directory, then launch the Schematic Editor or PCB Editor from the project window. Keep the whole directory together when copying a board or packaging it individually. The symbol and footprint tables resolve paths relative to the project.

All three MKR projects and both UNO R4 shield projects include local STEP models. The UNO R4 Bench Breakout references the standard KiCad 9 model library through `KICAD9_3DMODEL_DIR` for its 3D view.

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

## Source and licenses

The six board directories preserve the contents of the supplied Flux-labeled KiCad project archives. The accompanying KiCad library license notices are included in their original locations.
