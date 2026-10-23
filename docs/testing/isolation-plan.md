# Plan für isolierte Laufzeittests

## Zweck und Evidenzgrenze

Dieses Dokument beschreibt Gates für einen künftigen M1-Laufzeittest. Es ist ein Plan und kein Nachweis, dass ein isolierter Server oder Spielstand vorhanden ist. Dieser öffentliche Snapshot enthält kein Hostinventar, Prozess-Snapshot, Netzwerkscan oder Firewallprotokoll.

## Letzte Laufzeitbeobachtung

Die Testserverinstanz läuft. Ihr Lauf auf einer separaten Testkopie erreichte `Server startup complete`; ein Client verband sich und lud die Welt. Das Clientlog bestätigt die Registrierung des lokalen Projekt-Mod-Manifests und Server-Advertisement. Es belegt nicht, dass Lua-Scripts geladen oder `initialize` beziehungsweise Command-Handler ausgeführt wurden. Der Server meldete Multiplayer aktiviert und lauschte auf allen IPv4-Adressen; die technische Netzisolation ist nicht abgenommen.

Return/KP_Enter öffneten das Chatfeld nicht. Ein Return wurde zunächst einmal gesendet; das Clientlog meldete danach einen Notruf/Mayday und Sektorereignisse. Nach dem Chat-Eintrag `test` wurde im sichtbaren Chatbereich versucht, `/ai_commander_attach_probe inspect` einzugeben. Im ersten frischen Screenshot war kein Befehlstext sichtbar; ein weiteres Return wurde nicht gesendet. Nach einem Hinweis, dass physisch getippte Buchstaben in der Chatzeile sichtbar seien, wurde der Texteingabeversuch mit `/ai_commander_attach_probe inspect` wiederholt. Auch der frische Screenshot zeigte keinen Befehlstext; danach wurde kein Return gesendet. Die Chatprotokollierung zeigt inzwischen `inspect` als vom Spieler gesendeten Text; der Server antwortete `Unknown command: 'inspect'`. Der gewünschte Befehl `/ai_commander_attach_probe inspect` wurde nicht als solcher übermittelt und nicht ausgeführt. Die spätere `/help`-Serverliste zeigt `/ai_commander_attach_probe: Requests the passive AI Commander probe on the selected ship`; sie bestätigt die Laufzeit-Registrierung und Auflistung des Befehls. Das belegt weder Handler-Ausführung noch erfolgreichen `inspect`, Attach, IPC oder M1. Für diesen Schritt wurde kein Return gesendet. Bei sichtbarem Caret in der Chatzeile wurde erneut `sky.type_text('/ai_commander_attach_probe inspect')` aufgerufen; der sofortige Screenshot zeigte weiterhin keinen Befehlstext. Es wurde kein Return gesendet. Die zuvor unklare Teileingabe ist im neuesten Screenshot nicht mehr vorhanden; die Eingabezeile ist leer. Der Nutzer wurde gebeten, die Zeile manuell mit dem vollständigen Befehl zu füllen; bis der Text sichtbar und eindeutig ist, erfolgt kein Inspect. Der read-only `inspect`-Aufruf wurde nicht ausgeführt. Es gab weder Attach noch IPC-Roundtrip, Zustandsexport oder Schiffsaktion; M1 bleibt unbestätigt.

## Voraussetzungen

Ein Live-Test darf erst stattfinden, wenn alle folgenden Punkte im konkreten Testaufbau unabhängig bestätigt wurden:

1. Zielspielversion und passende API-Quellen sind festgehalten.
2. Der Spielstand ist entbehrlich und kein bestehender Benutzerspielstand.
3. Spielstanddaten, Modkonfiguration, Moddata, Backups und verwendete gemeinsame Profildaten sind verstanden und von Benutzerdaten getrennt. Eine Kommandozeilenoption für den Datenpfad allein beweist keine vollständige Isolation.
4. Modquelle und Laufzeitwert von `Server().folder` sind ohne Annahmen identifiziert. Die Bridge darf nur das für diesen Testspielstand verifizierte Moddata-Verzeichnis verwenden.
5. Die Netzwerkreichweite des Servers ist durch bestehende Kontrollen der Testumgebung begrenzt. Betriebssystem- oder Firewall-Einstellungen im Rahmen dieses Plans nicht ändern. Lässt sich die erforderliche Grenze ohne solche Änderung nicht nachweisen, Test abbrechen und Aufbau neu entwerfen.
6. Es gibt eine Wiederherstellungskopie der entbehrlichen Testdaten; die geplante Bereinigung kann nur diese Testdaten betreffen.

Ist eine Bedingung unbekannt, keinen weiteren Live-Test beginnen und keinen Spielbefehl ausführen. Die oben dokumentierte Sitzung hebt die Gates nicht auf.

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

Der aktuelle source-level `inspect`-Zweig und die Offline-Protokolltests sind kein Laufzeitnachweis. Die `/help`-Liste bestätigt die Laufzeit-Registrierung und Auflistung des Kommandos; Callback-Verhalten, tatsächliche Handler-Ausführung, `Owner(target)`, Mod-Scriptpfad-Zuordnung, Dateiberechtigungen, Lua-Parsing und echte Avorion-IPC bleiben unbestätigt.

## Spätere Aktionstests

Ein M2-Bewegungstest benötigt nach M1 eine eigene Prüfung und Abnahme. Er muss ein entbehrliches NPC-Schiff, einen serverseitig gewählten begrenzten Wegpunkt, genau eine beaufsichtigte Aktion, serverseitige Validierung und beobachtbaren Positionsfortschritt verwenden. Dispatch oder ein AI-Zustandsfeld allein belegen keine Bewegung. Keine freien LLM-Koordinaten oder Entity-IDs an den Spielserver übergeben.

## Aktualisierung: Command-Kontext und Offline-Verifikation

- **GETESTET, nur offline:** Die vorhandene Python-Suite bestand erneut mit 22 Tests und Exitcode 0. Sie verwendet temporäre Dateien, Fake-Peers, Mock-Kanäle und eine Fake-Uhr; das belegt keine Lua-Laufzeit oder echte Avorion-IPC.
- **DOKUMENTIERT:** Konsolen-/RCON-Aufrufe an `CommandFunctions.execute` erhalten `playerIndex == nil`. Der aktuelle Inspect-Handler verlangt Ingame-Spieler- und Zielkontext; `commands.txt` kann diesen nicht bereitstellen. Die `/help`-Liste belegt nur Befehlsregistrierung und Auflistung.
- **API-Kandidat, nicht getestet:** Ein separater read-only Konsolenmodus könnte eine Entity-ID über `Sector():getEntity(rawId)` prüfen. Ob `Sector()` im globalen Command-Kontext mit `playerIndex == nil` verfügbar ist, bleibt unbestätigt. Die dokumentierte Entity-Auflistung hat keine eingebaute Obergrenze und ist nicht implementiert.
- Für Command-Scripts ist kein dokumentierter Hot-Reload bekannt. Der Server wurde nicht für diese Prüfung geändert oder neu gestartet.
- Die letzte lesende UI-Prüfung zeigte eine leere Chatzeile. Der vollständige Inspect-Aufruf, Attach und IPC-Roundtrip wurden nicht ausgeführt; M1 bleibt offen.

## Aktualisierung 2026-10-23: Computer-Use-/Vollbild-Befund

- Der lesende Inventar-Check fand genau ein Avorion-Fenster (`Avorion`, `steam://rungameid/445220`, Prozess `Avorion.exe`); der Screenshot zeigte den Ladebildschirm mit Space-Hinweis.
- Zwei gezielt an dieses Fenster gerichtete Space-Eingaben führten zu keinem dauerhaft verifizierten Bildschirmwechsel. Die Zielfenster-Auswahl ist bestätigt, die Annahme der Eingabe durch Avorion nicht. UIA fokussierte die Avorion-Fläche, nicht ein Chatfeld. Es wurde kein weiterer Tastendruck ausgelöst.
- Computer-Use/Windows/Vollbild/Game-Input ist eine mögliche, nicht bewiesene Ursache. Offizielle OpenAI-Seiten ergaben keinen passenden Vollbild-Spiel-Workaround oder bestätigten Avorion-spezifischen Fehler. Die [Windows-App-Berichte](https://community.openai.com/t/computer-use-plugin-stopped-working/1397316/2) und [Initialisierungsberichte](https://community.openai.com/t/windows-computer-use-fails-at-initialization-with-eperm-after-repair-reset-and-reinstall/1389280) sind anekdotisch, keine bestätigte Fehlerursache.
- Es wurden kein Inspect, Attach oder IPC-Roundtrip ausgeführt. **M1 bleibt offen.**
