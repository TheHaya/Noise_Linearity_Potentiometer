# Firmware Änderung für den Potentiometer-Prüfstand

Du arbeitest an der Firmware eines Hardware nahen Mess und Prüfstands. Setze nur die konkret angefragte Firmware Änderung um. Behandle diese Datei als festen Arbeitsrahmen für jede Firmware Aufgabe in diesem Projekt.

## Projektkontext

Die Firmware läuft auf einem Arduino UNO R4 Minima mit PlatformIO und Arduino Framework.

Die Firmware steuert:
einen Dynamixel Servo,
Relais für Messpfade und Polarität,
Kalibrierabläufe,
Messbewegungen für Rauschen, Linearität und elektrische Grade,
die serielle Kommunikation zur Python GUI.

Die wichtigsten Firmware Dateien liegen in src und include. Besonders relevant sind:
src/main.cpp
src/dxl_servo.cpp
src/calibrate.cpp
src/noise.cpp
src/linearity.cpp
src/elec_deg.cpp
src/relay.cpp
src/side_functions.cpp
include/

Die GUI ist ein getrenntes System in Python. Änderungen an der seriellen Schnittstelle wirken direkt auf die GUI und auf die Messabläufe.

## Harte Regeln

Ändere nur die Firmware, außer die Aufgabe verlangt ausdrücklich auch GUI Änderungen.

Füge keine neuen Bibliotheken oder Frameworks hinzu, außer dies wird ausdrücklich verlangt.

Ändere keine Baudraten, COM Annahmen oder das serielle Nachrichtenformat ohne ausdrückliche Freigabe.

Wenn du eine serielle Nachricht, einen Befehl, eine Antwort oder einen Parameter ändern musst, dann:
1. sage ausdrücklich, dass sich dadurch auch GUI Anpassungen ergeben,
2. nenne die betroffenen Python Dateien,
3. ändere die Schnittstelle nicht stillschweigend.

Wenn du eine Funktion in src änderst, prüfe immer auch die zugehörigen Header in include.

Erhalte sichere Zustände bei Abbruch, Stop und Ende eines Messlaufs. Wenn du an Bewegungs oder Relay Logik arbeitest, achte darauf, dass Relais und Servo nicht in einem unklaren Zustand zurückbleiben.

## Arbeitsweise

Lies vor einer Änderung zuerst die tatsächlich betroffenen Dateien und ihre direkten Abhängigkeiten.

Verstehe zuerst den Ablauf in src/main.cpp und danach das betroffene Modul. Arbeite nicht blind nur in einer einzelnen Funktion.

Suche die Ursache des Problems an der Quelle. Repariere nicht nur das sichtbare Symptom, wenn die eigentliche Ursache an einer zentraleren Stelle liegt.

Behalte den bestehenden Aufbau der Firmware bei. Kleine, gezielte Änderungen sind besser als große Umstrukturierungen, wenn die Aufgabe keinen Umbau verlangt.

Wenn bestehende Namen, Konstanten oder Zustände bereits etabliert sind, nutze diese weiter statt neue Parallelstrukturen einzuführen.

## Technische Schwerpunkte, die du immer mitdenken sollst

1. Serielle Vertragsstabilität.
Die GUI setzt voraus, dass bestimmte Befehle und Antworten unverändert bleiben. Prüfe jede Änderung darauf.

2. Initialisierung.
Achte auf setup, measurements_init und alle Pfade, die vor einem Messlauf Zustand aufbauen.

3. Abbruch und Stop.
Achte auf STOP, CANCEL, ALL_END, all_relays_off, LED Zustände und Servo Endzustände.

4. Bewegungslogik.
Achte auf tick zu degree Umrechnung, erreichbare Zielpositionen, Blockierung, Timeout Verhalten und erreichter Zielzustand.

5. Kalibrierung.
Achte auf Mehrschritt Abläufe, Zwischenzustände, Abbrüche und Sonderfälle wie target_deg_total gleich null.

6. Relay Verhalten.
Achte darauf, dass Relais nur in sinnvollen Zuständen geschaltet werden und die Firmware bei Fehlern oder Abbruch nicht in einem riskanten Zustand endet.

7. Seiteneffekte.
Prüfe globale Variablen, implizite Zustände und Interaktionen mit anderen Messmodi.

## Qualitätsmaßstab

Eine gute Firmware Änderung in diesem Projekt erfüllt alle folgenden Punkte:

Sie löst das eigentliche Problem.
Sie bricht das bestehende serielle Protokoll nicht unbeabsichtigt.
Sie hält Initialisierung, Abbruch und Endzustände konsistent.
Sie bleibt klein und lokal, wenn keine größere Änderung nötig ist.
Sie berücksichtigt die echte Hardware und keine rein theoretische Idealarchitektur.

## Wenn die gewünschte Änderung unklar ist

Wenn die Aufgabe fachlich unklar ist, formuliere zuerst die Annahmen.
Wenn mehrere Lösungen möglich sind, bevorzuge die robusteste mit dem kleinsten Risiko für bestehende Messabläufe.
Wenn eine Änderung zwar lokal einfach wäre, aber das Protokoll oder die GUI berührt, weise ausdrücklich darauf hin.

## Erwartetes Ergebnisformat

Wenn du eine Firmware Aufgabe bearbeitest, liefere am Ende immer:

1. Eine kurze Beschreibung, was geändert wurde.
2. Die betroffenen Firmware Dateien.
3. Mögliche Auswirkungen auf GUI oder Schnittstellen.
4. Welche Verifikation sinnvoll ist.
5. Verbleibende Risiken oder offene Fragen.

## Verifikation, die du immer mitdenken sollst

Prüfe gedanklich mindestens diese Punkte:
Startet die Firmware weiterhin sauber.
Bleiben bestehende Kommandos intakt.
Sind Abbruch und Endzustände korrekt.
Muss ein Header mit angepasst werden.
Kann die GUI die Änderung unverändert weiter benutzen.
Gibt es Sonderfälle mit null Werten, Timeouts, Cancel oder unerwarteter Reihenfolge von Kommandos.

Antworte präzise, technisch und ohne unnötigen Text.