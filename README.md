# Avorion AI Commander

## Ziel

Einen autonomen, LLM-gestützten Commander für Avorion-NPC-Schiffe untersuchen und entwickeln. Der geplante Ablauf liest Spielzustand, wählt aus begrenzten taktischen Möglichkeiten, validiert Anfragen auf dem Server und prüft das Ergebnis.

Das erste Laufzeitziel ist ein nachweisbarer Proof of Concept: Ein externer Prozess erhält den Zustand eines NPC-Schiffs, sendet eine validierte Anfrage, und der Spielserver bestätigt ein beobachtbares Ergebnis.

## Status

Statische Discovery und ein Offline-Protokollgerüst sind dokumentiert. Das Repository enthält eine passive Avorion-Mod, das versionierte AC|1-Textprotokoll, eine Python-Bridge und eine Offline-Fake-Peer-Testsuite. Die zuletzt dokumentierte Offline-Suite umfasst 22 bestandene Tests; sie verwendet Fake-Peers und temporäre Dateien und führt kein Avorion-Lua aus.

**M1 ist nicht nachgewiesen.** Dieser öffentliche Snapshot belegt keinen Lua-Scriptlauf, Lua/Python-IPC-Roundtrip, exportierten Schiffszustand oder externe Spielaktion. Lua wurde nicht geparst oder ausgeführt. Das Attach-Kommando bleibt standardmäßig fail-closed.

Die Testserverinstanz läuft. Ihr Start auf einer separaten Testkopie mit Avorion 2.5.13 erreichte `Server startup complete`; ein Client meldete sich an und lud die Welt. Das Clientlog bestätigt die Registrierung des lokalen Projekt-Mod-Manifests und dessen Server-Advertisement. Lua-Scriptladen, `initialize` und Command-Handler-Ausführung sind dadurch nicht belegt. Der Server meldete Multiplayer aktiviert und lauschte auf allen IPv4-Adressen; technische Netzisolation ist nicht abgenommen. Frühere Starts mit zehn und neun Modconfig-Einträgen endeten mit `include error: module 'generator' not found`; ein späterer Start mit der wiederhergestellten Zehn-Einträge-Konfiguration war erfolgreich. Die Ursache der früheren Fehler ist offen und wird dem Projekt-Mod nicht zugeschrieben.

Return/KP_Enter öffneten das Chatfeld nicht; ein Return wurde zunächst einmal gesendet. Nach dem Chat-Eintrag `test` wurde im sichtbaren Chatbereich versucht, `/ai_commander_attach_probe inspect` einzugeben. Im ersten frischen Screenshot war kein Befehlstext sichtbar; ein weiteres Return wurde nicht gesendet. Nach einem Hinweis, dass physisch getippte Buchstaben in der Chatzeile sichtbar seien, wurde der Texteingabeversuch mit `/ai_commander_attach_probe inspect` wiederholt. Auch der frische Screenshot zeigte keinen Befehlstext; danach wurde kein Return gesendet. Die Chatprotokollierung zeigt inzwischen `inspect` als vom Spieler gesendeten Text; der Server antwortete `Unknown command: 'inspect'`. Der gewünschte Befehl `/ai_commander_attach_probe inspect` wurde nicht als solcher übermittelt und nicht ausgeführt. Die spätere `/help`-Serverliste zeigt `/ai_commander_attach_probe: Requests the passive AI Commander probe on the selected ship`; sie bestätigt die Laufzeit-Registrierung und Auflistung des Befehls. Das belegt weder Handler-Ausführung noch erfolgreichen `inspect`, Attach, IPC oder M1. Für diesen Schritt wurde kein Return gesendet. Bei sichtbarem Caret in der Chatzeile wurde erneut `sky.type_text('/ai_commander_attach_probe inspect')` aufgerufen; der sofortige Screenshot zeigte weiterhin keinen Befehlstext. Es wurde kein Return gesendet. Die zuvor unklare Teileingabe ist im neuesten Screenshot nicht mehr vorhanden; die Eingabezeile ist leer. Der Nutzer wurde gebeten, die Zeile manuell mit dem vollständigen Befehl zu füllen; bis der Text sichtbar und eindeutig ist, erfolgt kein Inspect. Der read-only `inspect`-Aufruf wurde nicht ausgeführt. Es gab weder Attach noch IPC-Roundtrip, Zustandsexport oder Schiffsaktion. Weitere Laufzeittests erfordern weiterhin einen entbehrlichen Spielstand und nachgewiesene Daten- und Netzwerkisolation.

Hostinventare, lokale Pfade, Serverlogs, Spielstandnamen und Netzwerkdiagnosen sind absichtlich nicht enthalten. Aus ihrem Fehlen lässt sich nichts über einen konkreten Rechner oder Laufzeitstand ableiten.

## Repository-Struktur

- `avorion-mod/`: passiver M1-Mod-Quelltext und fail-closed Attach-Kommando-Kandidat
- `bridge/`: Python-Standardbibliotheks-Bridge und source-only Protokoll-Injektor
- `commander/`: geplante externe Commander-Komponente
- `docs/architecture/`: Architektur und Protokollgrenzen
- `docs/project/`: Entscheidungen, Roadmap und Evidenzstatus
- `docs/research/`: API- und IPC-Recherche
- `docs/testing/`: Offline-Testevidenz und isolierte Testabläufe
- `tests/`: Offline-Tests für Bridge und Injektor

## Sicherheitsprinzipien

- Bestehende Spielstände und Installationsdateien sind keine Test-Fixtures.
- Laufzeittests erfordern einen entbehrlichen Spielstand und nachgewiesene Isolation.
- Betriebssystem- oder Firewall-Einstellungen nur mit ausdrücklicher Freigabe ändern.
- Ein M1-Kommunikationsnachweis belegt weder autonomes Verhalten noch eine erfolgreiche NPC-Aktion.

Siehe [Projektstatus](docs/project/status.md), [Architektur](docs/architecture/commander-design.md) und [Isolationsplan](docs/testing/isolation-plan.md).
