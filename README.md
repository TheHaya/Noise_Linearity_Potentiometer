# Potentiometer Prüfstand für Rauschen, Linearität, elektrische Grade und Widerstand

Dieses Projekt ist ein Prüfstand zur automatisierten Vermessung von Potentiometern. Die Codebase besteht aus einer Mikrocontroller Firmware und einer Windows GUI. Zusammen steuern beide den Messablauf, bewegen einen Dynamixel Servo, schalten Relais, lesen Messwerte aus und exportieren Ergebnisse.

Das Projekt ist auf reale Hardware ausgelegt. Es geht nicht nur um Softwarelogik, sondern auch um Bewegung, Zeitverhalten, Messketten und externe Geräte. Genau deshalb ist der Aufbau in diesem Repository zweigeteilt.

## 1. Ziel des Projekts

Der Prüfstand soll verschiedene Eigenschaften eines Potentiometers erfassen und bewerten. Dazu gehören:

Rauschprüfung
Linearitätsprüfung
Bestimmung elektrischer Grade
Bestimmung mechanischer Enden
Widerstandsbezogene Messungen

Die GUI lädt dazu passende Presets, startet den Ablauf und sammelt Ergebnisse. Die Firmware setzt die Bewegungen und Messschritte auf dem Mikrocontroller um.

## 2. Systemüberblick

### Firmware

Die Firmware ist in C++ geschrieben und wird mit PlatformIO für ein Arduino UNO R4 Minima gebaut.

Die Firmware übernimmt:
Servo Initialisierung und Bewegung
Kalibrierlogik
Relaissteuerung
Messmodus Logik
Kommunikation mit der GUI über die serielle Schnittstelle

Wichtige Firmware Dateien:
src/main.cpp
src/dxl_servo.cpp
src/calibrate.cpp
src/noise.cpp
src/linearity.cpp
src/elec_deg.cpp
src/relay.cpp
src/side_functions.cpp
include/

### GUI

Die GUI ist in Python mit Tkinter umgesetzt. Sie verwendet sv_ttk für das Erscheinungsbild und koordiniert alle Messabläufe.

Die GUI übernimmt:
Eingaben und Presets
Start und Stop der Messungen
Verbindung zu Arduino, Multimeter und Netzteil
Start des PicoScope Hilfsprogramms
Zusammenführung und Export der Messergebnisse

Wichtige GUI Dateien:
GUI/app.py
GUI/serial_client.py
GUI/noise_workflow.py
GUI/linear_workflow.py
GUI/elec_deg_workflow.py
GUI/mech_ends_workflow.py
GUI/pico_runner.py
GUI/export.py
GUI/side_functions.py

### Konfiguration

Preset Daten liegen in preset_Teile.json.
Die Build Konfiguration der Firmware liegt in platformio.ini.
Die PyInstaller Konfiguration der GUI liegt in app.spec.

## 3. Hardware

Das Projekt arbeitet mit folgender Hardware:

Arduino UNO R4 Minima
Dynamixel Servo mit ID 1
Relaisschaltung für Umschaltung und Polaritätswechsel
Keithley Multimeter Modell 2000
OWON P4305 Netzteil
PicoScope P2206B
Prüfling, also das zu vermessende Potentiometer

## 4. Software und Abhängigkeiten

### Firmware

Für die Firmware wird PlatformIO benötigt.
Das Board ist in platformio.ini als uno_r4_minima konfiguriert.
Verwendete Bibliotheken sind:
Dynamixel2Arduino
elapsedMillis

### GUI

Die GUI benötigt Python 3 und die Pakete aus requirements.txt:
Pillow
sv-ttk
pyserial
matplotlib
numpy
pandas
xlsxwriter

In der aktuellen Codebasis wird für bestimmte Excel Funktionen außerdem xlwings importiert. Falls der Excel Export beim Start oder Lauf mit einem Importfehler stoppt, fehlt diese Abhängigkeit lokal noch.

## 5. Repository Struktur

Die wichtigsten Ordner und Dateien:

src
Firmware Implementierung

include
Header und Schnittstellen der Firmware

GUI
Python GUI, Workflows, serielle Kommunikation, Pico Anbindung und Export

preset_Teile.json
Presets für Potentiometer Typen und Toleranzen

platformio.ini
PlatformIO Konfiguration für das Board und die Firmware Abhängigkeiten

app.spec
PyInstaller Konfiguration für die GUI Anwendung

build
Build Artefakte der gepackten Anwendung

Pico_Demo
Ablage für Pico Hilfsdateien im Projektaufbau

## 6. Installation und erster Start

### 6.1 Firmware vorbereiten

Projekt in VS Code mit PlatformIO öffnen.

Firmware Abhängigkeiten werden über PlatformIO aufgelöst.

Firmware auf das Board laden, zum Beispiel mit:

~~~text
pio run -t upload