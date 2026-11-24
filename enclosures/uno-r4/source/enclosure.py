"""UNO R4 stack enclosure, Rev A. All model and interface coordinates are millimetres."""
from pathlib import Path
import json
import math
import shutil
import tempfile
import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
INTERFACE = json.loads((ROOT / 'source/interfaces.json').read_text())
W, D = 132.0, 120.0
CORNER, WALL, FLOOR = 6.5, 2.8, 3.2
SEAT, RIM, RIM_WIDTH = 40.0, 3.0, 6.5
UNO_SEAT, NUT_ROOF = 10.0, 3.8
CARRIER_BOSS, HEAD_SEAT = 6.3, 3.25
TOWER_OFFSET, TOWER_RADIUS = 6.6, 5.2
TOWERS = [(x,y) for x in [TOWER_OFFSET,W-TOWER_OFFSET] for y in [TOWER_OFFSET,D-TOWER_OFFSET]]
PORT_BAY = (28.0,86.5)
NORTH_SOUTH = (16.0,85.0)
EAST = (12.0,110.0)
QWIIC = (39.0,56.0)
WIRE_SILL, QWIIC_SILL = 14.0, 6.4
def case_xy(p):
    return (round(p[0]-92.0,5),round(133.0-p[1],5))
UNO_ALL = [case_xy(p) for p in INTERFACE['uno_holes']]
UNO = [UNO_ALL[i] for i in (0,2,3)]
# Shift only the U1 screw axis inside the 3.2 mm PCB hole, away from the DC jack.
UNO_BORES = [(UNO[0][0] + 0.35, UNO[0][1]), *UNO[1:]]
CARRIER = [case_xy(p) for p in INTERFACE['breakout_holes']]

def box(x0,y0,z0,x1,y1,z1):
    return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,cq.Vector(x0,y0,z0))
def cyl(x,y,z0,z1,r):
    return cq.Solid.makeCylinder(r,z1-z0,cq.Vector(x,y,z0))
def rounded(x0,y0,z0,x1,y1,z1,r):
    s=box(x0,y0,z0,x1,y1,z1)
    return cq.Workplane(obj=s).edges('|Z').fillet(r).val()
def rounded_notch(x0,y0,z0,x1,y1,z1,r,axis):
    s=box(x0,y0,z0,x1,y1,z1)
    return cq.Workplane(obj=s).edges('|'+axis+' and <Z').fillet(r).val()
def hexagon(x,y,z0,z1,af):
    r=af/math.sqrt(3.0)
    poly=[(x+r*math.sin(math.pi*i/3),y+r*math.cos(math.pi*i/3)) for i in range(6)]
    return cq.Workplane('XY',origin=(0,0,z0)).polyline(poly).close().extrude(z1-z0).val()
def make_case():
    outside=rounded(0,0,0,W,D,SEAT,CORNER)
    inside=rounded(WALL,WALL,FLOOR,W-WALL,D-WALL,SEAT+2,CORNER-WALL)
    tray=outside.cut(inside)
    # Lower wall openings are open at the top until the independent guard is fitted.
    a,b=NORTH_SOUTH
    cuts=[rounded_notch(a,-2,WIRE_SILL,b,WALL+1,SEAT+2,3,'Y'),
          rounded_notch(a,D-WALL-1,WIRE_SILL,b,D+2,SEAT+2,3,'Y'),
          rounded_notch(-1,PORT_BAY[0],FLOOR,WALL+1,PORT_BAY[1],SEAT+2,3,'X'),
          rounded_notch(W-WALL-1,EAST[0],WIRE_SILL,W+2,EAST[1],SEAT+2,3,'X'),
          rounded_notch(W-WALL-1,QWIIC[0],QWIIC_SILL,W+2,QWIIC[1],SEAT+2,2,'X')]
    tray=tray.cut(*cuts)
    # M2 nuts enter from the bottom. The smaller seat leaves room around the UNO headers.
    bosses=[]
    for x,y in UNO:
        bosses += [cyl(x,y,0,7.5,4.25),
                   cq.Solid.makeCone(4.25,2.55,2.5,cq.Vector(x,y,7.5))]
    for x,y in CARRIER:
        bosses.append(cyl(x,y,0,CARRIER_BOSS,5.1))
    for x,y in TOWERS:
        bosses.append(cyl(x,y,0,SEAT,TOWER_RADIUS))
    tray=tray.fuse(*bosses)
    bores=[]
    for x,y in UNO_BORES:
        bores += [cyl(x,y,-1,UNO_SEAT+1,1.125),hexagon(x,y,-1,NUT_ROOF,4.26)]
    for x,y in CARRIER:
        bores += [cyl(x,y,-1,CARRIER_BOSS+1,1.7),cyl(x,y,-1,HEAD_SEAT,3.3)]
    for x,y in TOWERS:
        # The side opening captures the nut between two flats. The roof is a 5.85 mm print bridge.
        af=5.85
        y0,y1=(y,y+7) if y<D/2 else (y-7,y)
        bores += [cyl(x,y,33.8,SEAT+1,1.72),hexagon(x,y,35.45,38.15,af),
                  box(x-af/2,y0,35.45,x+af/2,y1,38.15)]
    tray=tray.cut(*bores).clean()
    outside=rounded(0,0,0,W,D,RIM,CORNER)
    inner=rounded(RIM_WIDTH,RIM_WIDTH,-.5,W-RIM_WIDTH,D-RIM_WIDTH,RIM+.5,4.1)
    guard=outside.cut(inner).fuse(*[cyl(x,y,0,RIM,TOWER_RADIUS) for x,y in TOWERS])
    guard=guard.cut(*[cyl(x,y,-.5,RIM+.5,1.75) for x,y in TOWERS]).clean()
    return tray,guard

def write_files():
    from cad_bundle import export_bundle
    paths={k:ROOT/k for k in ('cad','checks','fabrication')}
    for p in paths.values():p.mkdir(exist_ok=True)
    for label,solid in zip(['Base','Bezel'],make_case()):
        name='UNO-R4-Stack-'+label
        with tempfile.TemporaryDirectory() as scratch:
            p=Path(scratch)/'part'
            result=export_bundle(solid,p,name,revision='A',mesh_formats=('stl',),linear_tolerance_mm=.025,angular_tolerance_rad=.12)
            if result['geometry_status']!='PASS':raise RuntimeError(result['errors'])
            shutil.copyfile(next((p/'prototypes').glob('*.stl')),paths['fabrication']/(name+'.stl'))
            shutil.copyfile(next((p/'cad').glob('*.step')),paths['cad']/(name+'.step'))
            shutil.copyfile(p/'validation.json',paths['checks']/(label+'-geometry.json'))
        print(name,round(solid.Volume(),1),flush=True)
if __name__=='__main__':write_files()
