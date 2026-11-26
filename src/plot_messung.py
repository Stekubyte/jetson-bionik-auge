#!/usr/bin/env python3
"""
Auswertung einer Tracking-Messung von bionisches_auge.py.

Liest messung.csv (Spalten: t_s, modus, fehler_x_grad, fehler_y_grad, pan_grad, tilt_grad),
zeichnet Blickfehler und Servowinkel über der Zeit und gibt Kennwerte aus.

Aufruf:   python3 plot_messung.py                  (liest messung.csv, speichert messung.png)
          python3 plot_messung.py lauf2.csv        (andere Datei)
Benötigt: matplotlib (pip install matplotlib). Läuft auch auf dem PC, nicht nur auf dem Jetson.
"""

import csv
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # ohne Bildschirm lauffähig, Bild wird als PNG gespeichert
import matplotlib.pyplot as plt

# Farben je Betriebsart (Zustandsautomat im Hauptskript)
FARBEN = {"fixation": "#2e7d32", "folge": "#1565c0", "sakkade": "#c62828"}


def lese_messung(pfad):
    """CSV einlesen und Spalten als Listen zurückgeben."""
    daten = {"t": [], "modus": [], "ex": [], "ey": [], "pan": [], "tilt": []}
    with open(pfad, newline="", encoding="utf-8") as f:
        for zeile in csv.DictReader(f):
            daten["t"].append(float(zeile["t_s"]))
            daten["modus"].append(zeile["modus"])
            daten["ex"].append(float(zeile["fehler_x_grad"]))
            daten["ey"].append(float(zeile["fehler_y_grad"]))
            daten["pan"].append(float(zeile["pan_grad"]))
            daten["tilt"].append(float(zeile["tilt_grad"]))
    if not daten["t"]:
        sys.exit(f"{pfad} enthält keine Messwerte.")
    return daten


def kennwerte(d):
    """RMS-Blickfehler je Betriebsart, Anzahl Sakkaden und mittlere Bildrate."""
    gesamt = [math.hypot(x, y) for x, y in zip(d["ex"], d["ey"])]
    print(f"Messdauer:        {d['t'][-1] - d['t'][0]:.1f} s, {len(d['t'])} Bilder")
    if len(d["t"]) > 1:
        dt = (d["t"][-1] - d["t"][0]) / (len(d["t"]) - 1)
        print(f"Mittlere Bildrate: {1 / dt:.1f} fps (Abtastzeit {dt * 1000:.0f} ms)")
    for modus in sorted(set(d["modus"])):
        werte = [e for e, m in zip(gesamt, d["modus"]) if m == modus]
        rms = math.sqrt(sum(e * e for e in werte) / len(werte))
        print(f"RMS-Fehler {modus:<9} {rms:5.2f}°  ({len(werte)} Bilder)")
    # Eine Sakkade = Wechsel in den Modus "sakkade"
    starts = sum(1 for a, b in zip(d["modus"], d["modus"][1:]) if b == "sakkade" and a != "sakkade")
    starts += d["modus"][0] == "sakkade"
    print(f"Sakkaden:          {starts}")


def zeichne(d, ziel_png):
    t0 = d["t"][0]
    t = [x - t0 for x in d["t"]]
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(9, 6))

    ax1.plot(t, d["ex"], color="#555", lw=1, label="Fehler x (Pan)")
    ax1.plot(t, d["ey"], color="#999", lw=1, ls="--", label="Fehler y (Tilt)")
    # Betriebsart als farbige Punkte, damit Sakkaden sichtbar werden
    for modus, farbe in FARBEN.items():
        tm = [ti for ti, m in zip(t, d["modus"]) if m == modus]
        em = [e for e, m in zip(d["ex"], d["modus"]) if m == modus]
        if tm:
            ax1.scatter(tm, em, s=8, color=farbe, label=modus, zorder=3)
    ax1.axhline(0, color="black", lw=0.5)
    ax1.set_ylabel("Blickfehler in °")
    ax1.legend(loc="upper right", fontsize=8, ncol=2)
    ax1.grid(alpha=0.3)

    ax2.plot(t, d["pan"], label="Pan")
    ax2.plot(t, d["tilt"], label="Tilt")
    ax2.set_xlabel("Zeit in s")
    ax2.set_ylabel("Servowinkel in °")
    ax2.legend(loc="upper right", fontsize=8)
    ax2.grid(alpha=0.3)

    fig.suptitle("Bionisches Auge: Blickfehler und Servowinkel")
    fig.tight_layout()
    fig.savefig(ziel_png, dpi=150)
    print(f"Plot gespeichert: {ziel_png}")


if __name__ == "__main__":
    pfad = Path(sys.argv[1] if len(sys.argv) > 1 else "messung.csv")
    if not pfad.exists():
        sys.exit(f"{pfad} nicht gefunden. Erst bionisches_auge.py im Tracking-Modus laufen lassen.")
    d = lese_messung(pfad)
    kennwerte(d)
    zeichne(d, pfad.with_suffix(".png"))
