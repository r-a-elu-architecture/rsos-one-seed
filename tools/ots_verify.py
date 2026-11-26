import sys, hashlib, os, json
MAGIC = b'\x00OpenTimestamps\x00\x00Proof\x00\xbf\x89\xe2\xe8\x84\xe8\x92\x94'
BTC = bytes.fromhex('0588960d73d71901'); PEND = bytes.fromhex('83dfe30d2ef90c8e')
class R:
    def __init__(s, b): s.b, s.i = b, 0
    def byte(s): v = s.b[s.i]; s.i += 1; return v
    def bytes_(s, n): v = s.b[s.i:s.i+n]; s.i += n; return v
    def varuint(s):
        v = sh = 0
        while True:
            c = s.byte(); v |= (c & 0x7f) << sh; sh += 7
            if not c & 0x80: return v
    def varbytes(s): return s.bytes_(s.varuint())
def apply(tag, r, msg):
    if tag == 0xf0: return msg + r.varbytes()
    if tag == 0xf1: return r.varbytes() + msg
    if tag == 0xf2: return msg[::-1]
    if tag == 0xf3: return msg.hex().encode()
    if tag == 0x08: return hashlib.sha256(msg).digest()
    if tag == 0x02: return hashlib.sha1(msg).digest()
    if tag == 0x03: return hashlib.new('ripemd160', msg).digest()
    raise ValueError('unknown op %x' % tag)
def walk(r, msg, out):
    def one(tag):
        if tag == 0x00:
            t = r.bytes_(8); payload = r.varbytes()
            if t == BTC:
                out.append(('bitcoin', R(payload).varuint(), msg[::-1].hex()))
            elif t == PEND:
                out.append(('pending', R(payload).varbytes().decode(), None))
            else:
                out.append(('other', t.hex(), None))
        else:
            walk(r, apply(tag, r, msg), out)
    tag = r.byte()
    while tag == 0xff:
        one(r.byte()); tag = r.byte()
    one(tag)
res = {}
for p in sys.argv[1:]:
    b = open(p, 'rb').read(); assert b.startswith(MAGIC); r = R(b); r.i = len(MAGIC)
    r.varuint(); op = r.byte(); assert op == 0x08; digest = r.bytes_(32)
    out = []; walk(r, digest, out)
    res[os.path.basename(p)] = {'digest': digest.hex(), 'attestations': out}
print(json.dumps(res, indent=1))
