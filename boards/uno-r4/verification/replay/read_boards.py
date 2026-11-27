"""Read electrical pad locations and side placements directly from KiCad and Altium boards."""
from pathlib import Path
import hashlib
import json
import sys
import pcbnew as k

base=Path(sys.argv[1])
refs=Path(sys.argv[2]) if len(sys.argv)>2 else None
def xy(item):
    position = item.GetPosition()
    return [position.x / 1e6, position.y / 1e6]

for work in sorted((base/'tmp').glob('*/project')):
    board = k.LoadBoard(str(next(work.glob('*.kicad_pcb'))))
    pads, holes, tracks = [], [], []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            location = xy(pad)
            drill = pad.GetDrillSize()
            if drill.x:
                assert drill.x == drill.y
                holes.append([*location, drill.x/1e6, 'NPTH' if pad.GetAttribute()==k.PAD_ATTRIB_NPTH else 'PTH'])
            if pad.GetNumber():
                pads.append(dict(ref=fp.GetReference(), pin=pad.GetNumber(), net=pad.GetNetname(), xy=location,
                    drill=drill.x/1e6, copper=[side for side,layer in [('F',k.F_Cu),('B',k.B_Cu)] if pad.IsOnLayer(layer)],
                    mount=board.GetLayerName(fp.GetLayer()),part=fp.GetValue()))
    vias=0
    for track in board.GetTracks():
        if isinstance(track,k.PCB_VIA):
            vias+=1
            holes.append([*xy(track),track.GetDrillValue()/1e6,'PTH'])
        else:
            tracks.append(board.GetLayerName(track.GetLayer()))
    path=base/'evidence'/work.parent.name/'pad-inventory.json'
    silk=[dict(text=d.GetText(),xy=xy(d)) for d in board.GetDrawings() if isinstance(d,k.PCB_TEXT) and d.GetLayer()==k.F_SilkS]
    path.write_text(json.dumps(dict(pads=pads,holes=holes,vias=vias,tracks=tracks,silk=silk),indent=1)+'\n')
if refs is None:
    sys.exit(0)
records={}
for model, file in [('Minima','minima.PcbDoc'),('WiFi','wifi.PcbDoc')]:
    path=refs/file
    plugin=k.PCB_IO_MGR.PluginFind(k.PCB_IO_MGR.ALTIUM_DESIGNER)
    board=plugin.LoadBoard(str(path.resolve()),None)
    wanted={'JDIGITAL','JANALOG','J1','J2'} if model=='Minima' else {'JDIGITAL','JANALOG','J2','J3','J6','JOFF'}
    connectors={}
    for fp in board.GetFootprints():
        if fp.GetReference() in wanted:
            connectors[fp.GetReference()]={p.GetNumber():dict(net=p.GetNetname(),xy=xy(p)) for p in fp.Pads() if p.GetNumber()}
    assert wanted==set(connectors)
    records[model]=dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),connectors=connectors)
(base/'evidence'/'arduino-original-layouts.json').write_text(json.dumps(records,indent=1)+'\n')
