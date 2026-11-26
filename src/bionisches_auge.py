#!/usr/bin/env python3
"""
Bionisches Auge, Stufe 1: Eine Pan-Tilt-Kamera folgt einem farbigen Ball.

Hardware
  Jetson Orin Nano Dev Kit, USB-Webcam, 2x SG90, PCA9685 an I2C-Bus 7 (Header-Pins 3 und 5).

Bionik: zwei Betriebsarten wie beim menschlichen Auge
  Folgebewegung (smooth pursuit): kleiner Fehler -> I-Regler mit Gain G_FOLGE.
  Sakkade: großer Fehler -> Sprung direkt aufs Ziel. Danach werden Bilder kurz
           ignoriert (sakkadische Suppression), bis der Servo angekommen ist.
  Fixation: Fehler in der Totzone -> keine Bewegung.

Aufruf
  python3 bionisches_auge.py --test     Servos testen (zuerst ohne Kamera auf dem Halter!)
  python3 bionisches_auge.py --hsv      Farbschwelle für den Ball mit Schiebereglern einstellen
  python3 bionisches_auge.py            Tracking starten, Messdaten landen in messung.csv
  Beenden mit q im Bildfenster oder Strg+C.

Stand 26.11.2026: Kamera und Farberkennung laufen auf dem Jetson. Servoansteuerung und
geschlossener Regelkreis sind noch nicht auf der Hardware getestet. Vorzeichen und Pulsbereich beim
ersten Start prüfen.
"""

import argparse
import csv
import math
import time

import cv2
import numpy as np
from smbus2 import SMBus

# ---------------- Einstellungen ----------------
I2C_BUS = 7            # Pins 3/5 am Orin Nano Dev Kit. Prüfen: sudo i2cdetect -y -r 7
PCA_ADDR = 0x40        # Standardadresse des PCA9685
KANAL_PAN, KANAL_TILT = 0, 1

PULS_MIN_US, PULS_MAX_US = 500, 2400   # typischer SG90-Bereich für 0..180°. Brummt der Servo
                                       # am Ende, Bereich verkleinern.
WINKEL_MIN, WINKEL_MAX = 20.0, 160.0   # mechanische Grenzen deines Halters
RICHTUNG_PAN, RICHTUNG_TILT = -1, 1    # Vorzeichen je nach Einbau. Läuft das Auge vom Ball weg: umdrehen.

KAMERA = 0                 # /dev/video0
BREITE, HOEHE = 640, 480
HFOV_GRAD = 60.0           # Annahme für eine typische Webcam. Besser: f_x per Kalibrierung bestimmen.

HSV_UNTEN = (22, 105, 124)  # gemessen am 21.11.2026 mit --hsv (gelber Ball)
HSV_OBEN = (48, 255, 255)
MIN_FLAECHE_PX = 300       # kleinere Flecken gelten als Rauschen

G_FOLGE = 0.4              # I-Gain Folgebewegung. Theorie: stabil für g < 0,618 bei 2 Takten Totzeit
TOTZONE_GRAD = 1.0         # Fixation: darunter keine Korrektur (PWM-Auflösung ca. 0,5°)
SAKKADE_AB_GRAD = 8.0      # ab diesem Fehler springt das Auge
SUPPRESSION_S = 0.25       # so lange nach einer Sakkade keine Bilder auswerten


# ---------------- PCA9685 direkt über smbus2 ----------------
class PCA9685:
    """Minimaltreiber. Umgeht Adafruit Blinka, das auf dem Orin Nano oft das Board nicht erkennt."""
    MODE1, PRESCALE, LED0_ON_L = 0x00, 0xFE, 0x06

    def __init__(self, bus_nr, addr=0x40, freq_hz=50):
        self.bus = SMBus(bus_nr)
        self.addr = addr
        self.freq = freq_hz
        # Prescaler = round(f_osc / (4096 * f_pwm)) - 1, f_osc = 25 MHz -> 121 bei 50 Hz
        prescale = round(25_000_000 / (4096 * freq_hz)) - 1
        self.bus.write_byte_data(addr, self.MODE1, 0x10)      # Sleep (nur dann darf der Prescaler gesetzt werden)
        self.bus.write_byte_data(addr, self.PRESCALE, prescale)
        self.bus.write_byte_data(addr, self.MODE1, 0x00)      # aufwecken
        time.sleep(0.001)                                     # Oszillator braucht max. 500 µs
        self.bus.write_byte_data(addr, self.MODE1, 0x20)      # Auto-Increment für Blockschreiben

    def puls_us(self, kanal, us):
        # 1 Zählschritt = 1 / (f_pwm * 4096) ≈ 4,88 µs bei 50 Hz
        counts = int(round(us * self.freq * 4096 / 1e6))
        counts = max(0, min(4095, counts))
        self.bus.write_i2c_block_data(self.addr, self.LED0_ON_L + 4 * kanal,
                                      [0, 0, counts & 0xFF, counts >> 8])

    def aus(self, kanal):
        # Bit 4 in LEDn_OFF_H = "full off": Servo wird kraftlos statt Position zu halten
        self.bus.write_i2c_block_data(self.addr, self.LED0_ON_L + 4 * kanal, [0, 0, 0, 0x10])

    def close(self):
        self.bus.close()


class Servo:
    def __init__(self, pca, kanal, start_grad=90.0):
        self.pca, self.kanal = pca, kanal
        self.winkel = start_grad
        self.setze(start_grad)

    def setze(self, winkel_grad):
        self.winkel = min(max(winkel_grad, WINKEL_MIN), WINKEL_MAX)
        us = PULS_MIN_US + (PULS_MAX_US - PULS_MIN_US) * self.winkel / 180.0
        self.pca.puls_us(self.kanal, us)


# ---------------- Bildverarbeitung ----------------
def finde_ziel(bild, unten, oben):
    """Liefert den Schwerpunkt (x, y) des größten Flecks in der Farbschwelle oder None."""
    hsv = cv2.cvtColor(bild, cv2.COLOR_BGR2HSV)
    maske = cv2.inRange(hsv, np.array(unten, np.uint8), np.array(oben, np.uint8))
    maske = cv2.morphologyEx(maske, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))  # Rauschen entfernen
    konturen, _ = cv2.findContours(maske, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not konturen:
        return None, maske
    k = max(konturen, key=cv2.contourArea)
    if cv2.contourArea(k) < MIN_FLAECHE_PX:
        return None, maske
    m = cv2.moments(k)
    return (m["m10"] / m["m00"], m["m01"] / m["m00"]), maske


def pixel_zu_grad(dx_px, f_px):
    """theta = arctan(dx / f): Winkel zwischen optischer Achse und Ziel."""
    return math.degrees(math.atan(dx_px / f_px))


def oeffne_kamera():
    cap = cv2.VideoCapture(KAMERA, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, BREITE)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HOEHE)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # alte Bilder im Puffer erhöhen die Totzeit
    if not cap.isOpened():
        raise RuntimeError("Kamera nicht gefunden. Prüfen mit: v4l2-ctl --list-devices")
    return cap


# ---------------- Modi ----------------
def servo_test():
    pca = PCA9685(I2C_BUS, PCA_ADDR)
    pan, tilt = Servo(pca, KANAL_PAN), Servo(pca, KANAL_TILT)
    try:
        for w in (90, 60, 120, 90):
            print(f"Pan {w}°")
            pan.setze(w)
            time.sleep(1)
        for w in (90, 60, 120, 90):
            print(f"Tilt {w}°")
            tilt.setze(w)
            time.sleep(1)
    finally:
        pca.aus(KANAL_PAN)
        pca.aus(KANAL_TILT)
        pca.close()


def hsv_einstellen():
    cap = oeffne_kamera()
    fenster = "HSV einstellen (q = fertig)"
    cv2.namedWindow(fenster)
    namen = ["H min", "S min", "V min", "H max", "S max", "V max"]
    for name, start in zip(namen, HSV_UNTEN + HSV_OBEN):
        cv2.createTrackbar(name, fenster, start, 179 if name.startswith("H") else 255, lambda v: None)
    try:
        while True:
            ok, bild = cap.read()
            if not ok:
                break
            werte = [cv2.getTrackbarPos(n, fenster) for n in namen]
            ziel, maske = finde_ziel(bild, werte[:3], werte[3:])
            if ziel:
                cv2.circle(bild, (int(ziel[0]), int(ziel[1])), 8, (0, 0, 255), 2)
            cv2.imshow(fenster, bild)
            cv2.imshow("Maske", maske)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print(f"HSV_UNTEN = {tuple(werte[:3])}\nHSV_OBEN = {tuple(werte[3:])}")
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


def tracking(log_datei, anzeige=True):
    pca = PCA9685(I2C_BUS, PCA_ADDR)
    pan, tilt = Servo(pca, KANAL_PAN), Servo(pca, KANAL_TILT)
    cap = oeffne_kamera()
    breite = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or BREITE
    # Brennweite in Pixeln aus dem Bildwinkel: f_x = (B/2) / tan(HFOV/2)
    fx = (breite / 2) / math.tan(math.radians(HFOV_GRAD / 2))
    fy = fx  # quadratische Pixel angenommen

    log = open(log_datei, "w", newline="")
    schreiber = csv.writer(log)
    schreiber.writerow(["t_s", "modus", "fehler_x_grad", "fehler_y_grad", "pan_grad", "tilt_grad"])

    t0 = time.monotonic()
    gesperrt_bis = 0.0
    try:
        while True:
            ok, bild = cap.read()
            if not ok:
                break
            t = time.monotonic() - t0
            h_px, b_px = bild.shape[:2]
            ziel, _ = finde_ziel(bild, HSV_UNTEN, HSV_OBEN)

            if ziel is None:
                modus = "verloren"
            elif t < gesperrt_bis:
                modus = "suppression"
            else:
                ex = pixel_zu_grad(ziel[0] - b_px / 2, fx)
                ey = pixel_zu_grad(ziel[1] - h_px / 2, fy)
                fehler = math.hypot(ex, ey)
                if fehler > SAKKADE_AB_GRAD:
                    modus, g = "sakkade", 1.0          # ganzer Sprung, dann Suppression
                    gesperrt_bis = t + SUPPRESSION_S
                elif fehler > TOTZONE_GRAD:
                    modus, g = "folge", G_FOLGE        # u_k = u_{k-1} + g * e_k (I-Regler)
                else:
                    modus, g = "fixation", 0.0
                pan.setze(pan.winkel + RICHTUNG_PAN * g * ex)
                tilt.setze(tilt.winkel + RICHTUNG_TILT * g * ey)
                schreiber.writerow([f"{t:.3f}", modus, f"{ex:.2f}", f"{ey:.2f}",
                                    f"{pan.winkel:.1f}", f"{tilt.winkel:.1f}"])

            if anzeige:
                if ziel:
                    cv2.circle(bild, (int(ziel[0]), int(ziel[1])), 8, (0, 0, 255), 2)
                cv2.drawMarker(bild, (b_px // 2, h_px // 2), (255, 255, 255), cv2.MARKER_CROSS, 20, 1)
                cv2.putText(bild, modus, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow("Bionisches Auge (q = Ende)", bild)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        log.close()
        pca.aus(KANAL_PAN)
        pca.aus(KANAL_TILT)
        pca.close()
        cv2.destroyAllWindows()
        print(f"Messdaten gespeichert in {log_datei}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Bionisches Auge: Pan-Tilt-Tracking mit Sakkaden")
    p.add_argument("--test", action="store_true", help="nur Servos testen")
    p.add_argument("--hsv", action="store_true", help="Farbschwelle einstellen")
    p.add_argument("--log", default="messung.csv", help="CSV-Datei für Messdaten")
    p.add_argument("--ohne-anzeige", action="store_true", help="kein Bildfenster (z. B. über SSH)")
    a = p.parse_args()
    if a.test:
        servo_test()
    elif a.hsv:
        hsv_einstellen()
    else:
        tracking(a.log, anzeige=not a.ohne_anzeige)
