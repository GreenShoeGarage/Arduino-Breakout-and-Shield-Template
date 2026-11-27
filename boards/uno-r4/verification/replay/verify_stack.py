"""Check header mating, silk legends and published pin tables against the routed boards."""
from collections import Counter, defaultdict
from pathlib import Path
import csv
import json
import math
import sys

base=Path(sys.argv[1])
ev=base/'evidence'
def readcsv(path):
    with path.open(newline='') as f:return list(csv.DictReader(f))
def load(path):return json.loads(path.read_text())
boards=('bench-breakout','companion-shield','blank-shield')
inputs={k:load(ev/k/'pad-inventory.json') for k in boards}
copper={k:load(ev/k/'copper-test.json') for k in boards}
pads={k:{(p['ref'],p['pin']):p for p in inputs[k]['pads']} for k in boards}
silks={k:{(s['text'],*map(lambda x:round(x,5),s['xy'])) for s in inputs[k]['silk']} for k in boards}
host=load(ev/'arduino-original-layouts.json')
rows=readcsv(base/'tmp'/boards[0]/'Pin-map.csv')
tables={k:{(r['Breakout male'],r['Host pin']):r for r in readcsv(base/'tmp'/k/'Pin-map.csv')} for k in boards[1:]}
prior={(r['Arduino model'],r['Breakout input'],r['Input pin']):r for r in readcsv(base/'tmp'/boards[0]/'Arduino-to-terminal.csv')}
inp=lambda i:(i['Input'],i['Input pin'])
direct_labels=['SCL','SDA','AREF','GND','D13','D12','D11','D10','D9','D8','D7','D6','D5','D4','D3','D2','TX/D1','RX/D0']
analog_labels=['BOOT','IOREF','RESET','3V3','5V','GND','GND','VIN','A0/DAC','A1','A2','A3','A4/SDA','A5/SCL']
bank_labels={'J1':direct_labels[:10],'J2':direct_labels[10:],'J3':analog_labels[:8],'J4':analog_labels[8:],'J5':'CIPO 5V SCK COPI RESET GND'.split(),'J6':'OFF GND VRTC'.split(),'J7':'IO42 IO41 TXD0 IO0/DL RXD0 GND'.split(),'J8':'GND 3V3 SDA1 SCL1'.split(),'J9':'VT/5V SWDIO GND SWCLK GND NC RX1 TX1 GND RESET'.split()}
# Arduino full pinouts assign different RA4M1 ports to several digital and SPI pins on the two models.
dports={'Minima':'P111 P110 P109 P112 P303 P304 P107 P106 P102 P103 P104 P105 P302 P301',
       'WiFi':'P102 P410 P411 P103 P303 P304 P112 P111 P107 P106 P105 P104 P302 P301'}
analog_nets='MD +5V RESET +3V3 +5V GND GND VIN P014 P000 P001 P002 P101 P100'.split()
aux={ 'J6':'OFF GND VBATT','J7':'ESP_IO42 ESP_IO41 ESP_TXD0 ESP_DOWNLOAD ESP_RXD0 GND',
      'J8':'GND +3V3_I2C EXT_SDA EXT_SCL','J9':'+5V P108 GND P300 GND NC P502 P501 GND RESET'}
def expected(model,j):
    digital='P100 P101 AREF GND'.split()+dports[model].split()
    if j in ('J1','J2'):return digital[:10] if j=='J1' else digital[10:]
    if j in ('J3','J4'):return analog_nets[:8] if j=='J3' else analog_nets[8:]
    if j=='J5':
        return ('P110 +5V P111 P109 RESET GND' if model=='Minima' else 'P410 +5V P102 P411 RESET GND').split()
    return aux[j].split()
def match_net(n,target):
    normalized=n.removesuffix('_1').replace('~{RESET}','RESET') or 'NC'
    if target.startswith('P') and target[1:].isdigit():return normalized.split('_')[0]==target
    return normalized==target
def refpin(ref,pin):return ref+'.'+pin
def ids(r,pin_key,num_key):return (r[pin_key],r[num_key])
def center_error(a,b):return math.dist(a,b)
def silk_pass(board,label,x,y):
    assert (label,round(x,5),round(y,5)) in silks[board],(board,label,x,y)
summary={}; mapping=[]
for k in boards:
    assert not copper[k]['opens'] and not copper[k]['shorts'] and copper[k]['orphan_islands']==0
    pro=load(next((base/'tmp'/k/'project').glob('*.kicad_pro')))
    assert not pro['board']['design_settings'].get('drc_exclusions') and not pro.get('erc',{}).get('erc_exclusions')
for model,m in host.items():
    connectors=m['connectors']
    origin=connectors['JDIGITAL']['1']['xy']
    datum=pads[boards[0]][('J2','8')]['xy']
    delta=[datum[i]-origin[i] for i in (0,1)]
    directrefs={'JDIGITAL','JANALOG','J1' if model=='Minima' else 'J3'}
    reviewed=set(); residuals=[]; tally=Counter()
    for r in sorted(rows,key=lambda r:(int(r['Input'][1:]),int(r['Input pin']))):
        if r['Variant'] not in ('Both',model):continue
        source=inp(r); j,pin=source; pi=int(pin)-1
        assert r['Board legend']==bank_labels[j][pi]
        usbpad=pads[boards[0]][source]
        q=prior[model,j,pin]
        if int(j[1:])<=5:
            mode='Direct'
            point=usbpad['xy']
            candidates=[]
            for ref in directrefs:
                for n,z in connectors[ref].items():
                    xy=[a+b for a,b in zip(z['xy'],delta)]
                    if center_error(point,xy)<.001:candidates.append((ref,n,center_error(point,xy)))
            assert len(candidates)==1,(model,j,pin,candidates)
            ar,ap,gap=candidates[0]
            residuals.append(gap)
            assert usbpad['mount']==('B.Cu' if j=='J5' else 'F.Cu')
        else:
            mode='Cable'
            ar={'J6':'JOFF','J7':'J6','J8':'J2','J9':'J2'}[j]; ap=pin
        h=connectors[ar][ap]
        assert (ar,ap,h['net'] or 'NC',mode)==(q['Arduino CAD reference'],q['Arduino CAD pad'],q['Arduino CAD net'],q['Connection'])
        assert match_net(h['net'],expected(model,j)[pi]),(model,source,h)
        assert (ar,ap) not in reviewed
        reviewed.add((ar,ap));tally[mode]+=1
        net='/'+r['Bare-board net']; tap=ids(r,'Jumper','Jumper pin'); term=ids(r,'Terminal','Terminal pin')
        bp=pads[boards[0]]
        members={key for key,p in bp.items() if p['net']==net}
        assert members=={source,tap,term}|({('J8','MP')} if net=='/Q_GND' else set())
        assert bp[tap]['mount']=='F.Cu'
        for k,col in ((source,'Input'),(tap,'Jumper'),(term,'Terminal')):
            assert center_error(bp[k]['xy'],[float(r[col+' '+a+' mm']) for a in ('X','Y')])<.001
        x,y=bp[tap]['xy']
        bank=int(j[1:]); b=boards[0]
        if bank in (1,2,3,4,6):silk_pass(b,r['Board legend'],x, {1:35.3,2:35.3,3:110.6,4:110.6,6:111.55}[bank])
        else:silk_pass(b,r['Board legend'],200.7,y)
        for shield,table in tables.items():
            s=table[tap]; so=ids(s,'Shield underside socket','Socket pin'); field=ids(s,'Solder row','Solder pin')
            assert set(key for key,p in pads[shield].items() if p['net']==net)=={so,field}
            assert s['Net']==net[1:] and so==('J'+tap[0][1:],tap[1]) and field==('P'+tap[0][1:],tap[1])
            sp=pads[shield][so]
            assert sp['mount']=='B.Cu' and center_error(sp['xy'],bp[tap]['xy'])<.000001
            assert center_error(pads[shield][field]['xy'],[float(s['Solder '+a+' mm']) for a in ('X','Y')])<.001
            legend=s['Legend']
            if bank in (1,2,3,4,6):
                if bank==6:legend={'GND':'G','VRTC':'RTC'}.get(legend,legend)
                silk_pass(shield,legend,x,{1:37.55,2:37.55,3:109.08,4:109.08,6:106.25}[bank])
            else:silk_pass(shield,legend,200.28,y)
        mapping.append(dict(model=model,signal=r['Board legend'],bank=r['Bank'],ref=refpin(ar,ap),hostnet=h['net'] or 'NC',
                            attachment=mode,input=refpin(*source),male=refpin(*tap),terminal=refpin(*term),socket=refpin(*so),pad=refpin(*field),net=net[1:]))
    all_contacts={(r,n) for r,pts in connectors.items() for n in pts if n.isdigit()}
    assert all_contacts==reviewed and tally['Direct']==38
    summary[model]=dict(direct=tally['Direct'],cabled=tally['Cable'],distinct_connector_positions=len(reviewed),direct_max_offset_mm=round(max(residuals),9),unassigned=sum(not connectors[r][n]['net'] for r,n in reviewed))
for b in boards[1:]:
    grid=[p for p in inputs[b]['pads'] if p['ref'].startswith('G')]
    assert len(grid)==(180 if b=='companion-shield' else 0)
    assert all(p['net'].startswith('unconnected-') for p in grid)
by_input=defaultdict(dict)
for r in mapping:
    by_input[r['input']][r['model']]=r
assert len(by_input)==61
with (base/'output'/'UNO-R4-Pin-Continuity.csv').open('w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['Bank','Breakout signal','Bare-board net','UNO connection','Minima header.pin','Minima Arduino CAD net','WiFi header.pin','WiFi Arduino CAD net','Breakout input','Breakout male','2.54 mm screw terminal','Shield underside socket (both boards)','Shield solder pad (both boards)','Released copper and mating result','Bench measurement (blank for user)'])
    for v in sorted(by_input.values(),key=lambda v:tuple(map(int,next(iter(v.values()))['input'][1:].split('.')))):
        r=next(iter(v.values()));m=v.get('Minima',{});wif=v.get('WiFi',{})
        w.writerow([r['bank'],r['signal'],r['net'],r['attachment'],m.get('ref',''),m.get('hostnet',''),wif.get('ref',''),wif.get('hostnet',''),r['input'],r['male'],r['terminal'],r['socket'],r['pad'],'PASS (host pin NC)' if r['hostnet']=='NC' else 'PASS',''])
results=dict(hosts=summary,shared_direct_positions=38,breakout_positions=61,shield_mating_centers_checked_per_board=61,shield_max_offset_mm=0.0,verified_front_legend_positions_per_board=61,prototype_isolated_user_pads=180)
(ev/'stack-result.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
