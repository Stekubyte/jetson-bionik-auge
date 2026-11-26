// Druckbare SG90-Hoerner in der Form der Original-Hoerner (Masse vom Produktbild)
// Verzahnung aus mezger/customizable-servo-arm (LGPL-2.1), 21 Zaehne
use <customizable-servo-arm/customizable-servo-arm.scad>
preset = "SG90";      // SG90 = NoName 4,9 mm, SG90TP = Tower Pro 4,7 mm
gap    = 0.10;        // nach Testplatte anpassen
form   = "kreuz";     // einarm | doppel | kreuz
arm_t  = 1.6;         // Armdicke (Annahme, am Original messen)
loch_d = 1.2;         // Loch-Durchmesser in den Armen
loch_a = 2.5;         // Lochabstand
$fn = 48;
SG90   = [[4.9,3.2,1.05,2.5],[21,0.25,0.65,0.25]];   // Wand 1,05 mm -> Nabe ca. 7,0 mm
SG90TP = [[4.7,3.2,1.15,2.5],[21,0.25,0.65,0.25]];   // Nabe ca. 7,0 mm
P = preset=="SG90" ? SG90 : SG90TP;
nabe_r = P[0][0]/2 + P[0][2];

module arm(spitze) {          // spitze = Abstand Mitte bis Armende
  r_tip = 2;
  difference() {
    hull() { cylinder(r=3, h=arm_t); translate([spitze-r_tip,0,0]) cylinder(r=r_tip, h=arm_t); }
    cylinder(r=nabe_r-0.1, h=arm_t);
    for (x=[spitze-r_tip : -loch_a : nabe_r+loch_d]) translate([x,0,-1]) cylinder(d=loch_d, h=arm_t+2);
  }
}
module horn() {
  if (form=="einarm") arm(18.5);                       // 22 mm gesamt mit Nabe
  if (form=="doppel") { arm(17.5); rotate(180) arm(17.5); }   // 35 mm
  if (form=="kreuz")  { arm(17.5); rotate(180) arm(17.5); rotate(90) arm(9); rotate(270) arm(9); } // 35 x 18 mm
  servo_adapter(P, gap);
}
horn();
