from app.color import *

def test_hex_and_formats():
 c=parse_hex('#336699CC'); d=to_dict(c); assert d['hex']=='#336699CC'; assert d['r']==51 and d['alpha']<1

def test_rgb_hsl_roundtrip():
 c=parse_rgb('rgb(255, 0, 128)'); assert to_dict(c)['rgb']=='rgb(255, 0, 128)'
 c2=parse_hsl('hsl(0, 100%, 50%)'); assert to_dict(c2)['hex']=='#FF0000'

def test_contrast(): assert round(contrast(parse_hex('#fff'),parse_hex('#000')),1)==21.0

def test_palettes():
 for k in ['complementary','analogous','triadic','tetradic','split-complementary','monochromatic']: assert palette(parse_hex('#123456'),k)

def test_mix_adjust():
 assert to_dict(mix(parse_hex('#000'),parse_hex('#fff'),.5))['hex']=='#808080'
 assert adjust(parse_hex('#000'),'tint',1).r==1
