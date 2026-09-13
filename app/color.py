from __future__ import annotations
import colorsys, math, re
from dataclasses import dataclass
from typing import Any

CSS_NAMES = {'black':'#000000','white':'#FFFFFF','red':'#FF0000','green':'#008000','blue':'#0000FF','yellow':'#FFFF00','cyan':'#00FFFF','magenta':'#FF00FF','orange':'#FFA500','purple':'#800080','pink':'#FFC0CB','gray':'#808080','lime':'#00FF00','navy':'#000080','teal':'#008080','aqua':'#00FFFF','gold':'#FFD700','indigo':'#4B0082','violet':'#EE82EE','brown':'#A52A2A'}

HEX_RE = re.compile(r"^#?([0-9a-fA-F]{3,8})$")

@dataclass(frozen=True)
class Color:
    r: float
    g: float
    b: float
    a: float = 1.0

    def clamp(self) -> 'Color':
        return Color(*(max(0.0, min(1.0, v)) for v in (self.r, self.g, self.b)), max(0.0, min(1.0, self.a)))

def _byte(v: float) -> int: return round(max(0, min(255, v * 255)))
def _pct(v: float) -> float: return round(v * 100, 2)

def parse_hex(value: str) -> Color:
    m = HEX_RE.match(value.strip())
    if not m: raise ValueError('Invalid HEX color. Use #RGB, #RGBA, #RRGGBB, or #RRGGBBAA.')
    s=m.group(1)
    if len(s) in (3,4): s=''.join(c*2 for c in s)
    if len(s) not in (6,8): raise ValueError('Invalid HEX length.')
    vals=[int(s[i:i+2],16)/255 for i in range(0,len(s),2)]
    return Color(*vals).clamp()

def parse_rgb(value: str) -> Color:
    s=value.strip().lower().replace('rgba','').replace('rgb','').strip(' ()')
    parts=[p.strip() for p in s.split(',')]
    if len(parts) not in (3,4): raise ValueError('RGB requires 3 or 4 components.')
    vals=[]
    for p in parts[:3]:
        vals.append(float(p[:-1])/100 if p.endswith('%') else float(p)/255)
    a=float(parts[3][:-1])/100 if len(parts)==4 and parts[3].endswith('%') else (float(parts[3]) if len(parts)==4 else 1)
    if any(not math.isfinite(x) for x in vals+[a]) or any(x<0 or x>1 for x in vals+[a]): raise ValueError('RGB values are out of range.')
    return Color(*vals,a)

def parse_hsl(value: str) -> Color:
    s=value.strip().lower().replace('hsla','').replace('hsl','').strip(' ()')
    parts=[p.strip() for p in s.split(',')]
    if len(parts) not in (3,4): raise ValueError('HSL requires 3 or 4 components.')
    h=float(parts[0].replace('deg',''))%360
    ss=float(parts[1].rstrip('%'))/100; l=float(parts[2].rstrip('%'))/100
    a=float(parts[3].rstrip('%'))/100 if len(parts)==4 and parts[3].endswith('%') else (float(parts[3]) if len(parts)==4 else 1)
    if not 0<=ss<=1 or not 0<=l<=1 or not 0<=a<=1: raise ValueError('HSL saturation, lightness, or alpha is out of range.')
    r,g,b=colorsys.hls_to_rgb(h/360,l,ss)
    return Color(r,g,b,a)

def parse_hsv(value: str) -> Color:
    s=value.strip().lower().replace('hsb','').replace('hsv','').strip(' ()')
    parts=[p.strip() for p in s.split(',')]
    if len(parts) not in (3,4): raise ValueError('HSV requires 3 or 4 components.')
    h=float(parts[0].replace('deg',''))%360; sat=float(parts[1].rstrip('%'))/100; v=float(parts[2].rstrip('%'))/100
    a=float(parts[3].rstrip('%'))/100 if len(parts)==4 and parts[3].endswith('%') else (float(parts[3]) if len(parts)==4 else 1)
    if not 0<=sat<=1 or not 0<=v<=1 or not 0<=a<=1: raise ValueError('HSV values are out of range.')
    r,g,b=colorsys.hsv_to_rgb(h/360,sat,v)
    return Color(r,g,b,a)

def parse_color(value: str, format_hint: str='auto') -> Color:
    f=format_hint.lower()
    if f in ('hex','auto') and (value.strip().startswith('#') or (f=='hex')): return parse_hex(value)
    if f in ('rgb','rgba'): return parse_rgb(value)
    if f in ('hsl','hsla'): return parse_hsl(value)
    if f in ('hsv','hsb'): return parse_hsv(value)
    s=value.strip().lower()
    if s.startswith('rgb'): return parse_rgb(s)
    if s.startswith('hsl'): return parse_hsl(s)
    if s.startswith(('hsv','hsb')): return parse_hsv(s)
    return parse_hex(value)

def to_dict(c: Color) -> dict[str, Any]:
    c=c.clamp(); r,g,b,a=c.r,c.g,c.b,c.a
    h,l,s=colorsys.rgb_to_hls(r,g,b); hv,sv,v=colorsys.rgb_to_hsv(r,g,b)
    k=1-max(r,g,b)
    if k>=1: ck=cm=cy=0
    else: ck=k; cm=(1-r-k)/(1-k); cy=(1-g-k)/(1-k); ck=k
    return {
      'hex': '#%02X%02X%02X'%(_byte(r),_byte(g),_byte(b)) + ('' if a>=.999 else '%02X'%_byte(a)),
      'rgb': f'rgb({_byte(r)}, {_byte(g)}, {_byte(b)})',
      'rgba': f'rgba({_byte(r)}, {_byte(g)}, {_byte(b)}, {round(a,3)})',
      'hsl': f'hsl({round(h*360,2)}, {_pct(s)}%, {_pct(l)}%)',
      'hsla': f'hsla({round(h*360,2)}, {_pct(s)}%, {_pct(l)}%, {round(a,3)})',
      'hsv': f'hsv({round(hv*360,2)}, {_pct(sv)}%, {_pct(v)}%)',
      'hsb': f'hsb({round(hv*360,2)}, {_pct(sv)}%, {_pct(v)}%)',
      'cmyk': f'cmyk({_pct(cm)}%, {_pct(cy)}%, {_pct(ck)}%, {_pct(k)}%)',
      'alpha': round(a,4), 'r':_byte(r),'g':_byte(g),'b':_byte(b),
      'css_variable': f'--color-value: {("rgba" if a < .999 else "rgb")}({_byte(r)}, {_byte(g)}, {_byte(b)}' + (f', {round(a,3)}' if a < .999 else '') + ');',
      'css': f'rgba({_byte(r)}, {_byte(g)}, {_byte(b)}, {round(a,3)})' if a < .999 else f'rgb({_byte(r)}, {_byte(g)}, {_byte(b)})',
      'tailwind': f'[{"rgba" if a < .999 else "rgb"}({_byte(r)}, {_byte(g)}, {_byte(b)}' + (f'/{round(a,3)}' if a < .999 else '') + ')]',
      'json': {'r':_byte(r),'g':_byte(g),'b':_byte(b),'a':round(a,4),'hex':'#%02X%02X%02X'%(_byte(r),_byte(g),_byte(b))},
      'name': _nearest_name(Color(r,g,b)),
    }

def relative_luminance(c: Color) -> float:
    vals=[]
    for x in (c.r,c.g,c.b): vals.append(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4)
    return .2126*vals[0]+.7152*vals[1]+.0722*vals[2]

def contrast(a: Color,b: Color)->float:
    l1,l2=relative_luminance(a),relative_luminance(b)
    return (max(l1,l2)+.05)/(min(l1,l2)+.05)

def accessibility(ratio: float)->dict[str,bool]:
    return {'AA_normal':ratio>=4.5,'AA_large':ratio>=3,'AAA_normal':ratio>=7,'AAA_large':ratio>=4.5}

def mix(a:Color,b:Color,t:float,space='rgb')->Color:
    t=max(0,min(1,t))
    if space=='hsl':
        ha,la,sa=colorsys.rgb_to_hls(a.r,a.g,a.b); hb,lb,sb=colorsys.rgb_to_hls(b.r,b.g,b.b)
        dh=((hb-ha+.5)%1)-.5; h=(ha+dh*t)%1
        r,g,bb=colorsys.hls_to_rgb(h,la+(lb-la)*t,sa+(sb-sa)*t)
    else: r,g,bb=[x+(y-x)*t for x,y in zip((a.r,a.g,a.b),(b.r,b.g,b.b))]
    return Color(r,g,bb,a.a+(b.a-a.a)*t)

def adjust(c:Color, op:str, amount:float)->Color:
    h,l,s=colorsys.rgb_to_hls(c.r,c.g,c.b); amount=max(-1,min(1,amount))
    if op=='hue': h=(h+amount)%1
    elif op=='saturation': s=max(0,min(1,s+amount))
    elif op=='brightness':
        r,g,b=colorsys.hsv_to_rgb(*colorsys.rgb_to_hsv(c.r,c.g,c.b)[:2], max(0,min(1,colorsys.rgb_to_hsv(c.r,c.g,c.b)[2]+amount))); return Color(r,g,b,c.a)
    elif op=='tint': return mix(c,Color(1,1,1),amount)
    elif op=='shade': return mix(c,Color(0,0,0),amount)
    elif op=='tone': return mix(c,Color(.5,.5,.5),amount)
    return Color(*colorsys.hls_to_rgb(h,l,s),c.a)

def palette(c:Color, kind:str)->list[Color]:
    h,l,s=colorsys.rgb_to_hls(c.r,c.g,c.b); h=h*360
    steps={'complementary':[0,180],'analogous':[-30,0,30],'triadic':[0,120,240],'tetradic':[0,90,180,270],'split-complementary':[0,150,210],'monochromatic':[0,0,0,0]}
    if kind=='monochromatic':
        return [adjust(c,'brightness',x) for x in (-.35,-.15,0,.15,.35)]
    return [Color(*colorsys.hls_to_rgb(((h+d)%360)/360,l,s),c.a) for d in steps.get(kind,[0])]


def _nearest_name(c: Color) -> str:
    def dist(x: Color, y: Color) -> float: return (x.r-y.r)**2+(x.g-y.g)**2+(x.b-y.b)**2
    return min(CSS_NAMES, key=lambda n: dist(c, parse_hex(CSS_NAMES[n])))
