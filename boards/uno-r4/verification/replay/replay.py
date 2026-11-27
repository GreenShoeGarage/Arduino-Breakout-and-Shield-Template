"""Reproduce this release check in a new directory beside the extracted audit bundle."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

parser=argparse.ArgumentParser()
parser.add_argument('output',type=Path,help='New directory for regenerated files')
parser.add_argument('--pcb-python',default='/usr/bin/python3',help='Python executable that imports pcbnew')
parser.add_argument('--arduino-dir',type=Path,help='Optional directory with minima.PcbDoc and wifi.PcbDoc')
args=parser.parse_args()
here=Path(__file__).resolve().parent
root=here.parent
base=args.output.resolve()
base.mkdir(parents=True,exist_ok=False)
def run(args):subprocess.run(list(map(str,args)),check=True)
manifest=json.loads((root/'evidence'/'inputs.json').read_text())
(base/'evidence').mkdir()
(base/'output').mkdir()
shutil.copy2(root/'evidence'/'arduino-original-layouts.json',base/'evidence')
for key in ('bench-breakout','companion-shield','blank-shield'):
    work=base/'tmp'/key
    source=root/'inputs'/key
    shutil.copytree(source/'pin-tables',work)
    with ZipFile(next(source.glob('*Flux*.zip'))) as archive:archive.extractall(work/'project')
    with ZipFile(source/manifest[key]['fabrication_archive']) as archive:archive.extractall(work/'fab')
    pr=work/'project'; sch=next(pr.glob('*.kicad_sch')); pcb=next(pr.glob('*.kicad_pcb'))
    ev=base/'evidence'/key; ev.mkdir()
    fresh=work/'fresh'; fresh.mkdir()
    run(['kicad-cli','sch','erc','--format','json','--severity-all','--exit-code-violations','-o',ev/'ERC.json',sch])
    run(['kicad-cli','pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity','--exit-code-violations','-o',ev/'DRC.json',pcb])
    run(['kicad-cli','sch','export','netlist','--format','kicadxml','-o',ev/'Netlist.xml',sch])
    run(['kicad-cli','pcb','export','gerbers','-l','F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts','-o',fresh,pcb])
    run(['kicad-cli','pcb','export','drill','--excellon-separate-th','-o',fresh,pcb])
run([args.pcb_python,here/'read_boards.py',base]+([args.arduino_dir.resolve()] if args.arduino_dir else []))
run([args.pcb_python,here/'trace_ends.py',base])
run([sys.executable,here/'check_copper.py',base])
run([sys.executable,here/'verify_stack.py',base])
