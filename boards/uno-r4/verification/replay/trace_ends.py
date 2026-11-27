"""Check each routed segment end against other same-net copper on the same layer."""
from pathlib import Path
from collections import Counter
import json
import sys
import pcbnew as k

base=Path(sys.argv[1])
for project in sorted((base/'tmp').glob('*/project')):
    board=k.LoadBoard(str(next(project.glob('*.kicad_pcb'))))
    tracks=list(board.GetTracks())
    pads=[p for f in board.GetFootprints() for p in f.Pads() if p.GetNumber()]
    result=Counter()
    for index,segment in enumerate(tracks):
        if isinstance(segment,k.PCB_VIA):
            continue
        net=segment.GetNetCode(); layer=segment.GetLayer()
        for end in (segment.GetStart(),segment.GetEnd()):
            if any(p.GetNetCode()==net and p.IsOnLayer(layer) and p.HitTest(end,0) for p in pads):
                result['on_pad']+=1
                continue
            adjacent=[t for i,t in enumerate(tracks) if i!=index and t.GetNetCode()==net and t.IsOnLayer(layer) and t.HitTest(end,0)]
            assert adjacent,(project.name,segment.GetNetname(),end)
            result['on_via' if any(isinstance(t,k.PCB_VIA) for t in adjacent) else 'on_other_track']+=1
    path=base/'evidence'/project.parent.name/'trace-ends.json'
    path.write_text(json.dumps(dict(checked=sum(result.values()),counts=dict(result),dangling=0),indent=2)+'\n')
    print(project.parent.name,result)
