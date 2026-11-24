# MKR stack enclosure • Rev A

Print **MKR-Stack-Base.stl** and **one lid** from the fabrication folder. The Access Lid is the choice for prototyping. All STLs are in millimetres and oriented for printing at 100% scale. Open drawings/MKR-Stack-Assembly-Guide.pdf for hardware and assembly.

## Supported stacks

The lower PCB is the Rev A MKR Terminal Carrier (80 × 56 mm) with the Arduino MKR WiFi 1010 in its center sockets. The carrier's outboard headers accept either the Rev A Blank Shield or the Rev A ProtoShield. Case clearance for the Arduino uses its module envelope and port locations. Other MKR variants, accessory plugs and custom circuits may have different envelopes. Physical fit has yet to be tested.

The Access Lid exposes both banks of screw terminals, the MKR headers, the reset and front accessory ports, plus the full 76 × 42 mm space on the Blank Shield or the 25 × 7 ProtoShield grid. The Covered Lid shelters the rear area with 11.35 mm nominal headroom. Male carrier pins engage the shield's bottom sockets. Access to their board-level signals remains via the carrier terminal banks and the shield lands. The case has open wiring bays.

## Files

* fabrication/ contains the three printable STLs.
* cad/ contains exact STEP solids in assembled coordinates for mechanical editing.
* source/model.py is the CadQuery 2.7 generator. Run python source/model.py from the extracted project to recreate CAD, STLs and dimensions.
* setup/Dimensions.json gives the nominal dimensions. CAD uses the carrier's front-left PCB corner as the XY origin. Positive drawing Y runs toward the custom area and corresponds to negative CAD Y.
* checks/Geometry-and-fit.json records mesh topology and intersections against the released PCB STEP assemblies. checks/Slicing.json records H2S PETG reference slices for the individual STLs.
* drawings/ contains the two-page guide. previews/ shows the Blank Shield installed with the Access Lid.

Use two M3 × 6 mm screws through the carrier's front holes, two 11 mm M3 male/female spacers at its rear holes, two M3 × 6 mm screws for the shield, and four M3 × 8 mm screws for the lid. Match the spacer length to the actual gap between fully seated PCBs before tightening. The nominal case is 98 × 130 × 37.2 mm excluding screw heads.
