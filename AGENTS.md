# 
Projekt: Potentiometer-Prüfstand (Noise, Linearität, elektrische Grade, Widerstand)

## Architektur

- Firmware: C++ mit PlatformIO, Board: Arduino UNO R4 Minima
  - Quellcode: src/ und include/
  - Abhängigkeiten: Dynamixel2Arduino, elapsedMillis
- GUI: Python 3 mit Tkinter (sv-ttk Theme)
  - Quellcode: GUI/
  - Abhängigkeiten: siehe requirements.txt (pyserial, matplotlib, numpy, pandas, xlsxwriter, Pillow)
- Konfiguration: preset_Teile.json (Presets für verschiedene Potentiometer-Typen)
- Externe Messsoftware: PicoScope (pico_demo.exe in Pico_Demo/)

## Hardware-Setup

- Dynamixel Servo (ID 1) für Drehbewegung
- Relay-Schaltung für Polaritätswechsel und verbinden des relevanten Messequipments um unnötige Innenwiderstände zu reduzieren.
- Keithley Multimeter Modell 2000 (seriell, 19200 Baud)
- Netzteil/PSU OWON P4305 (seriell, 115200 Baud)
- Arduino UNO R4 Minima (seriell, 115200 Baud)
- PicoScope P2206B Oszilloskop

## Serielle Kommunikation

- Drei serielle Verbindungen gleichzeitig (Arduino, PSU und entweder Multimeter oder PicoScope)
- Textbasiertes Protokoll zwischen GUI und Firmware (Befehle wie NOISE_START, STOP; Antworten wie OUTPUT, PICO_START, PLOT_TIME)

## Regeln für den Agent

- Keine neuen Abhängigkeiten hinzufügen ohne Rückfrage
- COM-Ports und Baudraten nicht ändern ohne Rückfrage
- Firmware und GUI sind getrennte Systeme; Änderungen an der Schnittstelle immer auf beiden Seiten prüfen
- Deutsche Benutzeroberfläche beibehalten
- Bei Firmware-Änderungen: immer prüfen, ob Header in include/ aktualisiert werden muss
- Bei GUI-Änderungen: Thread-Safety beachten (GUI-Thread vs. Worker-Threads)
- Schreibe den Text (außer Code) so Credit-Effizient wie möglich.

Codex soll in diesem Repository standardmäßig nur im Ask-Modus arbeiten.

- Keine Dateien direkt ändern.
- Keine Patches anwenden.
- Keine Schreibbefehle ausführen.
- Keine Formatierung, Refactorings oder Fixes automatisch durchführen.
- Stattdessen nur erklären, analysieren und konkrete Vorschläge machen.
- Codeänderungen als Snippets oder Schritt-für-Schritt-Anleitung ausgeben, damit ich sie selbst implementieren kann.
- Wenn eine Änderung sinnvoll wäre, zuerst beschreiben:
  1. welche Datei betroffen ist
  2. welche Stelle geändert werden soll
  3. welcher Code vorgeschlagen wird
