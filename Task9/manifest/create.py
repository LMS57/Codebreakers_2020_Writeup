from hashlib import sha256

f = open('flightmonitor.sh').read()
s = sha256()
s.update(f)
l = s.digest()
s = sha256()
s.update(open('key.pub').read())
l+= s.digest()
l+= '\x0dflightmonitor\x07key.pub\x02'
import sys
sys.stdout.write(l)
