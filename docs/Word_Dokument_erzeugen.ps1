$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$projectRoot = Split-Path -Parent $PSScriptRoot
$outputPath = Join-Path $PSScriptRoot "Bedienungsanleitung_Potentiometer-Pruefstand.docx"
$logoPath = Join-Path $projectRoot "GUI\AMLogo.jpg"

# Word constants
$wdCollapseEnd = 0
$wdPageBreak = 7
$wdAlignLeft = 0
$wdAlignCenter = 1
$wdAlignRight = 2
$wdStyleNormal = -1
$wdStyleHeading1 = -2
$wdStyleHeading2 = -3
$wdStyleHeading3 = -4
$wdStyleTitle = -63
$wdStyleSubtitle = -75
$wdPaperA4 = 7
$wdFormatDocumentDefault = 16
$wdFieldPage = 33
$wdFieldNumPages = 26
$wdBorderBottom = -3
$wdLineStyleSingle = 1

$script:word = $null
$script:doc = $null

function Get-EndRange {
    $range = $script:doc.Content
    $range.Collapse($wdCollapseEnd)
    return $range
}

function Add-Paragraph {
    param(
        [string]$Text = "",
        [int]$Style = $wdStyleNormal,
        [int]$Alignment = $wdAlignLeft,
        [bool]$Bold = $false,
        [bool]$Italic = $false,
        [double]$SpaceBefore = 0,
        [double]$SpaceAfter = 6,
        [string]$Color = "000000"
    )

    $range = Get-EndRange
    $range.Text = $Text
    $range.Style = $Style
    $range.ParagraphFormat.Alignment = $Alignment
    $range.ParagraphFormat.SpaceBefore = $SpaceBefore
    $range.ParagraphFormat.SpaceAfter = $SpaceAfter
    $range.Font.Bold = [int]$Bold
    $range.Font.Italic = [int]$Italic
    $range.Font.Color = [System.Drawing.ColorTranslator]::ToOle(
        [System.Drawing.ColorTranslator]::FromHtml("#$Color")
    )
    $range.InsertParagraphAfter()
}

function Add-Heading {
    param([string]$Text, [ValidateSet(1,2,3)][int]$Level = 1)
    if ($Level -eq 1) {
        if (-not [string]::IsNullOrWhiteSpace($script:doc.Path)) {
            $script:doc.Save()
        }
        Write-Output ("SECTION=" + $Text)
    }
    $style = switch ($Level) {
        1 { $wdStyleHeading1 }
        2 { $wdStyleHeading2 }
        3 { $wdStyleHeading3 }
    }
    Add-Paragraph -Text $Text -Style $style -SpaceBefore 10 -SpaceAfter 5 -Color "1F4E78"
}

function Add-Bullets {
    param([string[]]$Items)
    foreach ($item in $Items) {
        $range = Get-EndRange
        $range.Text = $item
        $range.Style = $wdStyleNormal
        $range.ListFormat.ApplyBulletDefault()
        $range.ParagraphFormat.LeftIndent = $script:word.CentimetersToPoints(0.7)
        $range.ParagraphFormat.FirstLineIndent = $script:word.CentimetersToPoints(-0.35)
        $range.ParagraphFormat.SpaceAfter = 3
        $range.InsertParagraphAfter()
    }
    $end = Get-EndRange
    $end.ListFormat.RemoveNumbers()
}

function Add-Steps {
    param([string[]]$Items)
    $number = 1
    foreach ($item in $Items) {
        Add-Paragraph -Text ("{0}. {1}" -f $number, $item) -SpaceAfter 4
        $number++
    }
}

function Add-Table {
    param(
        [string[]]$Headers,
        [object[][]]$Rows,
        [double[]]$WidthsCm = @()
    )

    $range = Get-EndRange
    $table = $script:doc.Tables.Add($range, $Rows.Count + 1, $Headers.Count)
    $table.AllowAutoFit = $true
    $table.Borders.Enable = 1
    $table.Range.Font.Name = "Aptos"
    $table.Range.Font.Size = 9
    $table.Range.ParagraphFormat.SpaceAfter = 0

    for ($column = 1; $column -le $Headers.Count; $column++) {
        $cell = $table.Cell(1, $column)
        $cell.Range.Text = $Headers[$column - 1]
        $cell.Range.Font.Bold = 1
        $cell.Range.Font.Color = [System.Drawing.ColorTranslator]::ToOle(
            [System.Drawing.Color]::White
        )
        $cell.Shading.BackgroundPatternColor = [System.Drawing.ColorTranslator]::ToOle(
            [System.Drawing.ColorTranslator]::FromHtml("#1F4E78")
        )
    }

    for ($row = 0; $row -lt $Rows.Count; $row++) {
        for ($column = 0; $column -lt $Headers.Count; $column++) {
            $cell = $table.Cell($row + 2, $column + 1)
            $cell.Range.Text = [string]$Rows[$row][$column]
            if (($row % 2) -eq 1) {
                $cell.Shading.BackgroundPatternColor = [System.Drawing.ColorTranslator]::ToOle(
                    [System.Drawing.ColorTranslator]::FromHtml("#D9EAF7")
                )
            }
            if ($WidthsCm.Count -eq $Headers.Count) {
                $cell.Width = $script:word.CentimetersToPoints($WidthsCm[$column])
            }
        }
    }

    $after = Get-EndRange
    $after.InsertParagraphAfter()
    return $table
}

function Add-Callout {
    param(
        [string]$Title,
        [string]$Text,
        [ValidateSet("info", "warning", "danger")][string]$Type = "info"
    )

    $colors = switch ($Type) {
        "info"    { @("D9EAF7", "1F4E78") }
        "warning" { @("FFF2CC", "BF9000") }
        "danger"  { @("F4CCCC", "C00000") }
    }

    $range = Get-EndRange
    $table = $script:doc.Tables.Add($range, 1, 1)
    $table.Borders.Enable = 1
    $table.Borders.OutsideColor = [System.Drawing.ColorTranslator]::ToOle(
        [System.Drawing.ColorTranslator]::FromHtml("#$($colors[1])")
    )
    $table.Cell(1, 1).Shading.BackgroundPatternColor = [System.Drawing.ColorTranslator]::ToOle(
        [System.Drawing.ColorTranslator]::FromHtml("#$($colors[0])")
    )
    $table.Cell(1, 1).Range.Text = "$Title`r$Text"
    $table.Cell(1, 1).Range.Paragraphs.Item(1).Range.Font.Bold = 1
    $table.Cell(1, 1).Range.Font.Name = "Aptos"
    $table.Cell(1, 1).Range.Font.Size = 10
    $table.Cell(1, 1).Range.ParagraphFormat.SpaceAfter = 3
    $after = Get-EndRange
    $after.InsertParagraphAfter()
}

function Add-PageBreak {
    $range = Get-EndRange
    $range.InsertBreak($wdPageBreak)
}

try {
    $script:word = New-Object -ComObject Word.Application
    $script:word.Visible = $false
    $script:word.DisplayAlerts = 0
    if (-not (Test-Path -LiteralPath $outputPath)) {
        throw "Word-Grunddatei fehlt: $outputPath"
    }
    $script:doc = $script:word.Documents.Open($outputPath)
    $script:doc.Content.Text = ""
    Write-Output "INITIAL_OPEN_DONE"

    # Page and document defaults
    $section = $script:doc.Sections.Item(1)
    $section.PageSetup.PaperSize = $wdPaperA4
    $section.PageSetup.TopMargin = $script:word.CentimetersToPoints(2.1)
    $section.PageSetup.BottomMargin = $script:word.CentimetersToPoints(1.8)
    $section.PageSetup.LeftMargin = $script:word.CentimetersToPoints(2.2)
    $section.PageSetup.RightMargin = $script:word.CentimetersToPoints(2.0)
    $section.PageSetup.HeaderDistance = $script:word.CentimetersToPoints(0.8)
    $section.PageSetup.FooterDistance = $script:word.CentimetersToPoints(0.8)

    $normal = $script:doc.Styles.Item($wdStyleNormal)
    $normal.Font.Name = "Aptos"
    $normal.Font.Size = 10.5
    $normal.ParagraphFormat.LineSpacingRule = 0
    $normal.ParagraphFormat.SpaceAfter = 5

    foreach ($styleId in @($wdStyleHeading1, $wdStyleHeading2, $wdStyleHeading3)) {
        $style = $script:doc.Styles.Item($styleId)
        $style.Font.Name = "Aptos Display"
        $style.Font.Color = [System.Drawing.ColorTranslator]::ToOle(
            [System.Drawing.ColorTranslator]::FromHtml("#1F4E78")
        )
        $style.Font.Bold = 1
        $style.ParagraphFormat.KeepWithNext = -1
    }
    $script:doc.Styles.Item($wdStyleHeading1).Font.Size = 17
    $script:doc.Styles.Item($wdStyleHeading2).Font.Size = 13
    $script:doc.Styles.Item($wdStyleHeading3).Font.Size = 11

    # Header and footer
    $header = $section.Headers.Item(1).Range
    $header.Text = "Potentiometer-Prüfstand  |  Bedienungsanleitung"
    $header.Font.Name = "Aptos"
    $header.Font.Size = 8
    $header.Font.Color = [System.Drawing.ColorTranslator]::ToOle(
        [System.Drawing.ColorTranslator]::FromHtml("#666666")
    )
    $header.ParagraphFormat.Alignment = $wdAlignRight
    $header.ParagraphFormat.Borders.Item($wdBorderBottom).LineStyle = $wdLineStyleSingle
    $header.ParagraphFormat.Borders.Item($wdBorderBottom).Color = [System.Drawing.ColorTranslator]::ToOle(
        [System.Drawing.ColorTranslator]::FromHtml("#B4C6E7")
    )

    $footer = $section.Footers.Item(1).Range
    $footer.Text = "Version 1.0  |  Potentiometer-Prüfstand"
    $section.Footers.Item(1).Range.ParagraphFormat.Alignment = $wdAlignCenter
    $section.Footers.Item(1).Range.Font.Name = "Aptos"
    $section.Footers.Item(1).Range.Font.Size = 8

    # Cover page
    Add-Paragraph -Text "" -SpaceAfter 20
    if (Test-Path -LiteralPath $logoPath) {
        $logoRange = Get-EndRange
        $logoRange.ParagraphFormat.Alignment = $wdAlignCenter
        $logo = $script:doc.InlineShapes.AddPicture($logoPath, $false, $true, $logoRange)
        $logo.LockAspectRatio = -1
        $logo.Width = $script:word.CentimetersToPoints(6.5)
        $logoRange.InsertParagraphAfter()
    }
    Add-Paragraph -Text "BEDIENUNGSANLEITUNG" -Style $wdStyleTitle -Alignment $wdAlignCenter -Bold $true -SpaceBefore 26 -SpaceAfter 12 -Color "1F4E78"
    Add-Paragraph -Text "Potentiometer-Prüfstand" -Style $wdStyleSubtitle -Alignment $wdAlignCenter -SpaceAfter 8 -Color "404040"
    Add-Paragraph -Text "Prüfung von Rauschen, Linearität, elektrischem und mechanischem Winkel sowie Widerstand" -Alignment $wdAlignCenter -Italic $true -SpaceAfter 28 -Color "666666"

    Add-Table -Headers @("Dokumentenangabe", "Wert") -Rows @(
        @("Dokumentnummer", "[eintragen]"),
        @("Version", "1.0"),
        @("Stand", "18.09.2026"),
        @("Erstellt von", "[Name eintragen]"),
        @("Geprüft / freigegeben", "[Name und Datum eintragen]"),
        @("Anlage / Standort", "[eintragen]")
    ) -WidthsCm @(5.2, 10.5) | Out-Null

    Add-Callout -Title "DOKUMENTSTATUS" -Text "Arbeitsfassung zur technischen Ergänzung. Vor der endgültigen Freigabe müssen der elektrische Beispielabschnitt, alle mit [eintragen] markierten Angaben und die realen Sicherheitsmaßnahmen geprüft werden." -Type "warning"

    Add-Paragraph -Text "Urheber und Betreiber: [Unternehmen eintragen]" -Alignment $wdAlignCenter -SpaceBefore 22 -Color "666666"
    Add-PageBreak

    # Document control and TOC
    Add-Heading -Text "Dokumentenlenkung" -Level 1
    Add-Table -Headers @("Version", "Datum", "Änderung", "Bearbeiter") -Rows @(
        @("1.0", "18.09.2026", "Erstausgabe der Bedienungsanleitung", "[eintragen]")
    ) -WidthsCm @(2.0, 3.0, 8.2, 3.0) | Out-Null
    Add-Paragraph -Text "Dieses Dokument ist Bestandteil der Prüfvorrichtung. Änderungen an Mechanik, Elektrik, Firmware, GUI, Messgeräten oder Prüfabläufen müssen in dieser Anleitung nachvollziehbar nachgeführt werden. Veraltete Fassungen sind als ungültig zu kennzeichnen." -SpaceAfter 10

    Add-Heading -Text "Inhaltsverzeichnis" -Level 1
    Add-Table -Headers @("Kapitel", "Inhalt") -Rows @(
        @("1", "Zweck und Geltungsbereich"),
        @("2", "Sicherheit"),
        @("3", "Systemübersicht"),
        @("4", "Voraussetzungen und Inbetriebnahme"),
        @("5", "Bedienung der Prüfsoftware"),
        @("6", "Ergebnisse und Export"),
        @("7", "Erweiterter Modus"),
        @("8", "Elektrischer Aufbau – Musterabschnitt"),
        @("9", "Softwarepflege und Firmware-Upload"),
        @("10", "Fehlerbehebung"),
        @("11", "Außerbetriebnahme und Wartung"),
        @("12", "Hinweise zum aktuellen Softwarestand"),
        @("13", "Technische Referenz")
    ) -WidthsCm @(2.2, 14.0) | Out-Null
    Add-PageBreak

    # 1
    Add-Heading -Text "1 Zweck und Geltungsbereich" -Level 1
    Add-Paragraph -Text "Diese Anleitung beschreibt die sichere Inbetriebnahme, Bedienung, Auswertung, Fehlerbehebung und Softwarepflege des Potentiometer-Prüfstands. Sie richtet sich an eingewiesene Bedienpersonen sowie an qualifiziertes Personal für Wartung, Elektrik und Software."
    Add-Paragraph -Text "Die Prüfvorrichtung vermisst Potentiometer automatisiert. Je nach Auswahl werden mechanischer Drehwinkel, elektrischer Drehwinkel, Linearität, Rauschen sowie Anfangs-, End- und Gesamtwiderstand erfasst. Die Windows-GUI koordiniert den Ablauf; ein Arduino UNO R4 Minima steuert Servo und Relaismatrix."
    Add-Callout -Title "Gültigkeitsgrenze" -Text "Diese Anleitung beschreibt den aus dem Projektstand vom 18.09.2026 abgeleiteten Funktionsumfang. Der reale Schaltplan, die Klemmenbelegung und die betrieblichen Sicherheitsvorgaben haben stets Vorrang." -Type "info"

    # 2
    Add-Heading -Text "2 Sicherheit" -Level 1
    Add-Heading -Text "2.1 Bestimmungsgemäße Verwendung" -Level 2
    Add-Paragraph -Text "Die Vorrichtung darf ausschließlich zur Prüfung der dafür freigegebenen Potentiometertypen und innerhalb der hinterlegten Spannungs-, Strom-, Winkel- und Geschwindigkeitsgrenzen verwendet werden. Andere Bauteile oder improvisierte Adapter dürfen nur nach technischer Freigabe eingesetzt werden."

    Add-Heading -Text "2.2 Grundlegende Sicherheitsregeln" -Level 2
    Add-Bullets -Items @(
        "Prüfling nur bei stillgesetzter und spannungsfreier Vorrichtung montieren oder elektrisch anschließen.",
        "Während einer Bewegung nicht in Servo, Kupplung, Welle, Spannmittel oder Prüfling greifen.",
        "Vor jedem Start Befestigung, Kupplung, Leitungen und freie Beweglichkeit kontrollieren.",
        "Den Prüfling vor dem Start möglichst in eine sichere Mittelstellung bringen.",
        "Nur freigegebene Presets verwenden und Teilenummer sowie Prüfauftrag kontrollieren.",
        "Bei ungewöhnlichen Geräuschen, blockierter Mechanik, Geruch oder Erwärmung den Vorgang sofort abbrechen und die Anlage spannungsfrei schalten.",
        "Arbeiten an Netzspannung, Netzteil, Relaismatrix oder Schutzleiter dürfen nur durch entsprechend qualifiziertes Personal erfolgen."
    )
    Add-Callout -Title "WARNUNG – bewegte Mechanik" -Text "Der Servo kann selbstständig und mit wechselnder Drehrichtung anlaufen. Softwareseitiges Abbrechen ersetzt keinen hardwareseitigen Not-Halt oder eine sichere Trennung der Antriebsenergie." -Type "danger"

    Add-Heading -Text "2.3 Verhalten beim Abbruch" -Level 2
    Add-Paragraph -Text "Das Schließen des Fortschrittsfensters setzt ein Stoppsignal. Beim Schließen der Anwendung wird ebenfalls STOP an den Arduino gesendet und der Ausgang des Netzteils ausgeschaltet. Danach ist zu kontrollieren, ob die Mechanik tatsächlich steht und der PSU-Ausgang aus ist. Bei einem Kommunikationsausfall muss die Versorgung hardwareseitig abgeschaltet werden."

    # 3
    Add-Heading -Text "3 Systemübersicht" -Level 1
    Add-Table -Headers @("Komponente", "Aufgabe") -Rows @(
        @("Windows-PC", "Bedienoberfläche, Ablaufsteuerung, PicoScope-Hilfsprogramm und Export"),
        @("Arduino UNO R4 Minima", "Serielles Protokoll, Relais, Taster, LEDs und Servokoordination"),
        @("Dynamixel-Servo, ID 1", "Drehbewegung und Positions-/Stromrückmeldung"),
        @("Keithley 2000", "DC-Spannungs- und Widerstandsmessung"),
        @("OWON P4305", "Elektrische Versorgung des Prüflings"),
        @("PicoScope P2206B", "Erfassung und Bewertung der Rauschsignale"),
        @("Relaismatrix", "Umschaltung der Messpfade, Widerstandsmessung und Polarität"),
        @("Prüfling", "Zu vermessendes Potentiometer")
    ) -WidthsCm @(5.0, 11.2) | Out-Null

    Add-Heading -Text "3.1 Kommunikationsdaten" -Level 2
    Add-Table -Headers @("Gerät", "Schnittstelle", "Einstellung") -Rows @(
        @("Arduino", "USB / seriell", "115200 Baud"),
        @("Keithley 2000", "seriell", "19200 Baud, 8 Datenbits, keine Parität, 1 Stoppbit"),
        @("OWON P4305", "seriell", "115200 Baud"),
        @("Dynamixel", "Serial1", "ID 1, Protokoll 2.0, 1 MBit/s"),
        @("PicoScope", "USB", "Steuerung über pico_demo.exe")
    ) -WidthsCm @(4.0, 4.2, 8.0) | Out-Null

    Add-Paragraph -Text "Im aktuellen Softwarestand sind Arduino COM18, Keithley COM6 und OWON COM7 im Quellcode eingetragen. Diese Werte sind installationsabhängig und vor der endgültigen Übergabe mit dem Geräte-Manager abzugleichen."

    # 4
    Add-Heading -Text "4 Voraussetzungen und Inbetriebnahme" -Level 1
    Add-Heading -Text "4.1 Kontrolle vor dem Einschalten" -Level 2
    Add-Bullets -Items @(
        "Vorrichtung und Schutzabdeckungen ohne erkennbare Beschädigung",
        "Prüfling passend zur gewählten Teilenummer",
        "Prüfling mechanisch fest und fluchtend eingespannt",
        "Elektrische Kontaktierung entsprechend dem freigegebenen Klemmenplan",
        "Servo, Arduino, Messgeräte und PC korrekt verbunden",
        "PicoScope-Messleitung und Masseführung korrekt angeschlossen",
        "Bewegungsbereich frei von Werkzeugen, Leitungen und Körperteilen"
    )

    Add-Heading -Text "4.2 Einschalt- und Startreihenfolge" -Level 2
    Add-Steps -Items @(
        "Prüfling montieren und elektrisch anschließen.",
        "Prüfling in eine sichere Mittelstellung bringen.",
        "Messgeräte, Servo-Versorgung und Arduino einschalten.",
        "USB- und seriellen Verbindungen zum PC kontrollieren.",
        "Keithley auf 19200 Baud und 8N1 einstellen.",
        "Prüfprogramm starten.",
        "Konsolenausgabe auf erfolgreiche Geräteverbindungen prüfen.",
        "Erst anschließend einen Prüfablauf starten."
    )

    Add-Heading -Text "4.3 Statusanzeigen" -Level 2
    Add-Table -Headers @("Anzeige", "Bedeutung im aktuellen Firmwarestand") -Rows @(
        @("Grüne LED", "Dynamixel erreichbar; Vorrichtung bereit beziehungsweise Vorgang beendet"),
        @("Rote LED", "Messsystem wird initialisiert oder Messung ist aktiv"),
        @("Gelbe LED", "Rausch- oder Linearitätsfehler / Fehlerstatus gesetzt"),
        @("LEDs aus", "Servo nicht erreichbar oder noch kein gültiger Status erkannt"),
        @("PC-Signalton", "Erfolg, Fehler oder Abbruch; über die GUI abschaltbar")
    ) -WidthsCm @(4.2, 12.0) | Out-Null

    # 5
    Add-Heading -Text "5 Bedienung der Prüfsoftware" -Level 1
    Add-Heading -Text "5.1 Hauptfenster" -Level 2
    Add-Table -Headers @("Bedienelement", "Funktion") -Rows @(
        @("Teilenummer", "Sucht ein Preset und lädt Sollwerte, Totzonen und Toleranzen"),
        @("Auftragsnummer", "Wird für die Benennung der Ergebnisdateien verwendet"),
        @("Nacharbeit?", "Ordnet eine Linearitätsmessung einer vorhandenen Excel-Tabelle als Untertabelle zu"),
        @("Automatisches Speichern", "Exportiert vorhandene Linearitäts- und Rauschergebnisse nach Messende"),
        @("Signalton an", "Aktiviert die akustische Rückmeldung am PC"),
        @("Erweiterter Modus", "Gibt Parameterfelder und Diagnosefunktionen frei"),
        @("Messen", "Startet alle ausgewählten Prüfungen"),
        @("Position 0", "Fährt den Servo auf die fest programmierte Referenzposition 2050 Ticks")
    ) -WidthsCm @(4.7, 11.5) | Out-Null

    Add-Heading -Text "5.2 Teilenummer auswählen" -Level 2
    Add-Steps -Items @(
        "In das Feld Teilenummer die ersten Ziffern eingeben.",
        "Den passenden Vorschlag mit Maus oder Pfeiltasten auswählen.",
        "Mit Enter bestätigen.",
        "Angezeigten Kommentar sowie Winkel, Spannung, Geschwindigkeit und Totzonen auf Plausibilität prüfen."
    )
    Add-Callout -Title "Wichtig" -Text "Bei einer nicht vorhandenen Teilenummer erscheint 'Bitte eine Teilnummer auswählen'. Eine manuell eingetippte, aber nicht im Preset vorhandene Nummer ist ungültig." -Type "info"

    Add-Heading -Text "5.3 Prüfungen auswählen" -Level 2
    Add-Table -Headers @("Prüfung", "Beschreibung") -Rows @(
        @("Mech. Enden", "Fährt beide Anschläge an, ermittelt den mechanischen Gesamtwinkel und bewertet ihn gegen das Preset"),
        @("Elektr. Winkel", "Bestimmt den elektrisch wirksamen Bereich anhand der Spannungsgrenzen"),
        @("Rauschen", "Führt Bewegungen mit mehreren Geschwindigkeiten aus und wertet die PicoScope-Daten aus"),
        @("Linearität", "Erfasst Messpunkte in beiden Drehrichtungen und berechnet Linearitätsabweichungen"),
        @("Widerstand", "Blendet Anfangs-, End- und Gesamtwiderstand als auswählbare Teilmessungen ein")
    ) -WidthsCm @(4.0, 12.2) | Out-Null

    Add-Paragraph -Text "Die Widerstandsmessung besitzt die Unteroptionen Anfangs-, End- und Gesamtwiderstand. Im aktuellen Softwarestand kann Widerstand nicht allein gestartet werden; zusätzlich muss mindestens eine der Hauptprüfungen ausgewählt sein."
    Add-Paragraph -Text "Die mechanische Initialisierung und Referenzfahrt wird bei jedem Messauftrag ausgeführt, auch wenn 'Mech. Enden' nicht als sichtbares Ergebnis ausgewählt wurde. Der Prüfling bewegt sich daher bei jeder Messung in Richtung seiner Messgrenzen."

    Add-Heading -Text "5.4 Standard-Prüfablauf" -Level 2
    Add-Steps -Items @(
        "Gültige Teilenummer auswählen.",
        "Auftragsnummer eintragen.",
        "Gewünschte Prüfungen markieren.",
        "Prüfling, Kupplung, Kontaktierung und freien Bewegungsraum kontrollieren.",
        "Messen drücken oder den externen Starttaster betätigen.",
        "Fortschrittsfenster beobachten und die Mechanik nicht berühren.",
        "Nach Abschluss Winkel-, Widerstands-, Kreis- und Statusanzeigen kontrollieren.",
        "Ergebnisdateien prüfen und dem Prüfauftrag zuordnen."
    )

    Add-Heading -Text "5.5 Reihenfolge kombinierter Prüfungen" -Level 2
    Add-Paragraph -Text "Die Software führt zunächst die mechanische Referenzierung und gegebenenfalls Widerstandsmessungen aus. Anschließend folgt die Rauschprüfung. Elektrischer Winkel und Linearität werden danach ausgeführt. Sind elektrischer Winkel und Linearität gemeinsam gewählt, übernimmt der Linearitätsablauf beide Auswertungen. Erkennt die Rauschprüfung einen Fehler und sind nachfolgende Prüfungen gewählt, werden diese abgebrochen."

    Add-Heading -Text "5.6 Messung abbrechen" -Level 2
    Add-Paragraph -Text "Zum Abbrechen das Fortschrittsfenster schließen. Die Software sendet STOP an den Arduino, beendet einen laufenden PicoScope-Prozess und schaltet den PSU-Ausgang aus. Anschließend wird 'Vorgang wurde abgebrochen' angezeigt. Die Escape-Taste im Hauptfenster beendet die gesamte Anwendung; sie ist nicht als regulärer Einzelmessungs-Abbruch vorgesehen."

    # 6
    Add-Heading -Text "6 Ergebnisse und Export" -Level 1
    Add-Heading -Text "6.1 Anzeige" -Level 2
    Add-Table -Headers @("Darstellung", "Bedeutung") -Rows @(
        @("Grün / In Ordnung", "Ergebnis liegt innerhalb der programmierten Toleranzen"),
        @("Rot / Fehler", "Mindestens ein Ergebnis liegt außerhalb der Toleranz oder Rauschen wurde erkannt"),
        @("Bereit", "Prüfung wurde nicht ausgeführt, abgebrochen oder noch nicht bewertet"),
        @("Rote Kreisabschnitte", "Winkelbereiche, in denen Rauschereignisse erkannt wurden"),
        @("Markierte Ringsegmente", "Im Preset hinterlegte Totzonen beziehungsweise Messbereiche")
    ) -WidthsCm @(4.3, 11.9) | Out-Null

    Add-Heading -Text "6.2 Automatischer und manueller Export" -Level 2
    Add-Paragraph -Text "Bei aktivem automatischem Speichern wird ein vorhandenes Linearitätsergebnis nach Excel und ein vorhandenes Rauschergebnis als PDF gespeichert. Alternativ stehen die Schaltflächen 'Linearität speichern' und 'Rauschkurve speichern' zur Verfügung."
    Add-Table -Headers @("Ergebnis", "Dateiname") -Rows @(
        @("Linearität", "RMTest-<Auftragsnummer>.xlsx"),
        @("Rauschkurve", "Rauschkurve-RMTest-<Auftragsnummer>.pdf")
    ) -WidthsCm @(4.3, 11.9) | Out-Null
    Add-Paragraph -Text "Die Dateien werden im aktuellen Arbeitsverzeichnis der Anwendung abgelegt. Der Excel-Export verwendet Microsoft Excel über xlwings. Bei bereits vorhandener Datei wird für eine normale Prüfung ein neues nummeriertes Tabellenblatt angelegt."

    Add-Heading -Text "6.3 Nacharbeit" -Level 2
    Add-Paragraph -Text "Nach Aktivierung von 'Nacharbeit?' ist die Nummer eines bereits vorhandenen normalen Tabellenblatts einzugeben. Für die Basistabelle 3 entstehen beispielsweise die Blätter 3-1, 3-2 und so weiter. Die Excel-Datei und die angegebene Basistabelle müssen bereits existieren. Die Nacharbeitsnummer beeinflusst im aktuellen Stand nur den Excel-Export, nicht den Namen der Rausch-PDF."

    # 7
    Add-Heading -Text "7 Erweiterter Modus" -Level 1
    Add-Callout -Title "WARNUNG" -Text "Der erweiterte Modus umgeht die Schreibsperre der Presetwerte und ermöglicht direkte Servobewegungen. Er ist ausschließlich für Einrichtung, Diagnose und qualifiziertes Fachpersonal vorgesehen." -Type "danger"
    Add-Table -Headers @("Funktion", "Wirkung und Bedienhinweis") -Rows @(
        @("Sollspannung", "Bearbeitbarer Arbeitswert. Eine Änderung ist im aktuellen Softwarestand kein vollständiger Ersatz aller presetabhängigen PSU-Spannungen."),
        @("Gesamtwinkel", "Erwarteter mechanischer Drehbereich; ein zu großer Wert kann die Mechanik überlasten."),
        @("Max. Geschw.", "Maximale Drehgeschwindigkeit in U/min."),
        @("Totzone 1–3", "Grenzen für Kurzschlussstrecken und Mittelanzapfungsbereiche; werden im Ring dargestellt."),
        @("Curr Position", "Liest die absolute Dynamixel-Position und zeigt sie in Ticks an."),
        @("Go To", "Fährt auf die eingegebene absolute Tickposition; nur ganze, vorher geprüfte Werte verwenden."),
        @("Position 0", "Fährt auf den fest programmierten Wert 2050 Ticks. Die aktuelle Position wird nicht als neue Null gespeichert."),
        @("Relais switch", "Wechselt nacheinander zwischen Initial-, Polaritäts- und Gesamtwiderstands-Relaismodus."),
        @("Tester", "Öffnet den Keithley-Port und führt 100 Identifikationsabfragen aus; Ergebnis nur in der Konsole.")
    ) -WidthsCm @(4.0, 12.2) | Out-Null
    Add-Paragraph -Text "Relais switch und Tester sind Diagnosefunktionen. Sie dürfen nicht während einer Messung verwendet werden. Vor manuellen Positionsfahrten ist anhand der aktuellen Tickposition und der realen Mechanik sicherzustellen, dass kein Anschlag überfahren wird."

    # 8 Electrical example
    Add-Heading -Text "8 Elektrischer Aufbau – Musterabschnitt" -Level 1
    Add-Callout -Title "BEISPIELTEXT – VOR FREIGABE ERSETZEN UND PRÜFEN" -Text "Die folgenden Aussagen enthalten bewusst Platzhalter. Sie sind keine freigegebene Verdrahtungsanweisung. Ergänzung und Prüfung müssen anhand des realen Schaltplans durch eine qualifizierte Elektrofachkraft erfolgen." -Type "danger"

    Add-Heading -Text "8.1 Energieversorgung – Beispieltext" -Level 2
    Add-Paragraph -Text "Die Prüfvorrichtung wird über [Netzanschluss und Nennspannung eintragen] versorgt. Der Hauptschalter [Bezeichnung/Position eintragen] trennt [Umfang der Trennung eintragen] von der Energieversorgung. Die Absicherung erfolgt über [Sicherungstyp und Bemessungsstrom eintragen]. Schutzleiter und Gehäusepotentialausgleich sind gemäß Schaltplan [Zeichnungsnummer eintragen] ausgeführt."
    Add-Paragraph -Text "Der Dynamixel-Servo erhält [Versorgungsspannung und maximale Stromaufnahme eintragen] aus [Netzteil/Versorgungszweig eintragen]. Arduino und Relaisbaugruppe werden über [Versorgung eintragen] gespeist. Vor Arbeiten an der Verdrahtung sind sämtliche Einspeisungen abzuschalten, gegen Wiedereinschalten zu sichern und auf Spannungsfreiheit zu prüfen."

    Add-Heading -Text "8.2 Signal- und Messpfad – Beispieltext" -Level 2
    Add-Paragraph -Text "Der Prüfling wird an den Klemmen [Klemmenbezeichnungen eintragen] angeschlossen. Die Anschlüsse für Bahnanfang, Schleifer, Bahnende und gegebenenfalls Mittelanzapfung sind entsprechend Tabelle 8-1 zuzuordnen. Die Relaismatrix verbindet den Prüfling abhängig von der Prüfart mit Netzteil, Keithley oder PicoScope. Nicht benötigte Messgeräte werden vom Messpfad getrennt, um zusätzliche Innenwiderstände und Messfehler zu vermeiden."
    Add-Table -Headers @("Prüflingsanschluss", "Klemme", "Funktion / Leitung", "Farbe") -Rows @(
        @("Bahnanfang", "[eintragen]", "[eintragen]", "[eintragen]"),
        @("Schleifer", "[eintragen]", "[eintragen]", "[eintragen]"),
        @("Bahnende", "[eintragen]", "[eintragen]", "[eintragen]"),
        @("Mittelanzapfung", "[eintragen]", "[falls vorhanden]", "[eintragen]"),
        @("Schirm / Gehäuse", "[eintragen]", "[eintragen]", "[eintragen]")
    ) -WidthsCm @(3.3, 3.0, 6.6, 3.0) | Out-Null

    Add-Heading -Text "8.3 Relaismatrix – Beispieltext" -Level 2
    Add-Paragraph -Text "Die Relaisausgänge werden vom Arduino aktiv-low angesteuert. Ein LOW-Pegel zieht das jeweilige Relais an, ein HIGH-Pegel schaltet es ab. Die logische Relaisbezeichnung muss vor Freigabe mit der realen Relaisplatine und dem Stromlaufplan abgeglichen werden."
    Add-Table -Headers @("Relaisbezeichnung", "Arduino-Pin", "Reale Kontakte / Funktion") -Rows @(
        @("Relais 1", "D3", "[eintragen]"),
        @("Relais 2", "D4", "[eintragen]"),
        @("Relais 3", "D5", "[eintragen]"),
        @("Relais 4", "D6", "[eintragen]"),
        @("Relais 5", "D7", "[eintragen]"),
        @("Relais 6", "D8", "[eintragen]"),
        @("Relais 7 AB", "D9", "[eintragen]"),
        @("Relais 8 AB", "D10", "[eintragen]"),
        @("Relais 10 AB", "D11", "[eintragen]"),
        @("Relais 11 AB", "D12", "[eintragen]"),
        @("Relais 9 AB", "D13", "[eintragen]"),
        @("Relais 9 CD", "D21", "[eintragen]"),
        @("Relais 9 EF", "D22", "[eintragen]"),
        @("Relais 9 GH", "D20", "[eintragen]")
    ) -WidthsCm @(4.0, 3.0, 9.2) | Out-Null

    Add-Heading -Text "8.4 Einzufügende Schaltungsunterlagen" -Level 2
    Add-Bullets -Items @(
        "Stromlaufplan mit Zeichnungsnummer und Revisionsstand",
        "Klemmenplan des Prüflings und der externen Messgeräte",
        "Versorgungs- und Sicherungskonzept",
        "Relaiskontaktplan mit Ruhe- und Arbeitsstellung",
        "Masse-, Potentialausgleichs- und Schirmungskonzept",
        "Fotoübersicht mit beschrifteten Anschlüssen",
        "Angaben zu Not-Halt, Hauptschalter und sicherer Energietrennung"
    )
    Add-Paragraph -Text "[ABBILDUNG 8-1: Gesamtstromlaufplan hier einfügen]" -Alignment $wdAlignCenter -Italic $true -SpaceBefore 16 -SpaceAfter 16 -Color "C00000"
    Add-Paragraph -Text "[ABBILDUNG 8-2: Klemmen- und Anschlussübersicht hier einfügen]" -Alignment $wdAlignCenter -Italic $true -SpaceBefore 16 -SpaceAfter 16 -Color "C00000"

    # 9
    Add-Heading -Text "9 Softwarepflege und Firmware-Upload" -Level 1
    Add-Heading -Text "9.1 Voraussetzungen" -Level 2
    Add-Bullets -Items @(
        "Visual Studio Code mit PlatformIO",
        "USB-Verbindung zum Arduino UNO R4 Minima",
        "Projektverzeichnis mit src, include und platformio.ini",
        "Geschlossene Prüfsoftware und geschlossener serieller Monitor",
        "Sicherung beziehungsweise Versionsverwaltung des funktionierenden Stands"
    )

    Add-Heading -Text "9.2 Firmware bauen und übertragen" -Level 2
    Add-Steps -Items @(
        "Prüfprogramm schließen, damit der Arduino-COM-Port freigegeben ist.",
        "Projekt in Visual Studio Code öffnen.",
        "Änderungen in src durchführen und bei geänderten Schnittstellen die Header in include aktualisieren.",
        "PlatformIO-Terminal im Projektverzeichnis öffnen.",
        "Firmware mit 'pio run -e uno_r4_minima' bauen.",
        "Buildfehler vollständig beheben; keine fehlerhafte Firmware übertragen.",
        "Firmware mit 'pio run -e uno_r4_minima -t upload' hochladen.",
        "Arduino neu starten und anschließend die GUI öffnen.",
        "Kommunikation, Relais-Grundzustand, Stop-Funktion und Bewegungsrichtung ohne wertvollen Prüfling testen.",
        "Erst danach einen vollständigen Referenzprüflauf durchführen und dokumentieren."
    )
    Add-Callout -Title "Schnittstellenänderungen" -Text "Werden Befehle, Antworten, Baudraten oder Abläufe des seriellen Protokolls geändert, müssen Firmware und GUI gemeinsam geprüft und angepasst werden. COM-Ports und Baudraten nicht ohne dokumentierte Freigabe ändern." -Type "warning"

    Add-Heading -Text "9.3 GUI aus dem Quellcode starten" -Level 2
    Add-Paragraph -Text "Die Python-Abhängigkeiten sind in requirements.txt aufgeführt. Nach Einrichtung der freigegebenen Python-Umgebung wird die Anwendung aus dem Projektverzeichnis mit 'py GUI\\app.py' gestartet. Für den Excel-Export müssen Microsoft Excel und xlwings funktionsfähig sein."

    Add-Heading -Text "9.4 Relevante Projektdateien" -Level 2
    Add-Table -Headers @("Pfad", "Bedeutung") -Rows @(
        @("src/", "Implementierung der Arduino-Firmware"),
        @("include/", "Header und gemeinsame Firmware-Schnittstellen"),
        @("GUI/app.py", "Hauptfenster und Ablaufkoordination"),
        @("GUI/*_workflow.py", "Einzelne Messabläufe"),
        @("GUI/serial_client.py", "COM-Ports, Baudraten und Messgerätekommunikation"),
        @("GUI/preset_Teile.json", "Bauteilparameter und Toleranzen"),
        @("GUI/pico_runner.py", "Start und Auswertung des PicoScope-Hilfsprogramms"),
        @("platformio.ini", "Board- und Bibliothekskonfiguration")
    ) -WidthsCm @(5.2, 11.0) | Out-Null

    # 10
    Add-Heading -Text "10 Fehlerbehebung" -Level 1
    Add-Table -Headers @("Störung", "Mögliche Ursache", "Maßnahme") -Rows @(
        @("GUI startet nicht", "Python-Paket oder Ressourcendatei fehlt", "Anwendung aus der Konsole starten; Fehlermeldung prüfen; requirements.txt kontrollieren"),
        @("Mikrocontroller kein Port", "Falscher COM-Port, USB getrennt oder Port belegt", "Geräte-Manager prüfen; GUI und serielle Monitore schließen; USB neu verbinden"),
        @("Keithley antwortet nicht", "Port oder Schnittstelleneinstellung falsch", "COM-Port sowie 19200 Baud und 8N1 prüfen; anderes Programm vom Port trennen"),
        @("Netzteil reagiert nicht", "Port falsch oder Gerät nicht im Fernsteuerbetrieb", "COM-Port und 115200 Baud prüfen; PSU-Ausgang manuell ausschalten"),
        @("Servo bewegt sich nicht", "Versorgung, ID oder Busverbindung fehlerhaft", "Servo-Versorgung, ID 1, Datenleitung und Dynamixel-Ping prüfen"),
        @("Keine gültige Teilenummer", "Preset fehlt oder Eingabe nicht bestätigt", "Passenden Vorschlag auswählen; preset_Teile.json prüfen"),
        @("Bitte eine Messung ankreuzen", "Keine Hauptprüfung gewählt", "Mech. Enden, elektr. Winkel, Rauschen oder Linearität auswählen"),
        @("Abbruch am Anschlag", "Prüfling ungünstig positioniert oder Mechanik blockiert", "Spannungsfrei schalten; Mechanik prüfen; Prüfling sicher zur Mitte positionieren"),
        @("PicoScope startet nicht", "USB, EXE oder DLL fehlt", "PicoScope-Verbindung sowie pico_demo.exe, ps2000a.dll und picoipp.dll prüfen"),
        @("Keine Excel-Datei", "Excel/xlwings nicht verfügbar oder Daten fehlen", "Excel-Installation, Auftragsnummer und Konsolenausgabe prüfen"),
        @("Nacharbeit nicht gespeichert", "Datei oder Basistabelle fehlt", "Vorhandene RMTest-Datei und eingegebene Blattnummer prüfen"),
        @("Rauschfehler", "Kontakt-, Schirmungs-, Prüflings- oder Mechanikproblem", "PDF auswerten; Leitungen, Masseführung, Schleifer und Kupplung prüfen"),
        @("Messung bleibt stehen", "Kommunikationsverlust oder externer Prozess hängt", "Abbrechen; PSU-Ausgang prüfen; Anwendung neu starten; Konsolenprotokoll sichern"),
        @("Nach Upload keine Verbindung", "COM-Port geändert oder Firmware startet nicht", "Board neu verbinden; Port prüfen; Build/Upload wiederholen; serielle Ausgabe kontrollieren")
    ) -WidthsCm @(3.8, 5.7, 6.7) | Out-Null

    Add-Heading -Text "10.1 Informationen für die Störungsmeldung" -Level 2
    Add-Bullets -Items @(
        "Datum, Uhrzeit, Bedienperson und Auftragsnummer",
        "Teilenummer und ausgewählte Prüfungen",
        "letzte sichtbare Fortschrittsmeldung",
        "LED-Zustand und Verhalten der Mechanik",
        "vollständige Konsolenausgabe beziehungsweise Foto davon",
        "erzeugte PDF-/Excel-Dateien",
        "durchgeführte Änderungen an Firmware, GUI, Preset oder Verdrahtung"
    )

    # 11
    Add-Heading -Text "11 Außerbetriebnahme und Wartung" -Level 1
    Add-Heading -Text "11.1 Reguläres Ausschalten" -Level 2
    Add-Steps -Items @(
        "Laufende Messung beenden und Stillstand abwarten.",
        "Kontrollieren, dass der Ausgang des OWON-Netzteils ausgeschaltet ist.",
        "Prüfprogramm schließen.",
        "Prüfling nur im spannungsfreien Zustand entfernen.",
        "Messgeräte, Servo-Versorgung und Anlage gemäß betrieblicher Abschaltreihenfolge ausschalten."
    )

    Add-Heading -Text "11.2 Regelmäßige Kontrollen" -Level 2
    Add-Bullets -Items @(
        "Kupplung, Halterung und Spannmittel auf Spiel und Beschädigung prüfen",
        "Messleitungen, Stecker und Zugentlastungen kontrollieren",
        "Relaiskontakte und Klemmen auf Erwärmung oder Verschleiß prüfen",
        "Messgeräte gemäß betrieblichem Kalibrierplan überwachen",
        "Referenzprüfling in festgelegten Intervallen messen und Ergebnisse vergleichen",
        "Softwareversion, Presetstand und Dokumentversion gemeinsam archivieren"
    )

    # 12
    Add-Heading -Text "12 Hinweise zum aktuellen Softwarestand" -Level 1
    Add-Paragraph -Text "Die folgenden Punkte sind vor der endgültigen Anlagenfreigabe technisch zu bewerten und entweder zu korrigieren oder als freigegebene Einschränkung zu dokumentieren:"
    Add-Bullets -Items @(
        "Eine reine Widerstandsprüfung lässt sich ohne zusätzliche Hauptprüfung nicht starten.",
        "Die editierbare Sollspannung des erweiterten Modus überschreibt nicht alle intern gespeicherten, presetabhängigen PSU-Spannungen.",
        "Der Presetwert soll_spannung_widerstand wird im gegenwärtigen Messaufruf nicht als eigene PSU-Spannung verwendet.",
        "Das Ergebnis einer alleinigen elektrischen Winkelprüfung wird im Hauptfenster nicht in die Ergebniszeile übernommen.",
        "Das vorgesehene GUI-Fenster 'Schleifer zu nah am Anschlag' wird im aktuellen Ablauf nicht gesetzt.",
        "Die COM-Ports sind fest in GUI/serial_client.py hinterlegt; COM_PORTS.json wird nicht ausgewertet.",
        "Position 0 bedeutet Fahrt auf Tick 2050 und keine Nullung der aktuellen Position.",
        "Die Tester-Schaltfläche ist ein Keithley-Kommunikationstest und keine reguläre Prüffunktion."
    )

    # 13
    Add-Heading -Text "13 Technische Referenz" -Level 1
    Add-Heading -Text "13.1 Arduino-Pinbelegung" -Level 2
    Add-Table -Headers @("Pin", "Funktion", "Hinweis") -Rows @(
        @("D2", "Dynamixel-Richtung", "Kommunikationsrichtung des Halbduplex-Busses"),
        @("D3–D13", "Relaisausgänge", "Aktiv-low"),
        @("D20–D22", "weitere Relaisausgänge", "Aktiv-low"),
        @("D14", "Summer", "Im aktuellen Firmwarestand nur als Ausgang initialisiert"),
        @("D16", "grüne LED", "Bereit / Servo erreichbar"),
        @("D17", "gelbe LED", "Fehlerergebnis"),
        @("D18", "rote LED", "Initialisierung / Messbetrieb"),
        @("D19", "Starttaster", "INPUT_PULLUP; Taster schaltet gegen Masse")
    ) -WidthsCm @(2.7, 5.0, 8.5) | Out-Null

    Add-Heading -Text "13.2 Abnahmecheckliste vor Dokumentfreigabe" -Level 2
    Add-Table -Headers @("Prüfpunkt", "Status", "Datum / Zeichen") -Rows @(
        @("Schaltplan und Revisionsstand eingefügt", "☐", ""),
        @("Klemmenbelegung am realen Aufbau geprüft", "☐", ""),
        @("Versorgung, Sicherungen und Schutzleiter dokumentiert", "☐", ""),
        @("COM-Ports am Übergaberechner bestätigt", "☐", ""),
        @("Alle Presets fachlich geprüft", "☐", ""),
        @("Abbruch und hardwareseitige Energietrennung geprüft", "☐", ""),
        @("Referenzmessung erfolgreich durchgeführt", "☐", ""),
        @("Export und Ablageort geprüft", "☐", ""),
        @("Bedienpersonal unterwiesen", "☐", ""),
        @("Dokument fachlich freigegeben", "☐", "")
    ) -WidthsCm @(10.0, 2.0, 4.2) | Out-Null

    Add-Heading -Text "13.3 Freigabe" -Level 2
    Add-Table -Headers @("Rolle", "Name", "Datum", "Unterschrift") -Rows @(
        @("Erstellt", "", "", ""),
        @("Technisch geprüft", "", "", ""),
        @("Elektrisch geprüft", "", "", ""),
        @("Freigegeben", "", "", "")
    ) -WidthsCm @(4.0, 4.5, 3.0, 4.7) | Out-Null

    Add-Paragraph -Text "Ende des Dokuments" -Alignment $wdAlignCenter -Italic $true -SpaceBefore 20 -Color "777777"

    Write-Output "SAVE_BEGIN"
    $script:doc.Save()
    Write-Output "SAVE_DONE"
    $wordCount = $script:doc.Words.Count
    $script:doc.Close($false)
    $script:word.Quit()

    Write-Output "DOCX=$outputPath"
    Write-Output "WORDS=$wordCount"
}
finally {
    if ($null -ne $script:doc) {
        try { $script:doc.Close($false) } catch {}
        try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($script:doc) } catch {}
    }
    if ($null -ne $script:word) {
        try { $script:word.Quit() } catch {}
        try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($script:word) } catch {}
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

# Word occasionally discards header/footer range text during heavy COM
# automation. Writing the existing Open XML parts directly is deterministic
# and also permits dynamic PAGE and NUMPAGES fields without forcing Word to
# repaginate while saving.
if (Test-Path -LiteralPath $outputPath) {
    $headerXml = @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p>
    <w:pPr>
      <w:jc w:val="right"/>
      <w:pBdr><w:bottom w:val="single" w:sz="4" w:space="2" w:color="B4C6E7"/></w:pBdr>
    </w:pPr>
    <w:r>
      <w:rPr><w:rFonts w:ascii="Aptos" w:hAnsi="Aptos"/><w:color w:val="666666"/><w:sz w:val="16"/></w:rPr>
      <w:t>Potentiometer-Prüfstand  |  Bedienungsanleitung</w:t>
    </w:r>
  </w:p>
</w:hdr>
'@

    $footerXml = @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p>
    <w:pPr><w:jc w:val="center"/></w:pPr>
    <w:r>
      <w:rPr><w:rFonts w:ascii="Aptos" w:hAnsi="Aptos"/><w:color w:val="666666"/><w:sz w:val="16"/></w:rPr>
      <w:t xml:space="preserve">Version 1.0  |  Seite </w:t>
    </w:r>
    <w:fldSimple w:instr=" PAGE "><w:r><w:rPr><w:rFonts w:ascii="Aptos" w:hAnsi="Aptos"/><w:sz w:val="16"/></w:rPr><w:t>1</w:t></w:r></w:fldSimple>
    <w:r><w:rPr><w:rFonts w:ascii="Aptos" w:hAnsi="Aptos"/><w:color w:val="666666"/><w:sz w:val="16"/></w:rPr><w:t xml:space="preserve"> von </w:t></w:r>
    <w:fldSimple w:instr=" NUMPAGES "><w:r><w:rPr><w:rFonts w:ascii="Aptos" w:hAnsi="Aptos"/><w:sz w:val="16"/></w:rPr><w:t>11</w:t></w:r></w:fldSimple>
  </w:p>
</w:ftr>
'@

    $archive = [System.IO.Compression.ZipFile]::Open(
        $outputPath,
        [System.IO.Compression.ZipArchiveMode]::Update
    )
    try {
        $parts = @()
        foreach ($index in 1..3) {
            $parts += @{ Name = "word/header$index.xml"; Content = $headerXml }
            $parts += @{ Name = "word/footer$index.xml"; Content = $footerXml }
        }
        foreach ($part in $parts) {
            $existing = $archive.GetEntry($part.Name)
            if ($null -ne $existing) {
                $existing.Delete()
            }
            $entry = $archive.CreateEntry($part.Name)
            $stream = $entry.Open()
            $writer = New-Object System.IO.StreamWriter(
                $stream,
                [System.Text.UTF8Encoding]::new($false)
            )
            try {
                $writer.Write($part.Content)
            }
            finally {
                $writer.Dispose()
            }
        }
    }
    finally {
        $archive.Dispose()
    }
    Write-Output "HEADER_FOOTER_DONE"

    # Replace the fallback Open XML field representation with native Word
    # PAGE and NUMPAGES fields. The document already has a path at this point,
    # so this incremental save does not trigger the earlier SaveAs issue.
    $footerWord = New-Object -ComObject Word.Application
    $footerWord.Visible = $false
    $footerWord.DisplayAlerts = 0
    $footerDoc = $null
    try {
        $footerDoc = $footerWord.Documents.Open($outputPath, $false, $false)
        foreach ($type in 1..3) {
            $footerRange = $footerDoc.Sections.Item(1).Footers.Item($type).Range
            $footerRange.Text = "Version 1.0  |  Seite "
            $insertRange = $footerRange.Duplicate
            $insertRange.End = $insertRange.End - 1
            $insertRange.Collapse($wdCollapseEnd)
            $footerDoc.Fields.Add($insertRange, $wdFieldPage) | Out-Null

            $footerRange = $footerDoc.Sections.Item(1).Footers.Item($type).Range
            $insertRange = $footerRange.Duplicate
            $insertRange.End = $insertRange.End - 1
            $insertRange.Collapse($wdCollapseEnd)
            $insertRange.InsertAfter(" von ")
            $insertRange.Collapse($wdCollapseEnd)
            $footerDoc.Fields.Add($insertRange, $wdFieldNumPages) | Out-Null

            $footerRange.ParagraphFormat.Alignment = $wdAlignCenter
            $footerRange.Font.Name = "Aptos"
            $footerRange.Font.Size = 8
        }
        $footerDoc.Save()
        $footerDoc.Close($false)
        $footerWord.Quit()
        Write-Output "PAGE_FIELDS_DONE"
    }
    finally {
        if ($null -ne $footerDoc) {
            try { $footerDoc.Close($false) } catch {}
            try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($footerDoc) } catch {}
        }
        if ($null -ne $footerWord) {
            try { $footerWord.Quit() } catch {}
            try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($footerWord) } catch {}
        }
        [GC]::Collect()
        [GC]::WaitForPendingFinalizers()
    }
}
