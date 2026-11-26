"""Pan-Tilt V2 fuer SG90 (LYMISPIYA) + gedruckte Hoerner + Logitech C270.
Basis: fbuenonet 'Mini Pan Tilt - Servo G9' (Thingiverse thing:708819, CC BY-SA).
Gelenkmasse C270 aus adamoell 'Logitech C270 Tripod Mount' (thing:4233794, CC BY).
Aufruf: python3 v2_bauen.py <ordner_mit_original_stl> <ausgabeordner>
"""
import sys, numpy as np, trimesh, manifold3d as mf
from shapely.geometry import Polygon
src, out = sys.argv[1], sys.argv[2]

def to_mf(t):
    t = t.copy(); t.merge_vertices()
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
def to_tm(m):
    g = m.to_mesh(); return trimesh.Trimesh(g.vert_properties[:, :3], g.tri_verts, process=True)
def box(x0,x1,y0,y1,z0,z1): return mf.Manifold.cube([x1-x0,y1-y0,z1-z0]).translate([x0,y0,z0])
def cyl_y(x,z,r,y0,y1,n=64): return mf.Manifold.cylinder(y1-y0, r, r, n).rotate([-90,0,0]).translate([x,y0,z])

# ---------- Plataforma: Kreuztasche fuer Kreuzhorn 35 x 18 mm ----------
P = trimesh.load(f'{src}/Pan-tilt-plataforma.stl')
sec, T = P.section(plane_origin=[0,0,2.2], plane_normal=[0,0,1]).to_2D()
hole = max((Polygon(h) for pp in sec.polygons_full for h in pp.interiors), key=lambda h: h.area)
hole = Polygon(np.asarray(hole.exterior.coords) + T[:2,3])
TASCHE_ZUGABE = 0.75                                  # mm je Seite -> ca. 36,6 x 18,5 mm
from shapely.geometry.polygon import orient
grow = orient(hole.buffer(TASCHE_ZUGABE, join_style=2), 1.0)
cs = mf.CrossSection([np.asarray(grow.exterior.coords)[:-1]])
cut = mf.Manifold.extrude(cs, 3.4).translate([0,0,1.9])   # Boden bei z = 1,9 mm bleibt
# Original-Tasche ist um die Wellenmitte (x = 16,5) unsymmetrisch -> gespiegelt ergaenzen,
# damit das symmetrische gedruckte Kreuzhorn UND das Originalhorn passen
WX = 16.5
cut = cut + cut.mirror([1,0,0]).translate([2*WX,0,0])
plat = to_mf(P) - cut
print('Plataforma Tasche neu: %.2f x %.2f mm' % (grow.bounds[2]-grow.bounds[0], grow.bounds[3]-grow.bounds[1]))

# ---------- Tapa: Ausnehmung fuer Einarmhorn 22 x 7 mm, Nabe 7 mm ----------
Tm = to_mf(trimesh.load(f'{src}/Pan-tilt-tapa.stl'))
NX, NZ = 54.0, 5.7                                    # Nabenmitte (gemessen)
R_AUS = 3.8                                           # halbe Breite Ausnehmung / Nabenloch 7,6 mm
slot = mf.Manifold.batch_hull([cyl_y(NX,NZ,R_AUS,-10.4,-8.25), cyl_y(35.3+2.2,NZ,2.2,-10.4,-8.25)])  # Arm verjuengt zur Spitze
tapa = Tm - slot - cyl_y(NX,NZ,R_AUS,-10.4,-7.1)
print('Tapa Ausnehmung: Spitze x=%.1f bis Nabe x=%.1f -> %.1f mm lang, Nabe 7,6 mm' % (35.3, NX+R_AUS, NX+R_AUS-35.3))

# ---------- Kameraplatte: Pfostenabstand 23,5 mm + Gelenkgabel fuer C270 ----------
K = to_mf(trimesh.load(f'{src}/Pan-tilt-base-camara.stl'))
K = K - box(8.25,8.5+0.01,9.4,15.6,5.75,17.1) - box(31.5-0.01,31.75,9.4,15.6,5.75,17.1)
GB, GD, SPALT, BOHR = 27.0, 6.8, 7.4, 3.3             # Gabelbreite, -dicke, Spalt, Bohrung (M3)
YM = 45.5/2                                           # Plattenmitte in y
XA = 40.0 + 7.0                                       # Gelenkachse 7 mm vor der Plattenkante
gabel = box(36.5, XA, YM-GB/2, YM+GB/2, 0, GD) + cyl_y(XA, GD/2, GD/2, YM-GB/2, YM+GB/2)
gabel = gabel - box(40.2, XA+GD, YM-SPALT/2, YM+SPALT/2, -1, GD+1) - cyl_y(XA, GD/2, BOHR/2, YM-GB/2-1, YM+GB/2+1, 48)
# Fase an der Spaltkante, damit das Kameragelenk drehen kann
kam = K + gabel
print('Kameraplatte: Gabel %.1f mm breit, Spalt %.1f mm, Achse x=%.1f, z=%.1f, Bohrung %.1f mm' % (GB,SPALT,XA,GD/2,BOHR))

for name, m in [] or [('Plataforma_V2', plat), ('Tapa_V2', tapa), ('Kameraplatte_C270_V2', kam)]:
    print(name, 'Status', m.status(), 'Vol', round(m.volume(),1))
    t = to_tm(m); t.export(f'{out}/{name}.stl')
    print(name, np.round(t.extents,2), 'dicht' if t.is_watertight else 'NICHT dicht', '%.2f cm3' % (t.volume/1000))
