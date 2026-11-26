#!/usr/bin/env python3
"""
Schritt 2: Webcam-Livebild prüfen (Logitech C270 am Jetson).

Aufruf:   python3 kamera_test.py            (Kamera /dev/video0)
          python3 kamera_test.py 1          (andere Kamera-Nummer)
Tasten:   q = beenden, s = Foto speichern (foto_1.jpg, foto_2.jpg, ...)

Zeigt:    tatsächliche Auflösung, Pixelformat, gemessene Bildrate (fps).
          Mittelkreuz und Randlinien helfen beim Messen des Bildwinkels (HFOV).
"""

import sys
import time

import cv2

KAMERA = int(sys.argv[1]) if len(sys.argv) > 1 else 0
BREITE, HOEHE = 640, 480          # wie in bionisches_auge.py

cap = cv2.VideoCapture(KAMERA, cv2.CAP_V4L2)
if not cap.isOpened():
    sys.exit("Kamera nicht gefunden. Prüfen mit: v4l2-ctl --list-devices")

cap.set(cv2.CAP_PROP_FRAME_WIDTH, BREITE)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HOEHE)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # nur das neueste Bild halten (weniger Totzeit)

# Was die Kamera wirklich liefert (kann von der Anfrage abweichen)
b = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
code = int(cap.get(cv2.CAP_PROP_FOURCC))
fourcc = "".join(chr((code >> 8 * i) & 0xFF) for i in range(4))   # z. B. YUYV oder MJPG
print(f"Auflösung: {b} x {h} px, Format: {fourcc}")

fotos = 0
n, t_start, fps = 0, time.monotonic(), 0.0
while True:
    ok, bild = cap.read()
    if not ok:
        print("Kein Bild erhalten. Kabel und Kamera-Nummer prüfen.")
        break

    # Bildrate über jeweils 30 Bilder mitteln: fps = Anzahl Bilder / Zeit
    n += 1
    if n == 30:
        fps = n / (time.monotonic() - t_start)
        n, t_start = 0, time.monotonic()

    hb, bb = bild.shape[:2]
    anzeige = bild.copy()
    # Mittelkreuz = optische Achse (dorthin soll das Auge später den Ball holen)
    cv2.drawMarker(anzeige, (bb // 2, hb // 2), (255, 255, 255), cv2.MARKER_CROSS, 30, 1)
    # Linke und rechte Bildkante markieren (für die HFOV-Messung am Maßband)
    cv2.line(anzeige, (2, 0), (2, hb), (0, 0, 255), 2)
    cv2.line(anzeige, (bb - 3, 0), (bb - 3, hb), (0, 0, 255), 2)
    cv2.putText(anzeige, f"{bb}x{hb}  {fourcc}  {fps:4.1f} fps", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.imshow("Kameratest (q = Ende, s = Foto)", anzeige)

    taste = cv2.waitKey(1) & 0xFF
    if taste == ord("q"):
        break
    if taste == ord("s"):
        fotos += 1
        name = f"foto_{fotos}.jpg"
        cv2.imwrite(name, bild)          # Originalbild ohne Markierungen
        print(f"Gespeichert: {name}")

print(f"Letzte gemessene Bildrate: {fps:.1f} fps")
cap.release()
cv2.destroyAllWindows()
