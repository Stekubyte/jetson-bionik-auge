#!/usr/bin/env python3
"""
Übung vor der Webcam: Einen Ball auf einem Foto per Farbe finden (Schritt 3 ohne Kamera).

Aufruf:  python3 ball_foto.py ball.jpg
Bedienung: Schieberegler bewegen, bis in der Maske nur der Ball weiß ist.
           q drückt die gefundenen HSV-Werte ins Terminal und beendet.
           Diese Werte trägst du später in bionisches_auge.py ein (HSV_UNTEN, HSV_OBEN).
"""

import sys

import cv2
import numpy as np

if len(sys.argv) < 2:
    sys.exit("Bitte Bilddatei angeben, z. B.: python3 ball_foto.py ball.jpg")

bild = cv2.imread(sys.argv[1])                 # Bild als Zahlentabelle laden (Farben in BGR)
if bild is None:
    sys.exit(f"Bild nicht gefunden oder nicht lesbar: {sys.argv[1]}")

# Handyfotos sind riesig. Auf 640 px Breite verkleinern, wie später das Webcam-Bild.
faktor = 640 / bild.shape[1]
bild = cv2.resize(bild, None, fx=faktor, fy=faktor)

hsv = cv2.cvtColor(bild, cv2.COLOR_BGR2HSV)    # in HSV umrechnen: H = Farbton, S = Sättigung, V = Helligkeit

fenster = "Regler (q = fertig)"
cv2.namedWindow(fenster)
# Startwerte: grob gelbgrün bis grün (Tennisball liegt etwa bei H 25 bis 45)
start = {"H min": 25, "S min": 80, "V min": 60, "H max": 80, "S max": 255, "V max": 255}
for name, wert in start.items():
    obergrenze = 179 if name.startswith("H") else 255   # OpenCV: H 0..179, S und V 0..255
    cv2.createTrackbar(name, fenster, wert, obergrenze, lambda v: None)

while True:
    w = [cv2.getTrackbarPos(n, fenster) for n in start]
    unten, oben = np.array(w[:3], np.uint8), np.array(w[3:], np.uint8)

    maske = cv2.inRange(hsv, unten, oben)                                   # Ball weiß, Rest schwarz
    maske = cv2.morphologyEx(maske, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))  # kleine Störflecken weg

    anzeige = bild.copy()
    konturen, _ = cv2.findContours(maske, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if konturen:
        k = max(konturen, key=cv2.contourArea)     # größte weiße Fläche = vermutlich der Ball
        m = cv2.moments(k)
        if m["m00"] > 0:
            x, y = int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"])   # Schwerpunkt in Pixeln
            cv2.circle(anzeige, (x, y), 10, (0, 0, 255), 2)
            cv2.putText(anzeige, f"Ball bei x={x}, y={y}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("Foto", anzeige)
    cv2.imshow("Maske", maske)
    if cv2.waitKey(30) & 0xFF == ord("q"):
        print(f"HSV_UNTEN = {tuple(w[:3])}")
        print(f"HSV_OBEN = {tuple(w[3:])}")
        break

cv2.destroyAllWindows()
