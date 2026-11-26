# Verkabelung

Der Jetson schickt nur Sollwinkel über I²C. Der PCA9685 erzeugt daraus die 50-Hz-Servopulse in Hardware. Die Servos bekommen ihren Strom aus einem eigenen 5-V-Netzteil und nie aus dem Jetson.

```mermaid
flowchart LR
    subgraph Jetson["Jetson Orin Nano, 40-Pin-Header"]
        P1["Pin 1: 3,3 V"]
        P3["Pin 3: SDA (I²C-Bus 7)"]
        P5["Pin 5: SCL (I²C-Bus 7)"]
        P6["Pin 6: GND"]
    end
    subgraph PCA["PCA9685, Adresse 0x40"]
        VCC["VCC (Logik)"]
        SDA["SDA"]
        SCL["SCL"]
        GND1["GND"]
        VP["V+ Schraubklemme"]
        GND2["GND Schraubklemme"]
        K0["Kanal 0"]
        K1["Kanal 1"]
    end
    NT["Netzteil 5 V, 2 A<br/>Hohlstecker 5,5 × 2,1 mm"] --> DC["DC-Buchse auf Schraubklemme"]
    DC -- "+" --> VP
    DC -- "−" --> GND2
    P1 --> VCC
    P3 --> SDA
    P5 --> SCL
    P6 --> GND1
    K0 --> PAN["Pan-Servo (SG90)"]
    K1 --> TILT["Tilt-Servo (SG90)"]
    CAM["Logitech C270"] -- USB --> Jetson
```

## Verbindungen

| Von | Nach | Hinweis |
|---|---|---|
| Jetson Pin 1 (3,3 V) | PCA9685 VCC | Logikspannung. Nie 5 V, weil die I²C-Pull-ups an VCC hängen und der Header nur 3,3 V verträgt. |
| Jetson Pin 3 (SDA) | PCA9685 SDA | I²C-Bus 7 unter JetPack 6 |
| Jetson Pin 5 (SCL) | PCA9685 SCL | |
| Jetson Pin 6 (GND) | PCA9685 GND | gemeinsame Masse |
| Netzteil + | PCA9685 V+ (Schraubklemme) | Servostrom. Den V+-Pin der Stiftleiste frei lassen. |
| Netzteil − | PCA9685 GND (Schraubklemme) | |
| PCA9685 Kanal 0 | Pan-Servo | braunes Kabel auf GND |
| PCA9685 Kanal 1 | Tilt-Servo | braunes Kabel auf GND |
| C270 | Jetson USB | erscheint als `/dev/video0` |

## Prüfen vor dem ersten Einschalten

1. Polarität des Netzteils mit dem Multimeter an V+ und GND des PCA9685 messen. Erwartet werden +5 V.
2. Erst den Jetson einschalten, dann das Servonetzteil.
3. I²C-Bus scannen: `sudo i2cdetect -y -r 7`. Erwartet wird die Adresse `40`.
4. Servos lose testen, ohne Kamera auf dem Halter: `python3 bionisches_auge.py --test`.
