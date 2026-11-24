"""Check closed slice contours in the saved, millimetre-native STLs; this is a geometry check."""
from pathlib import Path
from collections import Counter
import json, math, numpy as np
from cad_bundle import _read_stl
base=Path(__file__).resolve().parents[1];report={}
for file in sorted((base/'fabrication').glob('*.stl')):
    vv,ff=_read_stl(file);vs=np.array(vv);tris=np.array(ff);parent=list(range(len(vs)))
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,j,k in ff:
        parent[root(i)]=root(j);parent[root(k)]=root(j)
    assert len({root(i) for i in range(len(vs))})==1
    t=vs[tris];zmin=t[:,:,2].min(axis=1);zmax=t[:,:,2].max(axis=1)
    count=0; largest=0
    for z in np.arange(.1007,np.max(vs[:,2]),.2):
        active=t[(zmin<z)&(zmax>z)]
        degree=Counter()
        for a,b in [(0,1),(1,2),(2,0)]:
            aa,bb=active[:,a],active[:,b];mask=(aa[:,2]<z)!=(bb[:,2]<z)
            aa,bb=aa[mask],bb[mask]
            if len(aa)==0:continue
            flip=aa[:,2]>bb[:,2]
            lo=np.where(flip[:,None],bb,aa);hi=np.where(flip[:,None],aa,bb)
            pts=lo[:,:2]+(hi[:,:2]-lo[:,:2])*((z-lo[:,2])/(hi[:,2]-lo[:,2]))[:,None]
            for pt in np.rint(pts*1e7).astype(np.int64):degree[tuple(pt)]+=1
        assert degree and all(d==2 for d in degree.values()),(file,z)
        largest=max(largest,len(degree));count+=1
    report[file.name]={'connected_surface_count':1,'slice_spacing_mm':.2,'closed_sections':count,'non_closed_sections':0,'largest_section_segments':largest,'bounds_mm':[list(vs.min(axis=0)),list(vs.max(axis=0))]}
(base/'checks/print-sections.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)
