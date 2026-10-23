# Plan für isolierte Laufzeittests

## Zweck und Evidenzgrenze

Dieses Dokument beschreibt Gates für einen künftigen M1-Laufzeittest. Es ist ein Plan und kein Nachweis, dass ein isolierter Server oder Spielstand vorhanden ist. Dieser öffentliche Snapshot enthält kein Hostinventar, Prozess-Snapshot, Netzwerkscan oder Firewallprotokoll.

## Letzte Laufzeitbeobachtung

Die Testserverinstanz läuft. Ihr Lauf auf einer separaten Testkopie erreichte `Server startup complete`; ein Client verband sich und lud die Welt. Das Clientlog bestätigt die Registrierung des lokalen Projekt-Mod-Manifests und Server-Advertisement. Es belegt nicht, dass Lua-Scripts geladen oder `initialize` beziehungsweise Command-Handler ausgeführt wurden. Der Server meldete Multiplayer aktiviert und lauschte auf allen IPv4-Adressen; die technische Netzisolation ist nicht abgenommen.

Historische Eingabephase vor dem neuesten Appshot: Return/KP_Enter oeffneten das Chatfeld nicht; der vollstaendige Inspect-Befehl wurde damals nicht uebermittelt. Ein spaeterer Nutzer-Appshot bestaetigt den begrenzten read-only Inspect. Der Attach-Versuch stoppte fail-closed an der leeren Allowlist; siehe Follow-up am Dokumentende.

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
4. Vor jedem Attach den Command-Dispatch-Vertrag prüfen. Der aktuelle Quellkandidat verlangt `/ai_commander_attach_probe attach confirm <ship-id-from-inspect>` und bindet die Bestätigung an das weiterhin ausgewählte Schiff; diese Argumentübergabe ist noch nicht zur Laufzeit bestätigt. Ein akzeptierter Attach lässt die Probe dauerhaft am Entity, wo sie weiterhin einmal pro Sekunde pollt. Daher nur mit einem ausdrücklich dafür vorgesehenen Testziel fortfahren.
5. Den resultierenden Moddata-Pfad mit dem vom Server gemeldeten Ordner abgleichen. Im Testverzeichnis zwei fehlende oder leere Kanaldateien bereitstellen.
6. Zuerst die Lua-Probe initialisieren. Danach `probe_bridge.py --cycles 1` mit unabhängig bestätigter Schiffs-ID und Moddata-Verzeichnis starten. Die Bridge nicht zuerst starten: Sie schreibt HELLO in den Kanal, den die Lua-Initialisierung bei nicht leerem Inhalt ablehnen soll.
7. Testlogs und beide Kanaldateien als Evidenz sichern. Erwartet werden auf Python-Seite HELLO, PROBE Sequenz 1 und ACK Sequenz 1; auf Lua-Seite HELLO_ACK, STATE Sequenz 1 und ACKED Sequenz 1. Die gemeldete Schiffs-ID muss zum ausgewählten Testschiff passen.
8. Bestätigen, dass keine ShipAI-Aktion erfolgt ist. Test nur nach dem freigegebenen Verfahren beenden und ausschließlich seine entbehrlichen Daten sichern oder entfernen.

## Abnahmekriterien

M1 gilt erst als nachgewiesen, wenn die isolierte Umgebung dokumentiert ist, das Modladen belegt wurde, `inspect` erwartete schreibgeschützte Werte liefert, der Ein-Zyklus-Roundtrip erfolgreich endet, beide Kanalprotokolle die erwarteten korrelierten Records enthalten und der Zustand das vorgesehene Testschiff bezeichnet. Ein angenommenes Kommando oder ein Server-Konsolenmarker belegt keine Mod-IPC. M1 enthält keine Schiffssteuerungsaktion.

Offline-Protokolltests sind kein Laufzeitnachweis. Der neueste Nutzer-Appshot belegt für diese Sitzung einen erfolgreichen read-only Inspect mit begrenzten Metadaten und Handler-Ausführung bis zur Inspect-Ausgabe; die Identität der geladenen Quelle bleibt ungeklaert. `probe_script_path` ist ein hart codierter vorgesehener Pfad und kein Beleg für ein angehängtes Script. Dateiberechtigungen, Lua-Parsing und echte Avorion-IPC bleiben unbestätigt.

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
- Der Appshot belegt einen read-only Inspect mit begrenzten Metadaten; weitergehender State-Export, tatsächlicher Attach und IPC-Roundtrip fehlen. **M1 bleibt offen.**

## Follow-up 2026-10-23: UI-Fensterreaktivierung

- Der lesende App-Check lieferte genau ein Avorion-Fenster (App-ID `steam://rungameid/445220`, Titel `Avorion`, Prozess `Avorion.exe`). Nach einer Minimiert-Meldung wurde dieselbe zurückgegebene Fensterreferenz aktiviert und neu geladen.
- Der frische Screenshot/UIA-Zustand zeigte den Vollbild-Ladebildschirm „Leertaste drücken um fortzufahren“ und Fokus auf der Avorion-Fläche. Es wurde keine Taste gesendet. Die Zielreferenz ist reaktivierbar; Tasteneingabe-Annahme und Ursache früherer Fehlschläge sind nicht nachgewiesen.
- Die API-Dokumentation beschreibt `key: 'space'` und `press_key` mit derselben Fensterreferenz als gültig. Ohne Tastendruck ergibt sich daraus kein Laufzeitnachweis. M1 bleibt offen.

## Historischer Follow-up 2026-10-23: Inspect-Ziel-Guard im früheren Appshot

- Der frühere Appshot zeigte zweimal `No valid selected target was found.`; der passende String steht an der `craft.selectedObject`-Guard. Das ist bedingter Laufzeitbeleg für diesen damaligen Zwischenstand, sofern die Quelle geladen war.
- Der neueste Appshot loest diesen Zwischenstand ab: Ein read-only Inspect lieferte begrenzte Metadaten; der Attach-Versuch wurde von der leeren Allowlist fail-closed gestoppt. Es gab keinen Attach oder IPC-Roundtrip.

### Follow-up: Read-only Inspect und Allowlist-Sperre (2026-10-23)

Der neueste Nutzer-Appshot zeigt ein ausgewähltes AI-eigenes Schiff. Der read-only Inspect gelang und gab eine Schiff-ID, den Serverordner der Testinstanz, `AI-owner=true` sowie `probe_script_path=data/scripts/entity/ai_commander_probe.lua` aus; konkrete IDs und lokale Pfade werden hier ausgelassen. Die Ausgabe belegt die begrenzten Inspect-Metadaten für diese Sitzung. `probe_script_path` ist ein hart codierter vorgesehener Pfad und kein Nachweis, dass das Script angehängt wurde. Der Attach-Versuch endete fail-closed mit `No disposable test ship is allowlisted; no attach was requested.`; es wurde nichts angehängt. Es gab keinen weitergehenden State-Export und keinen IPC-Roundtrip. Die lokale Tastenbelegung ordnet `Nearest Enemy` Scancode 21 (R) zu; das belegt nur eine konfigurierte Taste, nicht dass sie gedrückt wurde oder die Auswahl verursachte. **M1 bleibt offen.**

### Follow-up: ausgewählte AI-Fregatte und ID-bestätigter Attach-Kandidat (2026-10-23)

Ein neuerer Appshot zeigt eine ausgewählte AI-Fregatte und einen erfolgreichen read-only Inspect mit `AI-owner=true`; konkrete IDs und lokale Pfade werden nicht veröffentlicht. Der Source-Kandidat verlangt `attach confirm <ship-id-from-inspect>` und vergleicht die angegebene ID mit dem weiterhin ausgewählten Ziel. Das ist nicht im laufenden Server geladen oder ausgeführt; die Argumentübergabe an den Handler bleibt offen. Der frühere leere-Allowlist-Abbruch bleibt historische Evidenz. Eine akzeptierte Probe entfernt sich nicht nach `--cycles 1`: Sie bleibt am Entity und pollt weiter einmal pro Sekunde. Es gab keinen Attach und keinen IPC-Roundtrip.
