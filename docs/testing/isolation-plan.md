# Plan für isolierte Laufzeittests

## Zweck und Evidenzgrenze

Dieses Dokument beschreibt Gates für einen künftigen M1-Laufzeittest. Es ist ein Plan und kein Nachweis, dass ein isolierter Server oder Spielstand vorhanden ist. Dieser öffentliche Snapshot enthält kein Hostinventar, Prozess-Snapshot, Netzwerkscan oder Firewallprotokoll.

## Voraussetzungen

Ein Live-Test darf erst stattfinden, wenn alle folgenden Punkte im konkreten Testaufbau unabhängig bestätigt wurden:

1. Zielspielversion und passende API-Quellen sind festgehalten.
2. Der Spielstand ist entbehrlich und kein bestehender Benutzerspielstand.
3. Spielstanddaten, Modkonfiguration, Moddata, Backups und verwendete gemeinsame Profildaten sind verstanden und von Benutzerdaten getrennt. Eine Kommandozeilenoption für den Datenpfad allein beweist keine vollständige Isolation.
4. Modquelle und Laufzeitwert von `Server().folder` sind ohne Annahmen identifiziert. Die Bridge darf nur das für diesen Testspielstand verifizierte Moddata-Verzeichnis verwenden.
5. Die Netzwerkreichweite des Servers ist durch bestehende Kontrollen der Testumgebung begrenzt. Betriebssystem- oder Firewall-Einstellungen im Rahmen dieses Plans nicht ändern. Lässt sich die erforderliche Grenze ohne solche Änderung nicht nachweisen, Test abbrechen und Aufbau neu entwerfen.
6. Es gibt eine Wiederherstellungskopie der entbehrlichen Testdaten; die geplante Bereinigung kann nur diese Testdaten betreffen.

Ist eine Bedingung unbekannt, keinen Server für diesen Test starten und keinen Client verbinden.

## M1-No-Action-Smoke-Test

1. Die Projekt-Mod ausschließlich im entbehrlichen Testprofil bereitstellen. Hashes notieren und prüfen, dass keine Benutzerspielstände oder Installationsdateien verändert wurden.
2. Den Testserver erst starten, wenn die Voraussetzungen erfüllt sind. Erwartete Spielversion und Modlade-Nachweis in den eigenen Logs prüfen. Ein Konfigurationseintrag allein belegt kein Modladen.
3. Mit einem autorisierten Ingame-Administrator verbinden, ein gültiges AI-eigenes Testschiff auswählen und das schreibgeschützte Kommando `inspect` ausführen. Schiffs-ID, `Server().folder`, Owner-Prüfung und konfigurierten Scriptpfad prüfen. Dieser Modus muss zurückkehren, bevor ein Attach erfolgt.
4. Den resultierenden Moddata-Pfad mit dem vom Server gemeldeten Ordner abgleichen. Im Testverzeichnis zwei fehlende oder leere Kanaldateien bereitstellen.
5. Zuerst die Lua-Probe initialisieren. Danach `probe_bridge.py --cycles 1` mit unabhängig bestätigter Schiffs-ID und Moddata-Verzeichnis starten. Die Bridge nicht zuerst starten: Sie schreibt HELLO in den Kanal, den die Lua-Initialisierung bei nicht leerem Inhalt ablehnen soll.
6. Testlogs und beide Kanaldateien als Evidenz sichern. Erwartet werden auf Python-Seite HELLO, PROBE Sequenz 1 und ACK Sequenz 1; auf Lua-Seite HELLO_ACK, STATE Sequenz 1 und ACKED Sequenz 1. Die gemeldete Schiffs-ID muss zum ausgewählten Testschiff passen.
7. Bestätigen, dass keine ShipAI-Aktion erfolgt ist. Test nur nach dem freigegebenen Verfahren beenden und ausschließlich seine entbehrlichen Daten sichern oder entfernen.

## Abnahmekriterien

M1 gilt erst als nachgewiesen, wenn die isolierte Umgebung dokumentiert ist, das Modladen belegt wurde, `inspect` erwartete schreibgeschützte Werte liefert, der Ein-Zyklus-Roundtrip erfolgreich endet, beide Kanalprotokolle die erwarteten korrelierten Records enthalten und der Zustand das vorgesehene Testschiff bezeichnet. Ein angenommenes Kommando oder ein Server-Konsolenmarker belegt keine Mod-IPC. M1 enthält keine Schiffssteuerungsaktion.

Der aktuelle source-level `inspect`-Zweig und die Offline-Protokolltests sind kein Laufzeitnachweis. Kommandoerkennung, Callback-Verhalten, `Owner(target)`, Mod-Scriptpfad-Zuordnung, Dateiberechtigungen, Lua-Parsing und echte Avorion-IPC bleiben unbestätigt.

## Spätere Aktionstests

Ein M2-Bewegungstest benötigt nach M1 eine eigene Prüfung und Abnahme. Er muss ein entbehrliches NPC-Schiff, einen serverseitig gewählten begrenzten Wegpunkt, genau eine beaufsichtigte Aktion, serverseitige Validierung und beobachtbaren Positionsfortschritt verwenden. Dispatch oder ein AI-Zustandsfeld allein belegen keine Bewegung. Keine freien LLM-Koordinaten oder Entity-IDs an den Spielserver übergeben.
