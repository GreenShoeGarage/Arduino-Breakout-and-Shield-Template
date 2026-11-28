import math,sys,json,csv
from pathlib import Path
from collections import Counter
here=Path(__file__).resolve().parent
base=Path(sys.argv[1])/'evidence'
keys=['carrier','riser','companion-shield','blank-shield']
maps={k:{(p['ref'],p['pin']):p for p in json.loads((base/k/'pad-inventory.json').read_text())['pads']} for k in keys}
rows=list(csv.DictReader((here/'connector-order.csv').open()))
hdata=json.loads((here/'arduino-contacts.json').read_text())
qa=base
def exactpin(m,ref,num):
    return next(p for p in hdata[m] if p['ref']==ref and p['pin']==num)
def npin(board,ref,p):return maps[board][(ref,str(p))]
rows_out=[]; totals=Counter(); worst=0
for r in rows:
    m=r['Arduino model'];ref=r['Arduino CAD reference'];ap=r['Arduino CAD pad'];hr=exactpin(m,ref,ap)
    assert (hr['net'] or 'NC')==r['Arduino CAD net']
    j=r['Breakout input'];pn=int(r['Input pin']);h=r['Jumper'];hp=r['Jumper pin'];t=r['Terminal'];tp=r['Terminal pin']
    net=npin('carrier',h,hp)['net'];assert npin('carrier',t,tp)['net']==npin('carrier',j,pn)['net']==net
    for sh in ('blank-shield','companion-shield'):
        sock=npin(sh,'J'+h[1:],hp)
        assert sock['net']==npin(sh,'P'+h[1:],hp)['net']==net
        assert sock['mount']=='B.Cu' and npin('carrier',h,hp)['mount']=='F.Cu' and math.dist(sock['xy'],npin('carrier',h,hp)['xy'])<.000001
    entry=f'{ref}.{ap}';note='';method='Direct header'
    if j in ['J1','J2','J3','J4','J5','J6','J7']:
        actual={'J6':'J16','J7':'J17'}.get(j,j);pick=npin('carrier',actual,pn)
        assert pick['net']==net and math.dist(pick['xy'],hr['xy'])<.001
        if actual in ('J5','J16','J17'):assert pick['mount']=='B.Cu'
        worst=max(worst,math.dist(pick['xy'],hr['xy']))
        path=f'{actual}.{pn}'
    elif j=='J8':
        if pn==1:
            method='Direct ground via fitted R81';path='J5.6 > R81.1/2'
            assert exactpin(m,'J3','6')['net']==hr['net']=='GND'
            assert npin('carrier','R81',1)['net']==npin('carrier','J5',6)['net'] and npin('carrier','R81',2)['net']==net
        else:
            method='Spring contact';name=['3V3_IC','EXT_SDA','EXT_SCL'][pn-2]
            target=exactpin(m,name,'X');pick=npin('carrier','TP'+str(79+pn),'1')
            assert pick['net']==net and target['net']==hr['net']
            assert 'F' in target['mask'] and math.dist(target['xy'],pick['xy'])<.156
            path=name+' > '+pick['ref'];note='Qwiic J2 contact shares the selected factory land.'
    else:
        method='Rigid SWD riser';i=pn-1;lr='J2' if i%2==0 else 'J3';upper='J19' if i%2==0 else 'J20';pp=i//2+1
        socket=npin('riser','J1',pn); projected=[socket['xy'][0]-(.635 if i%2==0 else -.635),socket['xy'][1]]
        assert math.dist(projected,hr['xy'])<.001 and socket['net']==net and socket['mount']=='B.Cu'
        assert npin('riser',lr,pp)['net']==npin('carrier',upper,pp)['net']==net
        assert math.dist(npin('riser',lr,pp)['xy'],npin('carrier',upper,pp)['xy'])<1e-6
        path=f'Riser J1.{pn} > {lr}.{pp} > carrier {upper}.{pp}'
        if not hr['net']:note='Reserved NC on host. Continuity ends at physical connector contact.'
    rows_out.append([m,r['Bank'] if 'Bank' in r else j,r['Breakout legend'],entry,hr['net'] or 'NC',method,path,net[1:],f'{h}.{hp}',f'{t}.{tp}',f'J{h[1:]}.{hp}',f'P{h[1:]}.{hp}',note,''])
    totals[(m,method)]+=1
with (qa/'UNO-R4-Direct-Continuity.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['UNO model','Bank','Signal','UNO connector contact','Official host net','Stack connection','Pickup path','Carrier net','Breakout male','Screw terminal','Underside shield socket','Shield solder pad','Note','Bench reading']);w.writerows(rows_out)
assert len(rows_out)==99 and sum(r[0]=='Minima' for r in rows_out)==48
print(dict(totals))
