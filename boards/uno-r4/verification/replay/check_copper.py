"""Extract electrical connectivity from Gerber geometry and plated drill hits in millimetres."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
import warnings
import xml.etree.ElementTree as ET
from gerbonara import GerberFile, ExcellonFile
from gerbonara import graphic_primitives as gp
from gerbonara.utils import MM
from shapely import STRtree, union_all
from shapely.affinity import rotate
from shapely.geometry import Point, LineString, Polygon, box

base = Path(sys.argv[1])
res = 64
def disk(x,y,r):
    return Point(x,y).buffer(r,quad_segs=res)

def shape(p):
    if not p.polarity_dark:
        raise ValueError('Unexpected clear primitive; review Gerber compositing.')
    if isinstance(p,gp.Circle):
        return disk(p.x,p.y,p.r)
    if isinstance(p,gp.Line):
        return LineString([(p.x1,p.y1),(p.x2,p.y2)]).buffer(p.width/2,quad_segs=res)
    if isinstance(p,gp.Rectangle):
        rect=box(p.x-p.w/2,p.y-p.h/2,p.x+p.w/2,p.y+p.h/2)
        return rotate(rect,p.rotation,origin=(p.x,p.y),use_radians=True)
    if isinstance(p,gp.ArcPoly):
        return Polygon(p.approximate_arcs(0.0001).outline)
    raise TypeError(type(p))

def classify(copper,bores,pads):
    cuts=union_all([disk(x,y,r) for x,y,r,kind in bores])
    pieces=[]; trees={}; offsets={}
    for side,raw in copper.items():
        metal=raw.difference(cuts)
        side_polys=list(metal.geoms) if metal.geom_type=='MultiPolygon' else [metal]
        assert all(p.geom_type=='Polygon' and p.area>1e-8 for p in side_polys)
        trees[side]=STRtree(side_polys)
        offsets[side]=len(pieces)
        pieces.extend(side_polys)
    group=list(range(len(pieces)))
    def root(i):
        while i!=group[i]:
            group[i]=group[group[i]]
            i=group[i]
        return i
    def member(side, probe):
        candidates=trees[side].query(probe,predicate='intersects')
        assert len(candidates)==1,(side,probe.bounds,candidates)
        return int(candidates[0])+offsets[side]
    holes={}
    key=lambda x,y:(round(x,5),round(y,5))
    for x,y,r,kind in bores:
        if kind=='PTH':
            ring=disk(x,y,r+.012).difference(disk(x,y,r+.002))
            front=member('F',ring); back=member('B',ring)
            for i in (front,back):
                assert pieces[i].covers(ring), ('incomplete plated annulus',x,y,i)
            group[root(back)]=root(front)
            holes[key(x,y)]=front
    net_groups=defaultdict(set); group_nets=defaultdict(set)
    for p in pads:
        x, native_y=p['xy']; y=-native_y
        if p['drill']:
            island=root(holes[key(x,y)])
        else:
            assert len(p['copper'])==1
            island=root(member(p['copper'][0],Point(x,y)))
        net_groups[p['net']].add(island); group_nets[island].add(p['net'])
    opens=sorted(n for n,g in net_groups.items() if len(g)>1)
    shorts=sorted(sorted(v) for v in group_nets.values() if len(v)>1)
    roots={root(i) for i in range(len(pieces))}
    return dict(opens=opens,shorts=shorts,orphan_islands=len(roots-set(group_nets)),islands=len(roots))

def check(work):
    ev=base/'evidence'/work.name
    fab=work/'fab'; fresh=work/'fresh'
    inventory=json.loads((ev/'pad-inventory.json').read_text())
    schematic={e.get('name'):{(n.get('ref'),n.get('pin')) for n in e.findall('node')} for e in ET.parse(ev/'Netlist.xml').findall('nets/net')}
    native=defaultdict(set)
    for p in inventory['pads']:
        native[p['net']].add((p['ref'],p['pin']))
    assert schematic==native
    reports={}
    for name in ('ERC','DRC'):
        obj=json.loads((ev/(name+'.json')).read_text())
        reports[name]=obj['violations'] if name=='DRC' else [v for s in obj['sheets'] for v in s['violations']]
        assert not reports[name]
        if name=='DRC':
            assert not obj['unconnected_items'] and not obj['schematic_parity']
    copper={}; bores=[]; normalized={}
    def artwork_digest(p):
        lines=p.read_text().splitlines()
        metadata=('%TF.CreationDate,','G04 Created by KiCad','; DRILL file {KiCad','; #@! TF.CreationDate,')
        return hashlib.sha256('\n'.join(l for l in lines if not l.startswith(metadata)).encode()).hexdigest()
    for p in sorted(fab.iterdir()):
        if p.suffix not in ('.gtl','.gbl','.drl'):continue
        normalized[p.name]=artwork_digest(p)
        assert normalized[p.name]==artwork_digest(fresh/p.name)
        if p.suffix=='.drl':
            drill=ExcellonFile.open(p)
            for obj in drill.objects:
                primitives=list(obj.to_primitives(MM))
                assert len(primitives)==1 and isinstance(primitives[0],gp.Circle)
                q=primitives[0]
                bores.append((q.x,q.y,q.r, 'NPTH' if '-NPTH.' in p.name else 'PTH'))
        else:
            g=GerberFile.open(p)
            copper['F' if p.suffix=='.gtl' else 'B']=union_all([shape(q) for o in g.objects for q in o.to_primitives(MM)])
    for p in fresh.glob('*.drl'):
        if not (fab/p.name).exists():
            assert '-NPTH.' in p.name and len(ExcellonFile.open(p).objects)==0
    round_hole=lambda x,y,d,k:(round(x,5),round(y,5),round(d,5),k)
    assert Counter(round_hole(x,y,r*2,k) for x,y,r,k in bores)==Counter(round_hole(x,-y,d,k) for x,y,d,k in inventory['holes'])
    result=classify(copper,bores,inventory['pads'])
    assert not result['opens'] and not result['shorts'] and result['orphan_islands']==0 and result['islands']==len(schematic), result
    result.update(physical_pads=len(inventory['pads']),schematic_nets=len(native),track_segments=dict(Counter(inventory['tracks'])),vias=inventory['vias'],drills=dict(Counter(b[-1] for b in bores)),normalized_fab_sha256=normalized)
    if work.name=='bench-breakout':
        # These in-memory edits are to actual copper at the digital-low row; do not modify release files.
        broken=copper['F'].difference(box(163,-35,164,-34.9))
        injected=classify({**copper,'F':broken},bores,inventory['pads'])
        assert injected['opens']==['/D0_RX'] and not injected['shorts'],injected
        bridged=copper['F'].union(LineString([(160.96,-40.8),(163.5,-40.8)]).buffer(.15))
        injected_short=classify({**copper,'F':bridged},bores,inventory['pads'])
        assert injected_short['shorts']==[['/D0_RX','/D1_TX']] and not injected_short['opens'],injected_short
        result['negative_controls']={'cut_D0':injected,'bridge_D0_to_D1':injected_short}
    (ev/'copper-test.json').write_text(json.dumps(result,indent=2)+'\n')
    print(work.name, result['islands'],result['drills'],result['opens'],result['shorts'],flush=True)
warnings.filterwarnings('ignore',message='.*G90 header statement found after end of header',category=SyntaxWarning)
for w in sorted((base/'tmp').iterdir()):
    if (w/'fab').is_dir():
        check(w)
