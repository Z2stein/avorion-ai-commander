# Projektstatus

## Evidenzübersicht

- **M0 — Statische Discovery:** Recherche und Testplan liegen vor. Das ist ein Dokumentationsergebnis, kein Laufzeitnachweis.
- **M1 — Nicht nachgewiesen:** Passives Mod-/Bridge-Gerüst und AC|1-Protokollkandidat liegen vor. Das Clientlog bestätigt die Registrierung des lokalen Projekt-Mod-Manifests und Server-Advertisement, aber nicht Lua-Scriptladen, `initialize`, Command-Handler-Ausführung, Lua/Python-IPC-Roundtrip, Zustandsexport oder externe Spielaktion.
- **Offline-Tests:** Das Projekt dokumentiert 22 bestandene Python-Tests mit Fake-Peers und temporären Dateien. Sie führen Avorion nicht aus, parsen kein Lua und validieren keine echte Moddata-IPC.
- **Lua:** Nicht geparst oder ausgeführt.
- **M2 und später:** Geplant; keine Schiffssteuerungsaktion ist nachgewiesen.

## Letzter Laufzeitversuch

Die Testserverinstanz läuft. Ihr späterer Lauf auf einer separaten Testkopie mit Avorion 2.5.13 erreichte `Server startup complete`; der Client verband sich und lud die Spielwelt. Das Clientlog bestätigt Manifest-Registrierung und Server-Advertisement des lokalen Projekt-Mods. Lua-Scriptladen, `initialize` und Command-Handler-Ausführung sind nicht belegt. Der Server meldete Multiplayer aktiviert und lauschte auf allen IPv4-Adressen; technische Netzisolation ist nicht abgenommen. Frühere Starts mit zehn und neun Modconfig-Einträgen endeten mit `include error: module 'generator' not found`; ein anschließender Start mit der wiederhergestellten Zehn-Einträge-Konfiguration war erfolgreich. Die Ursache der früheren Fehler ist nicht bestimmt und wird dem Projekt-Mod nicht zugeschrieben. Server- und Clientstart belegen weder technische Isolation noch M1.

Return/KP_Enter öffneten das Chatfeld nicht; ein Return wurde zunächst einmal gesendet. Nach dem Chat-Eintrag `test` wurde im sichtbaren Chatbereich versucht, `/ai_commander_attach_probe inspect` einzugeben. Im ersten frischen Screenshot war kein Befehlstext sichtbar; ein weiteres Return wurde nicht gesendet. Nach einem Hinweis, dass physisch getippte Buchstaben in der Chatzeile sichtbar seien, wurde der Texteingabeversuch mit `/ai_commander_attach_probe inspect` wiederholt. Auch der frische Screenshot zeigte keinen Befehlstext; danach wurde kein Return gesendet. Die aktuelle Chatprotokollierung zeigt weiterhin nur den Chat-Eintrag `test`, keinen Inspect-Aufruf. Der Nutzer wurde gebeten, die Chatzeile manuell mit dem Befehlstext zu füllen; bis dahin erfolgt kein Inspect. Der Quelltext-Review des read-only `inspect`-Zweigs belegt keine Laufzeit: der Aufruf wurde nicht ausgeführt. Es gab weder Attach noch IPC-Roundtrip, Zustandsexport oder Schiffsaktion. M1 bleibt unbestätigt.

## Hinweise zur M1-Implementierung

Die Bridge akzeptiert ein explizit übergebenes Moddata-Verzeichnis; sie kann nicht selbst feststellen, ob dieses Verzeichnis zu einem isolierten Testspielstand gehört. Die Lua-Probe erwartet bei der Initialisierung fehlende oder leere Kanaldateien. Zuerst die Mod initialisieren, danach die Bridge für einen einzelnen Probe-Zyklus starten. Das Attach-Kommando ist mit leerer fester Test-ID-Allowlist standardmäßig fail-closed. Der `inspect`-Modus soll schreibgeschützten Kontext liefern und den Attach-Zweig umgehen, wurde aber nicht in Avorion ausgeführt.

## Erforderliche Evidenz vor weiteren Laufzeittests

Einen entbehrlichen Spielstand verwenden und die Trennung von Spielstanddaten, Modkonfiguration, Backups und Netzwerkzugriff nachweisen. Zielspielversion, Modladen, Kommandoerkennung, `Server().folder`-Zuordnung und IPC-Dateiberechtigungen in dieser Umgebung bestätigen. Ein erreichter Serverstart und eine geladene Clientwelt ersetzen diese Nachweise nicht.

Dieser öffentliche Status lässt Hostinventare, lokale Konfiguration, Spielstandnamen, Prozesskennungen, Zeitstempel und Netzwerkdiagnosen absichtlich aus. Aus dieser Auslassung keine Schlussfolgerung über einen konkreten Rechner ziehen.
