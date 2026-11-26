# Stückliste

Preise sind Richtwerte vom November 2026 und können sich ändern. Der Jetson war schon vorhanden und ist nicht eingerechnet.

| Teil | Menge | Preis ca. | Zweck |
|---|---|---|---|
| NVIDIA Jetson Orin Nano Developer Kit | 1 | vorhanden | Bildverarbeitung und Regelung |
| NVMe-SSD M.2 2280, 256 GB | 1 | vorhanden | Systemlaufwerk |
| Logitech C270 (USB, 720p) | 1 | 13,90 € | Kamera |
| PCA9685, 16 Kanäle, 12 Bit (2er-Pack) | 2 | 9,99 € | Servopulse über I²C, ein Modul als Ersatz |
| SG90 mit Metallgetriebe, 180° (3er-Pack) | 3 | 7,49 € | Pan- und Tilt-Achse, ein Servo als Ersatz |
| Steckernetzteil 5 V, 2 A, Hohlstecker 5,5 × 2,1 mm | 1 | 6,99 € | Servostrom |
| DC-Buchse 5,5 × 2,1 mm auf Schraubklemme | 1 | vorhanden | Netzteil an PCA9685 |
| Jumperkabel F-F | 4 | vorhanden | I²C-Verbindung zum Header |
| M3-Schraube ca. 35 mm mit Stoppmutter | 1 | vorhanden | Gelenk der C270 in der Gabel |
| PLA-Filament | | vorhanden | Druckteile |
| **Summe Neukauf** | | **ca. 38 €** | |

## Druckteile

Alle Dateien liegen in [`cad/pan-tilt-c270-v2/`](../cad/pan-tilt-c270-v2/).

| Druckplatte | Teile | Einstellungen |
|---|---|---|
| A: Halterung | Plataforma (Fuß), Tapa (Pan-Gehäuse), Kameraplatte mit C270-Gabel | PLA, 0,2 mm Schicht, 3 Perimeter, 20 bis 30 % Infill, keine Stützen |
| B: Hörner | Spline-Testplatte, Kreuz- und Einarmhörner | PLA, 0,1 mm Schicht, 100 % Infill, keine Stützen |
