infile = ''

import datetime,random,argparse,warnings
from bs4 import BeautifulSoup
warnings.filterwarnings("ignore", message='.*features="xml".*')
p = argparse.ArgumentParser()
p.add_argument('-i',help='infile')
p.add_argument('-o',help='outfile')
p.add_argument('-p',action='store_true',help='pad input file to 4x points')
p.add_argument('-r',help='randomness',type=float,default=1)
p.add_argument('-C',action='store_true',help='cycle (default: run)')
p.add_argument('-d',help='date in dd/mm/yyyy (default: today)')
p.add_argument('-t',help='hour (default: randint(7,21))',type=int,default=random.randint(7,21))
p.add_argument('-z',help='timezone (default: +8)',type=int,default=8)
p.add_argument('-k',help='estimated distance (default: 10km)',type=float,default=10)
p.add_argument('-K',help='original distance (default: 26km)',type=float,default=26)
p.add_argument('-s',help='speed-prob/decay-rate (default: .2/100000)',default='.2/100000')
p.add_argument('-b',help='rest prob (default: .001)',default=.001)
args = p.parse_args()

def parse_infile(f):
    try: d = open(infile,'r').read()
    except: print('[-] error opening infile');quit()
    try: b = BeautifulSoup(d,'html.parser'); a = ['%s,%s,%s'%(l['lat'],l['lon'],l.find_all('ele')[0].text) for l in b.find_all('trkpt')]
    except: print('[-] infile parsing error');quit()
    if args.p:
        try:
            c = []
            for k,v in enumerate(a[:-1]): c.append(v); c += [','.join(('%%.%sf'%(1 if j==2 else 7))%(((3-i)*float(v.split(',')[j])+(i+1)*float(a[k+1].split(',')[j]))/4) for j in range(3)) for i in range(3)]
            a = c+[a[-1]]
        except: print('[-] error while padding infile');quit()
    return a

try: d,m,y = (int(c) for c in args.d.split('/')); assert d-1 in range(31) and m-1 in range(12) and y>0
except: 
    d,m,y = (int(c) for c in datetime.date.today().strftime("%d/%m/%Y").split('/'))
    if args.d: print('[-] date format error. defaulting to %s/%s/%s'%(d,m,y))
assert args.t in range(24),'hours must be between 0 to 23'
assert args.z in range(-12,15),'timezome must be between -12 and +14'
st = datetime.datetime(y,m,d,args.t,random.randint(0,59),random.randint(0,59))-datetime.timedelta(hours=args.z)
t = '%s %s'%('Morning' if args.t<12 else 'Afternoon' if args.t<17 else 'Evening','Ride' if args.C else 'Run')
outfile = args.o if args.o else './%d%02d%02d_'%(y,m,d)+t.replace(' ','_')+'.gpx'

if args.i: infile = args.i
elif not infile: print('[-] no input file provided');quit()
print('[=] parsing infile %s%s'%(infile,' with padding' if args.p else ''))
d = parse_infile(infile)
print('[+] parsing success. %s datapoints'%len(d))

assert args.k and args.k>0,'target distance must be positive'
assert args.K>0,'original distance must be positive'
assert args.r>=0 and args.r<=1,'randomness must be between 0 and 1'
args.k += random.randint(0,1000)/1000-.5; n,r = round(args.k/args.K*len(d)),random.randint(0,round(args.r*len(d)))
try: s,q = args.s.split('/'); s,q = float(s),float(q); assert s>=0 and (q>0 or q==-1)
except: print('[-] invalid speed rate. defaulting to 2/100000'); s,q=2,100000
try: b = float(args.b); assert b>0
except: print('[-] invalid rest prob. defaulting to .001'); b = .001
print('[=] generating gpx:\n\ttype:\t\t%s\n\tstart time:\t%s (GMT%+d)\n\tpoints:\t\t%s (est. %s km)\n\tstart:\t\t%s\n\tspeed prob:\t%s-r/%s\n\trest prob:\t%s\n\toutfile:\t%s'%('cycle' if args.C else 'run',st+datetime.timedelta(hours=args.z),args.z,n,args.k,r,s,'inf' if q==-1 else q,b,outfile))

try: f = open(outfile,'w')
except: print('[-] error opening outfile');quit()
print('''<?xml version="1.0" encoding="UTF-8"?>\n<gpx xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd" creator="StravaGPX" version="1.1" xmlns="http://www.topografix.com/GPX/1/1">\n <metadata>\n  <time>%s</time>\n </metadata>\n <trk>\n  <name>%s</name>\n  <type>%s</type>\n  <trkseg>'''%(st.strftime('%Y-%m-%dT%H:%M:%SZ'),t,'cycling' if args.C else 'running'),file=f)
i,t = 0,'''   <trkpt lat="%s" lon="%s">\n    <ele>%s</ele>\n    <time>%s</time>\n   </trkpt>'''
while i<n:
	lat,lon,alt = (random.uniform(float(x),float(y)) for x,y in zip(d[(r)%len(d)].split(','),d[(r+1)%len(d)].split(',')))
	print(t%('%.7f'%round(lat,7),'%.7f'%round(lon,7),'%.1f'%round(alt,1),(st+datetime.timedelta(seconds=i)).strftime("%Y-%m-%dT%H:%M:%SZ")),file=f)
	if random.random()<b: i+=60
	elif random.random()<s-(r/q): r+=random.randint(1,4)
	else: i+=1;r+=1
print('  </trkseg>\n </trk>\n</gpx>\n',file=f);f.close()
print('[+] data written to %s'%outfile)
