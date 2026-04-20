# Codebase Review für den Potentiometer-Prüfstand

Du führst ein technisches Codebase Review für ein gemischtes Messsystem durch. Ziel ist keine allgemeine Zusammenfassung und keine Stilbewertung, sondern eine belastbare Analyse der wichtigsten technischen Risiken, Wartungsprobleme, Architekturgrenzen und Fehlerquellen.

## Projektkontext

Die Codebase besteht aus zwei eng gekoppelten Teilen.

Teil 1 ist eine Firmware in C++ mit PlatformIO für ein Arduino UNO R4 Minima. Die Firmware steuert einen Dynamixel Servo, Relais, Kalibrierungsabläufe und mehrere Messmodi. Die Firmware liegt hauptsächlich in src und include.

Teil 2 ist eine Windows Desktop Anwendung in Python mit Tkinter. Die GUI lädt Presets, steuert Messabläufe, spricht seriell mit mehreren Geräten, startet PicoScope als externen Prozess und exportiert Ergebnisse nach PDF und Excel. Die GUI liegt im Ordner GUI.

Die Codebase ist kein Webprojekt. Sie arbeitet mit echter Hardware, Timing, serieller Kommunikation, Motorbewegung, Messwerten und externer Messsoftware. Bitte bewerte sie als Hardware nahes Steuer und Prüfprojekt und nicht mit Maßstäben, die nur für typische CRUD Anwendungen sinnvoll sind.

## Projektaufbau

Berücksichtige besonders diese Bereiche:

Firmware:
src/main.cpp
src/dxl_servo.cpp
src/calibrate.cpp
src/noise.cpp
src/linearity.cpp
src/elec_deg.cpp
src/relay.cpp
src/side_functions.cpp
include/

GUI:
GUI/app.py
GUI/serial_client.py
GUI/noise_workflow.py
GUI/linear_workflow.py
GUI/elec_deg_workflow.py
GUI/mech_ends_workflow.py
GUI/pico_runner.py
GUI/export.py
GUI/side_functions.py

Konfiguration und Build:
platformio.ini
preset_Teile.json
app.spec

## Wichtige fachliche und technische Randbedingungen

Die Firmware und die GUI sind getrennte Systeme, aber sie hängen über ein textbasiertes Protokoll direkt zusammen.

Die GUI arbeitet aktuell mit mehreren seriellen Verbindungen. In der bestehenden Codebasis sind feste COM Ports und feste Baudraten hinterlegt.

Die PicoScope Anbindung läuft über einen externen Prozess und nicht über eine normale Python Bibliothek.

Presets werden aus einer JSON Datei geladen und enthalten Sollwerte, Deadzones, Toleranzen und Polarity Informationen.

Die Firmware kennt Befehle wie INIT_GO, NOISE_GO, NOISE_START, LINEAR_GO, LINEAR_START, ELEC_DEG_GO, ELEC_DEG_START, STOP, ZERO, GOTO, WHERE und ALL_END. Außerdem werden Parameter über Präfixe wie SETV, SETW, SETS, REL_SW und dead11 bis dead32 gesetzt.

Bitte nimm diese Randbedingungen ernst und schlage keine rein theoretischen Verbesserungen vor, die die reale Hardware Kopplung ignorieren.

## Was geprüft werden soll

Prüfe die Codebase gezielt auf diese Punkte:

1. Architektur und Verantwortlichkeiten.
Prüfe, ob die Trennung zwischen Firmware, GUI, Workflow Logik, Messlogik und Gerätekommunikation klar ist oder ob Verantwortlichkeiten vermischt sind.

2. Schnittstelle zwischen GUI und Firmware.
Prüfe, ob das textbasierte Protokoll robust genug ist, ob Zustände sauber gehandhabt werden und ob Befehle, Antworten und Fehlerfälle konsistent sind.

3. Serielle Kommunikation und Geräteanbindung.
Prüfe, ob die Behandlung von Arduino, Multimeter und Netzteil stabil genug ist, ob harte Port Annahmen, Timeouts, Buffer Handling und Fehlerfälle sauber gelöst sind.

4. Timing, Synchronisation und Threading.
Prüfe, ob Worker Threads, GUI Thread, Stop Events, Polling Schleifen, Blocking Calls und externe Prozesse sauber zusammenspielen oder ob Race Conditions und Hänger wahrscheinlich sind.

5. Messabläufe und Datenintegrität.
Prüfe, ob Messwerte, Zeitreihen, Winkelberechnungen, Pico Daten und Exportdaten konsistent verarbeitet werden oder ob stille Inkonsistenzen möglich sind.

6. Kalibrierung und Bewegungslogik.
Prüfe, ob die Servo, Kalibrier und Relay Logik verständlich, wartbar und fehlertolerant aufgebaut ist. Achte besonders auf Abbruchfälle, Initialisierung und sichere Endzustände.

7. Preset und Eingabevalidierung.
Prüfe, ob preset_Teile.json und Nutzereingaben ausreichend validiert werden oder ob ungültige oder unvollständige Werte zu schwer erkennbaren Fehlern führen können.

8. Wartbarkeit und Änderbarkeit.
Prüfe, welche Bereiche bei zukünftigen Änderungen besonders riskant sind. Achte auf globale Zustände, implizite Kopplung, doppelte Logik und schlecht isolierte Hardware Annahmen.

9. Testbarkeit und Beobachtbarkeit.
Prüfe, wie gut sich Fehler eingrenzen lassen. Achte auf Logging, Fehlermeldungen, Debug Ausgaben, fehlende Verifikation und Stellen, die nur schwer reproduzierbar wirken.

10. Build, Packaging und Betrieb.
Prüfe, ob Python Abhängigkeiten, Exportpfade, Pico Integration, PyInstaller und Projektstruktur betriebssicher wirken oder ob es wahrscheinliche Laufzeitprobleme gibt.

## Was nicht im Fokus stehen soll

Bitte konzentriere dich nicht auf:
kleine Stilfragen,
Formatierungsfragen,
rein subjektive Namensdiskussionen,
mikroskopische Optimierungen ohne praktischen Nutzen.

Wenn es keine belastbare technische Auswirkung gibt, ist es kein Review Finding.

## Erwartetes Ausgabeformat

Gib das Ergebnis in dieser Form aus.

1. Kurzer Architekturabriss.
Maximal 10 Sätze. Nur damit der Gesamtrahmen klar ist.

2. Findings nach Schweregrad.
Ordne alle Findings in Hoch, Mittel und Niedrig.

3. Für jedes Finding liefere:
einen kurzen Titel,
die betroffenen Dateien oder Bereiche,
die konkrete Beobachtung,
warum das problematisch ist,
welche Auswirkung das im realen Betrieb haben kann,
welche Maßnahme die beste erste Reaktion wäre.

4. Priorisierte Maßnahmenliste.
Nenne danach die 5 wichtigsten nächsten Schritte in sinnvoller Reihenfolge.

5. Offene Fragen.
Liste Annahmen oder Punkte auf, die ohne Hardware oder weitere Informationen nicht sicher bewertet werden können.

## Zusätzliche Arbeitsweise

Stütze jede Aussage auf konkrete Stellen in der Codebase.
Wenn etwas nur wahrscheinlich ist, kennzeichne es als Annahme.
Wenn ein Bereich solide wirkt, darfst du das kurz erwähnen.
Wenn keine schwerwiegenden Findings vorliegen, sage das ausdrücklich.
Antworte fachlich, direkt und ohne Fülltext.