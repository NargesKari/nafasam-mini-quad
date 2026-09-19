import re, json

class Atom(str): pass

def parse(text):
    toks = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)
    stack = [[]]
    for t in toks:
        if t == '(':
            n=[]; stack[-1].append(n); stack.append(n)
        elif t == ')': stack.pop()
        elif t.startswith('"'): stack[-1].append(json.loads(t))
        else: stack[-1].append(Atom(t))
    return stack[0][0]

def dump(x):
    if isinstance(x,list): return '('+' '.join(dump(v) for v in x)+')'
    if isinstance(x,Atom): return str(x)
    if isinstance(x,str): return json.dumps(x,ensure_ascii=False)
    return str(x)

def children(x,k): return [n for n in x if isinstance(n,list) and n and n[0]==k]
def child(x,k): return next((n for n in children(x,k)),None)

def load_symbol(lib,name):
    from pathlib import Path
    import copy
    root=parse((Path('E:/kiCad/share/kicad/symbols')/(lib+'.kicad_sym')).read_text(encoding='utf-8'))
    def resolve(name):
        s=copy.deepcopy(next(n for n in children(root,'symbol') if n[1]==name))
        parent=child(s,'extends')
        if parent:
            b=resolve(parent[1]); old=b[1]
            b[1]=name
            for sub in children(b,'symbol'): sub[1]=sub[1].replace(old+'_',name+'_',1)
            props={p[1] for p in children(s,'property')}
            b=[n for n in b if not(isinstance(n,list) and n[0]=='property' and n[1] in props)]
            b.extend(n for n in s[2:] if not(isinstance(n,list) and n[0]=='extends'))
            return b
        return s
    return resolve(name)

def pins(s):
    return [p for sub in children(s,'symbol') for p in children(sub,'pin')]

if __name__=='__main__':
    for lib,name in [('RF_Module','ESP32-S3-MINI-1'),('Sensor_Motion','MPU-6050'),('Transistor_FET','AO3400A'),('Regulator_Linear','TLV70012_SOT23-5'),('Regulator_Linear','TLV70028_SOT23-5')]:
        s=load_symbol(lib,name)
        print(lib,name)
        print([(child(p,'number')[1],child(p,'name')[1],p[1],child(p,'at')[1:]) for p in pins(s)])
