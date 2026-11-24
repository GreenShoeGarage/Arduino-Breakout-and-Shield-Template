from pathlib import Path
import argparse, json, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
parser=argparse.ArgumentParser(description='Check the enclosure against the source assembly STEP files.')
parser.add_argument('--wifi-step',type=Path,required=True)
parser.add_argument('--blank-step',type=Path,required=True)
parser.add_argument('--proto-step',type=Path,required=True)
args=parser.parse_args()
from enclosure import *
from cadquery import importers
from itertools import chain

base=importers.importStep(str(ROOT/'cad/UNO-R4-Stack-Base.step')).val()
bezel=importers.importStep(str(ROOT/'cad/UNO-R4-Stack-Bezel.step')).val().translate((0,0,SEAT))
case=cq.Compound.makeCompound([base,bezel]); out={}
def overlap(a,b):
    return a.intersect(b).Volume()
def require_clear(a,b,m,limit=1e-4):
    v=overlap(a,b)
    if v>limit: raise AssertionError((m,v))
    return round(v,6)
def poly(points,z,h):
    return cq.Workplane('XY',origin=(0,0,z)).polyline([case_xy(p) for p in points]).close().extrude(h).val()
def shape_for(g,z,h):
    board=poly(g['outline'],z,h)
    for ring in g.get('windows',[]):board=board.cut(poly(ring,z-1,h+2))
    return board
def ext(sh):
    bb=sh.BoundingBox();return [round(x,4) for x in (bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax)]
def disjoint(a,b):
    return any(a[k+3]<b[k]+1e-5 or b[k+3]<a[k]+1e-5 for k in range(3))
def check_bundle(shapes,other,name):
    comp=cq.Compound.makeCompound(shapes)
    return require_clear(comp,other,name)

# All potentially loaded heights use the UNO top as reference.
under_range=[21.1,24.6]
carrier=poly(INTERFACE['breakout_outline'],under_range[0],under_range[1]-under_range[0]+1.6)
out['carrier_height_range_bed_to_underside_mm']=under_range
out['carrier_swept_clearance_to_housing_mm']=round(case.distance(carrier),3)
assert out['carrier_swept_clearance_to_housing_mm']>.3
variants=[(name,shape_for(g,under_range[0]+1.6+11.05,under_range[1]-under_range[0]+1.6)) for name,g in INTERFACE['variants'].items()]
for name,v in variants:
    require_clear(v,case,name)
# Full populated shield STEP envelopes embedded in the board frame. Include all socket bodies and tails.
for name,shift in [('blank',(-92.,133.)),('proto',(20.4,104.5))]:
    path=args.blank_step if name=='blank' else args.proto_step
    step=importers.importStep(str(path)).val()
    dims=ext(step)
    env=box(dims[0]+shift[0],dims[1]+shift[1],dims[2]+under_range[0]+1.6+11.05,
            dims[3]+shift[0],dims[4]+shift[1],dims[5]+under_range[1]+1.6+11.05)
    out[name+'_populated_envelope_clearance_mm']=round(case.distance(env),3)
    assert out[name+'_populated_envelope_clearance_mm']>0.9
# Verify complete connector footprint courtyards and model-specific example cable envelopes from the released CAD.
courts=INTERFACE['parent_courts']
access=[]
for r,b in courts.items():
    if r.startswith('TB') or r in ('J1','J2','J3','J4','J6','J7','J8','J9'):
        x0,y0=case_xy([b[0],b[3]]);x1,y1=case_xy([b[2],b[1]])
        access.append(box(x0,y0,22.7,x1,y1,54))
check_bundle(access,case,'bank vertical access')
for name,v in variants:check_bundle(access,v,'bank access vs '+name)
for name,data in INTERFACE['variants'].items():
    plugs=[]
    for b in data['plug_envelopes'].values():
        x0,y0=case_xy([b[0],b[3]]);x1,y1=case_xy([b[2],b[1]])
        plugs.append(box(x0,y0,22.7,x1,y1,55))
    check_bundle(plugs,case,'aux-plug drops')
# A 4 mm screwdriver shaft at all 61 screw centers and a 3 mm diameter straight wire-entry path.
tools=[];wires=[]
for r,num,x0,y0 in INTERFACE['terminals']:
    x,y=case_xy([x0,y0]);i=int(r[2:])
    tools.append(cyl(x,y,27.0,55,2))
    if i in [1,2]:a=box(x-1.5,y-1,23.0,x+1.5,122,34.0)
    elif i in [3,4,6]:a=box(x-1.5,-2,23.0,x+1.5,y+1,34.0)
    else:a=box(x-1,y-1.5,23.0,134,y+1.5,34.0)
    wires.append(a)
check_bundle(tools,case,'all screwdrivers')
check_bundle(wires,case,'all wires')
for name,v in variants:check_bundle(tools,v,'all screwdrivers plus '+name)
# All top solder-pad centers, and the 180 proto holes where fitted, have direct vertical access through the case.
for name,data in INTERFACE['variants'].items():
    pads=[q for q in data['pads'] if q[0].startswith(('P','G'))]
    out[name+'_exposed_solder_and_proto_positions']=len(pads)
    bounds=[case_xy([q[2],q[3]]) for q in pads]
    assert all(14<x<119 and 14<y<106 for x,y in bounds)
    require_clear(box(min(x for x,y in bounds)-.8,min(y for x,y in bounds)-.8,34,
                      max(x for x,y in bounds)+.8,max(y for x,y in bounds)+.8,57),case,'probe field')
rx,ry=case_xy(INTERFACE['uno_ports']['reset'])
probe=cyl(rx,ry,13.0,56,1.35)
require_clear(probe,carrier,'reset path above pushbutton')
for name,v in variants:require_clear(probe,v,'reset path plus '+name)
require_clear(probe,case,'reset vs case')
ports={'USB-C (20 x 10 mm plug body)':box(-9,70.87-10,7.9,7.14,70.87+10,17.9),
       'barrel (17 mm plug-body envelope)':box(-12,41.16-8.5,8.1,6.04,41.16+8.5,25.1),
       'east low Qwiic cable path (8 x 5 mm)':box(77,47.35-4,10.0,135,47.35+4,15)}
for p,b in ports.items():require_clear(case,b,p)
# Check all bores penetrate the proper printed members. Positive annular material is required at each supporting seat.
for (x,y),(px,py) in zip(UNO_BORES,UNO):
    assert math.hypot(px-x,py-y) + 1.125 < 1.599, 'Check shaft float inside host hole'
    require_clear(cyl(x,y,-1,10.1,1.10),base,'UNO bore')
    assert base.isInside(cq.Vector(x+2.1,y,9.8))
for x,y in CARRIER:
    require_clear(cyl(x,y,-1,6.4,1.65),base,'breakout bore')
    assert base.isInside(cq.Vector(x+3.65,y,5.7))
for x,y in TOWERS:
    require_clear(cyl(x,y,34,44,1.65),case,'bezel bore')
    assert base.isInside(cq.Vector(x+2.35,y,39.4))
# Details of the official WiFi STEP placed on the three UNO seats. Whole assembly includes barrel-jack tails.
host=importers.importStep(str(args.wifi_step)).val().translate((8.,33.,11.61))
outer=ext(host)
eligible=0; tested=0;total=0
heads=[cyl(x,y,11.612,13.812,2.04) for x,y in UNO_BORES]
# The base consists of the floor, perimeter walls, four corner towers and seven mounting bosses.
# Reject disjoint bounding boxes before costly exact solid intersections.
regions=[box(0,0,0,W,D,FLOOR),box(0,0,FLOOR,WALL,D,40),box(W-WALL,0,FLOOR,W,D,40),
         box(0,0,FLOOR,W,WALL,40),box(0,D-WALL,FLOOR,W,D,40)]
regions+=[cyl(x,y,0,40,TOWER_RADIUS) for x,y in TOWERS]+[cyl(x,y,0,10,4.25) for x,y in UNO]+[cyl(x,y,0,6.3,5.1) for x,y in CARRIER]
rboxes=[ext(e) for e in regions];hboxes=[ext(e) for e in heads]
for solid in host.Solids():
    total+=1;b=ext(solid)
    if any(not disjoint(b,g) for g in rboxes):
        eligible+=1;require_clear(base,solid,'WiFi populated body '+str(b),.0002)
    for h,hb in zip(heads,hboxes):
        if not disjoint(b,hb):
            tested+=1;require_clear(h,solid,'UNO screw head '+str(b),.0002)
out.update(host_wifi_bounds_mm=outer,host_wifi_solids=total,host_exact_collision_candidates=eligible,host_head_exact_collision_candidates=tested,
           three_mount_head_envelope_diameter_mm=4.08,reset_probe_diameter_mm=2.7,top_terminal_screwdriver_tests=len(tools),terminal_wire_entry_tests=len(wires),
           cable_plug_envelopes=list(ports),carrier_and_host_mounts_mm={'uno':UNO,'breakout':CARRIER},
           upper_headers_and_auxiliary_banks='All 9 terminal and 8 top-side connector courtyards clear on both variants',
           status='pass',machine_sliced=False,printed=False)
(ROOT/'checks/access-and-fit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
