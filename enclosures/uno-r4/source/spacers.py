"""Generate the two direct-stack register spacers in millimetres using CadQuery."""
from pathlib import Path
import cadquery as cq
from cadquery import exporters
ROOT = Path(__file__).resolve().parents[1]
GAP = 11.8
def box(x0,y0,z0,x1,y1,z1):
    return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,cq.Vector(x0,y0,z0))
def cyl(x,y,z,r,h):
    return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
def registered_spacer(relieved):
    # A diamond pilot relieves pitch tolerance along the line between the two holes.
    def pilot(z):
        s=cyl(0,0,z,1.57,1.0)
        if relieved:s=s.intersect(box(-2,-1.40,z,2,1.40,z+1))
        return s
    blank=cyl(0,0,0,2.00,GAP).fuse(pilot(-1)).fuse(pilot(GAP))
    return blank.cut(cyl(0,0,-1.1,1.10,GAP+2.2))

for name in ("Round", "Diamond"):
    solid = registered_spacer(name == "Diamond").translate((0, 0, 1))
    for folder, suffix in (("cad", "step"), ("fabrication", "stl")):
        target = ROOT / folder / ("Locating-Spacer-" + name + "." + suffix)
        exporters.export(solid, str(target), tolerance=0.015, angularTolerance=0.10)
