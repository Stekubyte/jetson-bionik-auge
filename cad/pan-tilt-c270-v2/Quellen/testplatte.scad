// Spline-Testplatte: SG90 (NoName, 4,9 mm) oben, SG90TP (Tower Pro, 4,7 mm) unten
// Spalt (gap) von links nach rechts: 0,00 / 0,05 / 0,10 / 0,15 / 0,20 mm
use <customizable-servo-arm/customizable-servo-arm.scad>
SG90   = [[4.9,3.2,1.5,2.5],[21,0.25,0.65,0.25]];
SG90TP = [[4.7,3.2,1.5,2.5],[21,0.25,0.65,0.25]];
gaps = [0, 0.05, 0.10, 0.15, 0.20];
for (i=[0:4]) {
  translate([i*12, 12, 0]) servo_adapter(SG90, gaps[i]);
  translate([i*12, 0, 0])  servo_adapter(SG90TP, gaps[i]);
}
// Steg mit Markierungen: Anzahl Kerben = Spalte (1..5), Steg oben = SG90
difference(){
  union(){
    translate([-4,16.5,0]) cube([56,2,1]);
    translate([-4,-6.5,0]) cube([56,2,1]);
    for (i=[0:4]) { translate([i*12-1,16.5-1.1,0]) cube([2,1.5,1]); translate([i*12-1,-5,0]) cube([2,1.5,1]); }
  }
  for (i=[0:4]) for (k=[0:i]) translate([i*12-3+k*1.4,17.2,0.5]) cube([0.7,2,1]);
}
