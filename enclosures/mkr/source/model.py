"""Rebuild the Rev A enclosure in millimetres using CadQuery 2.7.
Drawing coordinates use the carrier's upper left as XY = (0,0), with Y toward
the shield extension. Model Y is the opposite direction, matching native STEP.
"""
from pathlib import Path
import json, math
import cadquery as cq

ROOT=Path(__file__).resolve().parents[1]
PARAM={
 'revision':'A','outside_xy':[-9,-20,89,110],'corner_r':5.5,
 'floor':2.4,'wall':2.4,'rim_z':34.0,'lid_thickness':3.2,
 'carrier_under_z':8.4,'carrier_thickness':1.6,'face_gap':11.05,'shield_thickness':1.6,
 'board_mounts':[[4,4],[76,4],[4,52],[76,52]],
 'lid_mounts':[[-3,-14],[83,-14],[-3,104],[83,104]],
 'pcb_boss_radius':3.4,'lid_boss_radius':4.5,'pilot_d':2.60,
 'lid_hole_d':3.55,'front_open_x':[18,62],'front_sill_z':11.0,
 'side_open_y':[-5.5,51.4],'side_sill_z':8.8,
 'rear_open_x':[26,54],'rear_sill_z':22.0,
 'front_window':[-2.2,-15.5,82.2,51.35],'rear_window':[-1.2,55.25,81.2,101.8],
 'ledge_x':[[-2.2,1.30],[78.70,82.2]],'ledge_y':[[65,76],[91,98]],
 'ledge_clearance':0.45,'key_x':[[-6.23,-4.60],[84.60,86.23]],
 'key_y':[[57,65],[88,96]],'key_drop':2.6
}
P=PARAM
NAMES=['MKR-Stack-Base','MKR-Stack-Access-Lid','MKR-Stack-Covered-Lid']
def block(x0,y0,x1,y1,z0,z1,r=0):
    w=cq.Workplane('XY').box(x1-x0,y1-y0,z1-z0,centered=(True,True,False))
    if r:w=w.edges('|Z').fillet(r)
    return w.val().translate(((x0+x1)/2,-(y0+y1)/2,z0))
def cyl(x,y,z0,z1,r):
    return cq.Solid.makeCylinder(r,z1-z0,cq.Vector(x,-y,z0),cq.Vector(0,0,1))
def cone(x,y,z0,z1,r0,r1):
    return cq.Solid.makeCone(r0,r1,z1-z0,cq.Vector(x,-y,z0),cq.Vector(0,0,1))
def outside(z0,z1):
    return block(*P['outside_xy'],z0,z1,P['corner_r'])
def make_base():
    x0,y0,x1,y1=P['outside_xy'];w=P['wall'];rim=P['rim_z'];under=P['carrier_under_z']
    base=outside(0,rim).cut(block(x0+w,y0+w,x1-w,y1-w,P['floor'],rim+1,P['corner_r']-w))
    # Sills are open upward to allow cable installation before the lid goes on.
    a,b=P['front_open_x'];base=base.cut(block(a,y0-1,b,y0+w+1,P['front_sill_z'],rim+1))
    a,b=P['side_open_y']
    for u,v in [(x0-1,x0+w+1),(x1-w-1,x1+1)]:
        base=base.cut(block(u,a,v,b,P['side_sill_z'],rim+1))
    a,b=P['rear_open_x'];base=base.cut(block(a,y1-w-1,b,y1+1,P['rear_sill_z'],rim+1))
    adds=[cyl(x,y,0,rim,P['lid_boss_radius']) for x,y in P['lid_mounts']]
    adds.extend(cyl(x,y,0,under,P['pcb_boss_radius']) for x,y in P['board_mounts'])
    shield_under=under+P['carrier_thickness']+P['face_gap']
    for x0,x1 in P['ledge_x']:
        for y0,y1 in P['ledge_y']:
            adds.append(block(x0,y0,x1,y1,0,shield_under-P['ledge_clearance'],.75))
    base=base.fuse(*adds).clean()
    holes=[]
    for pts,upper,bottom in [(P['lid_mounts'],rim,rim-9),(P['board_mounts'],under,1.35)]:
        for x,y in pts:
            holes.extend([cyl(x,y,bottom,upper+1,P['pilot_d']/2),
                          cone(x,y,upper-.40,upper,P['pilot_d']/2,P['pilot_d']/2+.40)])
    return base.cut(*holes).clean()
def make_lid(open_rear):
    z=P['rim_z'];t=P['lid_thickness'];x0,y0,x1,y1=P['outside_xy']
    lid=outside(z,z+t)
    lid=lid.cut(block(*P['front_window'],z-1,z+t+1,2.0))
    a,b=P['front_open_x'];lid=lid.cut(block(a,y0-1,b,P['front_window'][1]+3,z-1,z+t+1))
    if open_rear:lid=lid.cut(block(*P['rear_window'],z-1,z+t+1,1.5))
    lugs=[block(a,c,b,d,z-P['key_drop'],z+.1,.38) for a,b in P['key_x'] for c,d in P['key_y']]
    lid=lid.fuse(*lugs).clean()
    return lid.cut(*(cyl(x,y,z-1,z+t+1,P['lid_hole_d']/2) for x,y in P['lid_mounts'])).clean()
def print_pose(shape,lid):
    if lid:shape=shape.rotate((0,0,0),(1,0,0),180)
    b=shape.BoundingBox()
    return shape.translate((-b.xmin,-b.ymin,-b.zmin))
def export():
    parts=[make_base(),make_lid(True),make_lid(False)]
    for dirname in ('cad','fabrication','checks','setup'):(ROOT/dirname).mkdir(exist_ok=True,parents=True)
    for i,(name,shape) in enumerate(zip(NAMES,parts)):
        assert shape.isValid() and len(shape.Solids())==1 and shape.Volume()>0
        cq.exporters.export(shape,str(ROOT/'cad'/(name+'.step')))
        out=print_pose(shape,i!=0)
        out.exportStl(str(ROOT/'fabrication'/(name+'.stl')),tolerance=.035,angularTolerance=.12,ascii=False,relative=False)
    (ROOT/'setup'/'Dimensions.json').write_text(json.dumps(P,indent=2)+'\n')
if __name__=='__main__':export()
