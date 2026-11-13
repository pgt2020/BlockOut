# -*- coding: utf-8 -*-
import random
W, H = 1080, 1920
parts = []
def add(s): parts.append(s)

def cloud(x, y, s, op=1, blur=5):
    add(f'''<g transform="translate({x},{y}) scale({s})" filter="url(#b{blur})" opacity="{op}">
      <ellipse cx="0" cy="18" rx="105" ry="38" fill="#DCEBF2"/>
      <ellipse cx="-62" cy="8" rx="62" ry="44" fill="#F4FAFD"/>
      <ellipse cx="0" cy="-12" rx="82" ry="58" fill="#FFFFFF"/>
      <ellipse cx="62" cy="10" rx="58" ry="40" fill="#FBFEFF"/>
      <ellipse cx="18" cy="26" rx="96" ry="28" fill="#FFFFFF" opacity=".9"/>
    </g>''')

def bush(x, y, s, blur=2, dark=False):
    base = '#4F8C46' if dark else '#5E9E48'
    cols = ['#6FB75B', '#7FC566', '#8FD372', '#5FA84F']
    add(f'<g transform="translate({x},{y}) scale({s})" filter="url(#b{blur})">')
    add(f'<ellipse cx="0" cy="6" rx="72" ry="52" fill="{base}" opacity=".55"/>')
    for i in range(9):
        cx = random.uniform(-58, 58); cy = random.uniform(-30, 26); r = random.uniform(20, 38)
        add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{random.choice(cols)}"/>')
    for i in range(5):
        cx = random.uniform(-45, 40); cy = random.uniform(-36, -8); r = random.uniform(8, 18)
        add(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r:.1f}" ry="{r*0.62:.1f}" fill="#B4E792" opacity=".55"/>')
    add('</g>')

def flower(x, y, s, kind='pink', rot=0, blur=0, op=1):
    petal = {'pink': '#F4A6C0', 'deep': '#DE7D9E', 'white': '#FFF9EC', 'yellow': '#F7D45C'}[kind]
    center = '#E8A21C' if kind != 'pink' else '#C97A2E'
    pet = ''
    for i in range(5):
        pet += (f'<g transform="rotate({i*72})">'
                f'<ellipse cx="0" cy="-16" rx="7.6" ry="13.5" fill="{petal}"/>'
                f'<ellipse cx="0" cy="-19" rx="5" ry="7" fill="#FFFFFF" opacity=".28"/></g>')
    f = f' filter="url(#b{blur})"' if blur else ''
    add(f'<g transform="translate({x},{y}) scale({s}) rotate({rot})" opacity="{op}"{f}>')
    add('<ellipse cx="0" cy="20" rx="25" ry="7" fill="#3F6B3A" opacity=".16" filter="url(#b6)"/>')
    add('<ellipse cx="-14" cy="10" rx="14" ry="5.5" fill="#4F9149" transform="rotate(-28)"/>')
    add('<ellipse cx="14" cy="11" rx="13" ry="5" fill="#63A854" transform="rotate(24)"/>')
    add(pet)
    add(f'<circle r="7.2" fill="{center}"/><circle cx="-2.2" cy="-2.4" r="2" fill="#FFF3C4" opacity=".75"/>')
    add('</g>')

def tree(x, y, s, blur=3, op=1):
    add(f'<g transform="translate({x},{y}) scale({s})" filter="url(#b{blur})" opacity="{op}">')
    add('<rect x="-4" y="10" width="8" height="60" rx="4" fill="#8C6B4A"/>')
    for i in range(7):
        cx = random.uniform(-34, 34); cy = random.uniform(-40, 4); r = random.uniform(20, 34)
        add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{random.choice(["#6FAF55","#7DBF60","#5C9C4A","#8CCB6C"])}"/>')
    add('</g>')

def butterfly(x, y, s, color='#F4CE67', op=.9):
    add(f'<g transform="translate({x},{y}) scale({s})" opacity="{op}">')
    add(f'<ellipse cx="-7" cy="-3" rx="8" ry="11" fill="{color}" transform="rotate(-25 -7 -3)"/>')
    add(f'<ellipse cx="7" cy="-3" rx="8" ry="11" fill="{color}" transform="rotate(25 7 -3)"/>')
    add(f'<ellipse cx="-5" cy="6" rx="5" ry="7" fill="#FFF3C9" transform="rotate(-20 -5 6)"/>')
    add(f'<ellipse cx="5" cy="6" rx="5" ry="7" fill="#FFF3C9" transform="rotate(20 5 6)"/>')
    add('<rect x="-1.4" y="-9" width="2.8" height="18" rx="1.4" fill="#8E5A2E"/>')
    add('</g>')

def pixel_art(x, y, cell, rows, pal):
    out = [f'<g transform="translate({x},{y})">']
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in pal and ch != '.':
                out.append(f'<rect x="{i*cell}" y="{j*cell}" width="{cell+0.4}" height="{cell+0.4}" fill="{pal[ch]}"/>')
    out.append('</g>')
    add(''.join(out))

add('''<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
 <stop offset="0" stop-color="#58BEF0"/><stop offset=".32" stop-color="#86D2F7"/>
 <stop offset=".66" stop-color="#C8EBFB"/><stop offset=".86" stop-color="#EAF7EE"/>
 <stop offset="1" stop-color="#F6FAE8"/>
</linearGradient>
<linearGradient id="grass" x1="0" y1="0" x2="0" y2="1">
 <stop offset="0" stop-color="#B7E08C"/><stop offset=".35" stop-color="#93CB70"/>
 <stop offset=".75" stop-color="#77B457"/><stop offset="1" stop-color="#5E9C48"/>
</linearGradient>
<linearGradient id="path" x1="0" y1="0" x2="0" y2="1">
 <stop offset="0" stop-color="#FBF3DC"/><stop offset=".45" stop-color="#F0E0BD"/><stop offset="1" stop-color="#DCC79F"/>
</linearGradient>
<linearGradient id="building" x1="0" y1="0" x2="0" y2="1">
 <stop offset="0" stop-color="#FDF6E3"/><stop offset=".55" stop-color="#F3E5C6"/><stop offset="1" stop-color="#DFCAA4"/>
</linearGradient>
<linearGradient id="stone" x1="0" y1="0" x2="0" y2="1">
 <stop offset="0" stop-color="#F7EDD5"/><stop offset="1" stop-color="#DBC7A2"/>
</linearGradient>
<linearGradient id="wood" x1="0" y1="0" x2="0" y2="1">
 <stop offset="0" stop-color="#DCA365"/><stop offset="1" stop-color="#A96C38"/>
</linearGradient>
<linearGradient id="gold" x1="0" y1="0" x2="0" y2="1">
 <stop offset="0" stop-color="#F2CD74"/><stop offset=".5" stop-color="#D8A94E"/><stop offset="1" stop-color="#B47E2E"/>
</linearGradient>
<radialGradient id="sun" cx=".5" cy=".5" r=".5">
 <stop offset="0" stop-color="#FFF7CF" stop-opacity=".95"/><stop offset=".35" stop-color="#FFF3B8" stop-opacity=".55"/><stop offset="1" stop-color="#FFF3B8" stop-opacity="0"/>
</radialGradient>
<radialGradient id="vignette" cx=".5" cy=".45" r=".75">
 <stop offset=".55" stop-color="#1F3A1E" stop-opacity="0"/><stop offset=".85" stop-color="#1F3A1E" stop-opacity=".08"/><stop offset="1" stop-color="#1F3A1E" stop-opacity=".2"/>
</radialGradient>
<filter id="b2" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="2"/></filter>
<filter id="b4" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="4"/></filter>
<filter id="b6" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="6"/></filter>
<filter id="b7" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="7"/></filter>
<filter id="b10" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="10"/></filter>
<filter id="b16" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="16"/></filter>
<filter id="b24" x="-70%" y="-70%" width="240%" height="240%"><feGaussianBlur stdDeviation="24"/></filter>
<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" stitchTiles="stitch"/>
 <feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncA type="linear" slope=".055"/></feComponentTransfer></filter>
<clipPath id="facadeClip"><path d="M-40 700 Q-40 500 170 500 Q380 500 380 760 L380 1300 L-40 1300 Z"/></clipPath>
<linearGradient id="warmEdge" x1="0" y1="0" x2="1" y2="0">
 <stop offset="0" stop-color="#FFF3C9" stop-opacity="0"/><stop offset="1" stop-color="#FFF3C9" stop-opacity=".42"/>
</linearGradient>
</defs>''')

add(f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')
add('<circle cx="880" cy="180" r="420" fill="url(#sun)"/>')
add('<circle cx="892" cy="172" r="74" fill="#FFF8D8" opacity=".75" filter="url(#b16)"/>')

cloud(120, 210, 1.15, .95)
cloud(520, 110, .95, .85)
cloud(860, 330, 1.0, .9)
cloud(40, 470, .85, .8)
cloud(960, 520, .9, .85)
cloud(300, 370, .65, .6)
cloud(700, 620, .7, .55)
butterfly(200, 430, 1.0, '#F4CE67', .9)
butterfly(780, 650, .8, '#F4A6C0', .8)

add('<path d="M0 1040 Q180 940 360 1010 T720 1000 T1080 960 L1080 1200 L0 1200 Z" fill="#BCE3A6" filter="url(#b16)" opacity=".9"/>')
add('<path d="M0 1090 Q240 1000 460 1070 T820 1050 T1080 1020 L1080 1250 L0 1250 Z" fill="#94CF7C" filter="url(#b10)" opacity=".95"/>')
add('<path d="M0 1140 Q260 1060 520 1120 T1080 1090 L1080 1320 L0 1320 Z" fill="#78BB5E" filter="url(#b6)"/>')

for x, y, s in [(250, 1090, 1.2), (330, 1120, 1.05), (690, 1080, 1.1), (770, 1110, 1.2), (880, 1100, 1.0), (160, 1110, .95)]:
    tree(x, y, s, 4, .9)

add('<rect x="0" y="1150" width="1080" height="770" fill="url(#grass)"/>')
add('<path d="M0 1220 Q260 1160 540 1190 T1080 1170 L1080 1920 L0 1920 Z" fill="#9FD374" opacity=".55"/>')

add('<ellipse cx="540" cy="1200" rx="330" ry="95" fill="#EADCB9" opacity=".85" filter="url(#b6)"/>')
add('<path d="M436 1160 L648 1160 L822 1920 L258 1920 Z" fill="url(#path)"/>')
add('<path d="M470 1170 L614 1170 L700 1920 L380 1920 Z" fill="#FBF4DF" opacity=".55"/>')
add('<path d="M436 1160 L648 1160 L822 1920 L258 1920 Z" fill="none" stroke="#C9AE82" stroke-width="12" opacity=".35"/>')
random.seed(5)
for i in range(12):
    yy = 1186 + i * 60
    t = (yy - 1160) / 760
    half = 90 + 155 * t
    n = 2 if i < 4 else 3
    for k in range(n):
        cx = 540 + (k - (n - 1) / 2) * (half * 1.15) + random.uniform(-8, 8)
        w = (half * 0.78) * (0.82 + random.uniform(-.10, .12))
        h = 22 + 10 * t
        rot = random.uniform(-3, 3)
        add(f'<g transform="translate({cx:.1f},{yy}) rotate({rot:.1f})">'
            f'<rect x="{-w/2:.1f}" y="{-h/2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h*.42:.1f}" '
            f'fill="#FFF9E8" fill-opacity=".55" stroke="#D6BE93" stroke-width="1.5" stroke-opacity=".55"/>'
            f'<rect x="{-w/2+8:.1f}" y="{-h/2+4:.1f}" width="{w-16:.1f}" height="{h*.28:.1f}" rx="{h*.14:.1f}" fill="#FFFFFF" opacity=".22"/></g>')
for side in (-1, 1):
    for i in range(10):
        yy = 1200 + i * 70
        t = (yy - 1160) / 760
        xx = 540 + side * (108 + 168 * t)
        add(f'<ellipse cx="{xx:.1f}" cy="{yy}" rx="{19+11*t:.1f}" ry="{10+4*t:.1f}" fill="#F3E6C7" opacity=".85" stroke="#D6BE93" stroke-width="2"/>')
for i in range(18):
    side = random.choice([-1, 1])
    yy = random.uniform(1200, 1750)
    t = (yy - 1160) / 760
    xx = 540 + side * (120 + 168 * t) + random.uniform(-16, 16)
    add(f'<path d="M{xx:.1f} {yy:.1f} q-6 -18 2 -28 q2 16 8 26 Z" fill="{random.choice(["#5FA84F","#6FB75B","#4F9149"])}" opacity=".8"/>')

add('<g id="gallery">')
add('<ellipse cx="120" cy="1290" rx="300" ry="70" fill="#3F6B3A" opacity=".18" filter="url(#b16)"/>')
add('<path d="M-40 700 Q-40 500 170 500 Q380 500 380 760 L380 1300 L-40 1300 Z" fill="url(#building)" stroke="#DCC59A" stroke-width="5"/>')
add('<g clip-path="url(#facadeClip)" stroke="#CBB085" stroke-width="2" opacity=".20">')
for yy in range(820, 1260, 64):
    add(f'<path d="M-40 {yy} Q170 {yy-14} 380 {yy}"/>')
add('</g>')
add('<rect x="250" y="760" width="130" height="500" fill="#C9A878" opacity=".10" clip-path="url(#facadeClip)"/>')
add('<rect x="330" y="740" width="50" height="520" fill="url(#warmEdge)" opacity=".75"/>')
add('<rect x="-40" y="1262" width="420" height="34" rx="16" fill="#E6D1AB" stroke="#CDB58C" stroke-width="3"/>')
add('<path d="M-40 700 Q-40 500 170 500 Q380 500 380 760" fill="none" stroke="url(#gold)" stroke-width="26" opacity=".95"/>')
add('<path d="M-20 720 Q-20 540 170 540 Q350 540 350 770" fill="none" stroke="#FFF6DC" stroke-width="10" opacity=".8"/>')
for cx in (28, 110, 300):
    add(f'<rect x="{cx}" y="760" width="26" height="470" rx="13" fill="#FAEFD2"/>')
    add(f'<rect x="{cx+4}" y="770" width="7" height="450" rx="4" fill="#FFFFFF" opacity=".65"/>')
    add(f'<rect x="{cx-5}" y="754" width="36" height="18" rx="8" fill="#EAD8B4"/>')
    add(f'<rect x="{cx-5}" y="1218" width="36" height="18" rx="8" fill="#DDC69E"/>')
add('<rect x="20" y="792" width="190" height="246" rx="8" fill="url(#gold)" stroke="#B47E2E" stroke-width="3"/>')
add('<rect x="33" y="805" width="164" height="220" fill="#FFF8E6"/>')
add('<rect x="41" y="813" width="148" height="204" fill="#2B3040"/>')
pal = {'S': '#7EC8F2', 'B': '#3E7CC8', 'P': '#A07BD0', 'Y': '#F4CE67', 'G': '#6FAF55', 'D': '#3F7A46', 'O': '#E98A5A'}
pixel_art(41, 813, 12.3, [
    'SSSSSBBBBB', 'SSSYSSBBBB', 'SSYYYSSSBB', 'SSYYSSSSBB', 'SSSSSSSSBB',
    'GGGGGGGGGG', 'DGGGGGGGGD', 'DDGGGGGGDD', 'DDDPGGGDDD', 'DDDDPGDDDD',
    'DDDDDDDDDD', 'DDDDDDDDDD'], pal)
add('<rect x="41" y="1017" width="148" height="7" fill="#FFF3C9" opacity=".22"/>')
add('<circle cx="266" cy="700" r="27" fill="#F6E8C6" stroke="#D8B96E" stroke-width="4"/>')
add('<circle cx="266" cy="700" r="17" fill="#7EC8F2" stroke="#B47E2E" stroke-width="2"/>')
add('<path d="M266 683 L266 717 M249 700 L283 700" stroke="#FFF8E6" stroke-width="3" opacity=".8"/>')
add('<path d="M208 1000 Q208 930 266 930 Q324 930 324 1000 L324 1290 L208 1290 Z" fill="#9B7047"/>')
add('<path d="M216 1004 Q216 946 266 946 Q316 946 316 1004 L316 1286 L216 1286 Z" fill="#7A5334"/>')
add('<path d="M236 1010 Q236 968 266 968 Q296 968 296 1010 L296 1286 L236 1286 Z" fill="#5C3C27"/>')
add('<path d="M244 1020 Q244 984 266 984 Q288 984 288 1020 L288 1286 L244 1286 Z" fill="#43291B"/>')
add('<rect x="204" y="986" width="120" height="18" rx="8" fill="#D8B96E" stroke="#B47E2E" stroke-width="2"/>')
add('<circle cx="160" cy="620" r="30" fill="#F6E8C6" stroke="#D8B96E" stroke-width="4"/>')
add('<path d="M148 620 l10 -12 10 12 -10 12 Z" fill="#D8A94E"/>')
add('<rect x="-6" y="740" width="14" height="520" rx="7" fill="#F7E9C8" opacity=".9"/>')
add('<rect x="350" y="740" width="14" height="520" rx="7" fill="#F7E9C8" opacity=".9"/>')
for yy, ww in [(1288, 360), (1320, 400), (1352, 440)]:
    add(f'<rect x="{160-ww/2:.0f}" y="{yy}" width="{ww}" height="28" rx="12" fill="#F2E5C6" stroke="#D6C098" stroke-width="2"/>')
    add(f'<rect x="{160-ww/2+10:.0f}" y="{yy+4}" width="{ww-20}" height="9" rx="5" fill="#FFF8E6" opacity=".7"/>')
add('<path d="M-10 1180 q50 -55 105 0 l-12 90 q-40 22 -82 0 Z" fill="#C98A50"/>')
add('<ellipse cx="42" cy="1178" rx="58" ry="18" fill="#8B5A32" opacity=".55"/>')
bush(40, 1140, .8, 2)
bush(330, 1120, .55, 3)
# lantern
add('<rect x="352" y="950" width="22" height="32" rx="6" fill="#E8C36A" stroke="#A9762C" stroke-width="3"/>')
add('<circle cx="363" cy="966" r="6" fill="#FFF6C8" filter="url(#b4)"/>')
add('<rect x="358" y="936" width="10" height="16" rx="4" fill="#A9762C"/>')
add('</g>')

add('<g id="easel">')
add('<ellipse cx="940" cy="1385" rx="185" ry="42" fill="#3F6B3A" opacity=".22" filter="url(#b10)"/>')
add('<path d="M946 1220 L960 1390 L938 1394 L932 1220 Z" fill="#9C6334"/>')
add('<path d="M866 1388 L902 1170 L930 1170 L900 1392 Z" fill="url(#wood)" stroke="#8E5A2E" stroke-width="3"/>')
add('<path d="M1018 1392 L986 1170 L958 1170 L984 1390 Z" fill="url(#wood)" stroke="#8E5A2E" stroke-width="3"/>')
add('<path d="M884 1300 L1000 1300" stroke="#8E5A2E" stroke-width="14" stroke-linecap="round"/>')
add('<path d="M890 1288 L996 1288" stroke="#E0A66C" stroke-width="5" opacity=".7"/>')
add('<rect x="850" y="976" width="240" height="284" rx="6" fill="#8B5A32" opacity=".20" filter="url(#b6)"/>')
add('<rect x="834" y="960" width="244" height="290" rx="8" fill="#F9EFD8" stroke="url(#gold)" stroke-width="14"/>')
add('<rect x="850" y="976" width="212" height="258" fill="#F7F0DE"/>')
pal2 = {'P': '#EF8FB6', 'O': '#E98A5A', 'Y': '#F4CE67', 'G': '#6FAF55', 'W': '#FFF9EC', 'B': '#8FCBEE'}
pixel_art(850, 976, 17.6, [
    'WWWWWWWWWW', 'WWWPPWWWWW', 'WWPPPPWWWW', 'WPPPOPPWWW', 'WWPOOOPWWW',
    'WWWOOOWWWW', 'WWWWGWWWWW', 'WWWGGGWWWW', 'WWBWGWBWWW', 'WWWWGWWWWW',
    'WWGGGGGWWW', 'WWWWGWWWWW', 'WWWWGWWWWW', 'WWWWWWWWWW'], pal2)
add('<rect x="850" y="976" width="8" height="258" fill="#FFF9E6" opacity=".35"/>')
add('<rect x="1050" y="972" width="10" height="278" fill="#FFF3C9" opacity=".35"/>')
add('<rect x="824" y="1236" width="264" height="22" rx="10" fill="url(#wood)" stroke="#8E5A2E" stroke-width="3"/>')
add('<rect x="840" y="1240" width="232" height="7" rx="4" fill="#F0C08A" opacity=".6"/>')
add('<path d="M1042 1372 q22 -30 44 0 l-6 26 q-16 9 -32 0 Z" fill="#D9A05C" stroke="#8E5A2E" stroke-width="3"/>')
add('<path d="M1062 1338 l10 34" stroke="#8E5A2E" stroke-width="5" stroke-linecap="round"/>')
add('<path d="M1058 1332 l4 -14 8 12" fill="#5C9C4A" stroke="#3F7A46" stroke-width="2"/>')
add('</g>')

add('<g id="beds">')
bush(-30, 1690, 2.2, 6)
bush(1110, 1710, 2.4, 6)
bush(255, 1850, 1.7, 8)
bush(855, 1860, 1.8, 8)
for x, y, s in [(150, 1310, 1.1), (60, 1380, 1.2), (980, 1300, 1.1), (1040, 1380, 1.2), (430, 1260, .7), (680, 1260, .7)]:
    bush(x, y, s, 3)
random.seed(21)
for i in range(26):
    side = random.choice([-1, 1])
    x = random.uniform(0, 300) if side < 0 else random.uniform(800, 1080)
    y = random.uniform(1190, 1550)
    flower(x, y, random.uniform(.55, 1.0), random.choice(['pink', 'white', 'yellow']), random.uniform(-20, 20), random.choice([0, 0, 2]), .95)
random.seed(33)
for i in range(16):
    flower(random.uniform(-20, 280), random.uniform(1500, 1830), random.uniform(1.0, 1.8), random.choice(['pink', 'white', 'yellow']), random.uniform(-25, 25), random.choice([2, 0, 0]), 1)
for i in range(16):
    flower(random.uniform(820, 1100), random.uniform(1480, 1830), random.uniform(1.0, 1.8), random.choice(['pink', 'white', 'yellow']), random.uniform(-25, 25), random.choice([2, 0, 0]), 1)
for x, y, s, c in [(80, 1870, 3.2, 'pink'), (280, 1900, 2.6, 'white'), (760, 1890, 2.8, 'yellow'), (1000, 1850, 3.0, 'pink'), (520, 1910, 2.4, 'white')]:
    flower(x, y, s, c, random.uniform(-20, 20), 16, .75)
add('</g>')

add('<path d="M1080 0 L1080 720 L520 1280 L300 1280 Z" fill="#FFF6C8" opacity=".10" filter="url(#b24)"/>')
add('<rect width="1080" height="1920" fill="url(#vignette)"/>')
add('<rect width="1080" height="1920" filter="url(#grain)" opacity=".5"/>')

svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">' + ''.join(parts) + '</svg>'
html = f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>html,body{{margin:0;padding:0;background:#fff}}svg{{display:block}}</style></head><body>{svg}</body></html>'
open('DesignAssets/UI_garden_kit/tools/bg_scene.html', 'w', encoding='utf-8').write(html)
print('svg parts', len(parts))
