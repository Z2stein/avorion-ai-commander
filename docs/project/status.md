# Projektstatus

## Evidenzübersicht

- **M0 — Statische Discovery:** Recherche und Testplan liegen vor. Das ist ein Dokumentationsergebnis, kein Laufzeitnachweis.
- **M1 - Nicht nachgewiesen:** Passives Mod-/Bridge-Geruest und AC|1-Protokollkandidat liegen vor. Serverstart, Manifest-Registrierung und Server-Advertisement belegen kein Lua-Scriptladen oder `initialize`. Ein neuerer Nutzer-Appshot zeigt eine ausgewählte AI-Fregatte; der read-only Inspect meldet `AI-owner=true`. Der frühere Attach-Versuch stoppte an der damals leeren Allowlist; es gab keinen Attach. Der aktuelle Quellkandidat verlangt `attach confirm <ship-id-from-inspect>` und vergleicht die ID mit dem weiterhin ausgewählten Ziel. Die genaue Argumentübergabe an den Handler ist nicht bestätigt, und die Änderung ist nicht im laufenden Server geladen. Die Probe würde nach einem Ein-Zyklus-Bridge-Lauf am Entity bleiben und weiter sekündlich pollen. Es gab keinen Attach, breiteren State-Export, IPC-Roundtrip oder externe Spielaktion.
- **Offline-Tests:** Das Projekt dokumentiert 22 bestandene Python-Tests mit Fake-Peers und temporären Dateien. Sie führen Avorion nicht aus, parsen kein Lua und validieren keine echte Moddata-IPC.
- **Lua:** Nicht geparst oder ausgeführt.
- **M2 und später:** Geplant; keine Schiffssteuerungsaktion ist nachgewiesen.

## Letzter Laufzeitversuch

Die Testserverinstanz läuft. Ihr späterer Lauf auf einer separaten Testkopie mit Avorion 2.5.13 erreichte `Server startup complete`; der Client verband sich und lud die Spielwelt. Das Clientlog bestätigt Manifest-Registrierung und Server-Advertisement des lokalen Projekt-Mods. Server- und Clientstart allein belegen Lua-Scriptladen oder `initialize` nicht. Der spätere Appshot belegt erfolgreichen read-only Inspect und Handler-Ausführung bis zur Inspect-Ausgabe; die geladene Quellidentitaet bleibt offen. Der Server meldete Multiplayer aktiviert und lauschte auf allen IPv4-Adressen; technische Netzisolation ist nicht abgenommen. Frühere Starts mit zehn und neun Modconfig-Einträgen endeten mit `include error: module 'generator' not found`; ein anschließender Start mit der wiederhergestellten Zehn-Einträge-Konfiguration war erfolgreich. Die Ursache der früheren Fehler ist nicht bestimmt und wird dem Projekt-Mod nicht zugeschrieben. Server- und Clientstart belegen weder technische Isolation noch M1.

Fruehere Chat-Eingabeversuche uebermittelten den vollstaendigen Inspect-Befehl nicht. Der spaetere Nutzer-Appshot bestaetigt den read-only Inspect mit begrenzten Metadaten; der Attach-Versuch stoppte fail-closed an der leeren Allowlist. Details zu den frueheren Eingaben stehen weiter unten als Chronologie; der aktuelle Evidenzstand steht im Follow-up am Dokumentende.

## Hinweise zur M1-Implementierung

Die Bridge akzeptiert ein explizit übergebenes Moddata-Verzeichnis; sie kann nicht selbst feststellen, ob dieses Verzeichnis zu einem isolierten Testspielstand gehört. Die Lua-Probe erwartet bei der Initialisierung fehlende oder leere Kanaldateien. Zuerst die Mod initialisieren, danach die Bridge für einen einzelnen Probe-Zyklus starten. Der aktuelle Quellkandidat verlangt nach `inspect` eine explizite ID-Bestätigung für das weiterhin ausgewählte AI-Schiff. Der frühere Attach-Versuch wurde noch durch die leere Allowlist abgewiesen; es erfolgten kein Attach, breiterer State-Export oder IPC-Roundtrip. Die Argumentübergabe des neuen Befehls ist nicht bestätigt.

## Erforderliche Evidenz vor weiteren Laufzeittests

Einen entbehrlichen Spielstand verwenden und die Trennung von Spielstanddaten, Modkonfiguration, Backups und Netzwerkzugriff nachweisen. Zielspielversion und Modladen bleiben zu bestaetigen. Ein erfolgreicher read-only Handler-Aufruf und die aktuelle `Server().folder`-Ausgabe sind für diese Sitzung belegt; die Identität der geladenen Quelle bleibt offen. Das Mapping des hart codierten `probe_script_path` zu einem angehängten Script ist nicht belegt. IPC-Dateiberechtigungen und ein echter Roundtrip muessen noch bestätigt werden. Ein erreichter Serverstart und eine geladene Clientwelt ersetzen diese Nachweise nicht.

Dieser öffentliche Status lässt Hostinventare, lokale Konfiguration, Spielstandnamen, Prozesskennungen, Zeitstempel und Netzwerkdiagnosen absichtlich aus. Aus dieser Auslassung keine Schlussfolgerung über einen konkreten Rechner ziehen.

## Aktualisierung 2026-10-23

- Die Offline-Suite wurde erneut mit Python 3.14.5 ausgeführt: 22/22 Tests bestanden, Exitcode 0. Sie verwendet Fake-Peers, temporäre Dateien, Mock-Kanäle und eine Fake-Uhr; sie belegt keine Lua-Laufzeit oder echte Avorion-IPC.
- Laut installierter API-Dokumentation erhält ein Konsolen-/RCON-Command `playerIndex == nil`. Der bestehende read-only Inspect-Handler benötigt Ingame-Spieler- und Zielkontext; `commands.txt` kann diesen Kontext nicht bereitstellen.
- Eine separate read-only Konsolenabfrage per Entity-ID ist als API-Kandidat dokumentiert. Ob `Sector()` im globalen Command-Kontext verfügbar ist, bleibt unbestätigt. Die dokumentierte Sektor-Auflistung liefert alle Treffer ohne eingebaute Obergrenze und ist nicht implementiert.
- Die API-Dokumentation beschreibt keinen Hot-Reload für Command-Scripts. Der laufende Server wurde nicht für diese Prüfung verändert oder neu gestartet.
- Eine erneute lesende Spielansicht zeigte eine leere Chatzeile. Der volle Inspect-Aufruf, Attach und IPC-Roundtrip wurden nicht ausgeführt; M1 bleibt offen.

## Aktualisierung 2026-10-23: Computer-Use-/Vollbild-Befund

- Ein lesender Fensterinventar-Check fand genau ein Avorion-Fenster (`Avorion`, `steam://rungameid/445220`, Prozess `Avorion.exe`). Der Screenshot zeigte den Ladebildschirm mit Space-Hinweis.
- Zwei gezielt an dieses Fenster gerichtete Space-Eingaben führten zu keinem dauerhaft verifizierten Bildschirmwechsel. Die Zielfenster-Auswahl ist bestätigt; ob Avorion die Eingabe annahm, ist nicht bestätigt. UIA-Fokus lag auf der Avorion-Fläche, nicht auf einem Chatfeld. Es wurde kein weiterer Tastendruck ausgelöst.
- Computer-Use/Windows/Vollbild/Game-Input bleibt eine mögliche, unbewiesene Ursache. Offizielle OpenAI-Seiten ergaben keinen passenden Vollbild-Spiel-Workaround und keinen bestätigten Avorion-spezifischen Fehler. [Community-Berichte zu Windows-App-Erkennung/-Steuerung](https://community.openai.com/t/computer-use-plugin-stopped-working/1397316/2) und [zu einem Initialisierungsfehler vor der App-Erkennung](https://community.openai.com/t/windows-computer-use-fails-at-initialization-with-eperm-after-repair-reset-and-reinstall/1389280) sind anekdotische Nutzerberichte, keine bestätigte OpenAI-Fehlerursache.
- Inspect, Attach und IPC-Roundtrip wurden nicht ausgeführt. **M1 bleibt offen.**

## Historischer Follow-up 2026-10-23: Inspect-Ziel-Guard im früheren Appshot

- Ein früherer Nutzer-Appshot zeigte zweimal `No valid selected target was found.`; derselbe Wortlaut steht an der Guard für `craft.selectedObject`. Das ist bedingter Laufzeitbeleg, dass der Handler im früheren Zwischenstand bis zu dieser Guard ausgeführt wurde, sofern die Quelle geladen war.
- Der neueste Nutzer-Appshot supersedes diesen Zustand: Er zeigt einen erfolgreichen read-only Inspect mit begrenzten Metadaten für ein ausgewähltes AI-eigenes Schiff. Der Attach-Versuch stoppte an der leeren Allowlist. **M1 bleibt offen.**

## Follow-up 2026-10-23: UI-Fensterreaktivierung

- Ein erneutes `list_apps()` lieferte genau ein Avorion-Fenster (App-ID `steam://rungameid/445220`, Titel `Avorion`, Prozess `Avorion.exe`). `get_window_state` meldete zunächst, dass es minimiert sei. Die zurückgegebene Referenz wurde aktiviert und mit `sky.get_window` rehydratisiert.
- Frischer Screenshot/UIA zeigten den Vollbild-Ladebildschirm „Leertaste drücken um fortzufahren“ und Fokus auf der Avorion-Fläche. Es wurde keine Taste gesendet. Damit ist die Reaktivierbarkeit der Zielreferenz bestätigt, nicht die Annahme einer Spieleingabe oder die Ursache früherer Fehlschläge.
- Laut API-Dokumentation sind `key: 'space'` und `press_key` mit derselben Window-Referenz gültig. Da keine Taste gesendet wurde, ist dies kein Laufzeitnachweis. Inspect, Attach und IPC-Roundtrip bleiben offen; **M1 bleibt offen.**

### Historischer Follow-up: Read-only Inspect und Allowlist-Sperre (2026-10-23)

Der neueste Nutzer-Appshot zeigt ein ausgewähltes AI-eigenes Schiff. Der read-only Inspect gelang und gab eine Schiff-ID, den Serverordner der Testinstanz, `AI-owner=true` sowie `probe_script_path=data/scripts/entity/ai_commander_probe.lua` aus; konkrete IDs und lokale Pfade werden hier ausgelassen. Die Ausgabe belegt die begrenzten Inspect-Metadaten für diese Sitzung. `probe_script_path` ist ein hart codierter vorgesehener Pfad und kein Nachweis, dass das Script angehängt wurde. Der Attach-Versuch endete fail-closed mit `No disposable test ship is allowlisted; no attach was requested.`; es wurde nichts angehängt. Es gab keinen weitergehenden State-Export und keinen IPC-Roundtrip. Die lokale Tastenbelegung ordnet `Nearest Enemy` Scancode 21 (R) zu; das belegt nur eine konfigurierte Taste, nicht dass sie gedrückt wurde oder die Auswahl verursachte. **M1 bleibt offen.**

### Follow-up: ausgewählte AI-Fregatte und ID-bestätigter Attach-Kandidat (2026-10-23)

Ein neuerer Appshot zeigt eine ausgewählte AI-Fregatte und einen erfolgreichen read-only Inspect mit `AI-owner=true`; konkrete Schiff-ID und lokale Pfade werden nicht veröffentlicht. Der Quellkandidat verlangt exakt `attach confirm <ship-id-from-inspect>` und vergleicht den ID-Token mit dem aktuell ausgewählten Ziel. Die Argumentübergabe an den Handler und die geänderte Quelldatei im Server bleiben zur Laufzeit unbestätigt. Eine akzeptierte Probe entfernt sich nicht nach `--cycles 1`: Sie bleibt am Entity und pollt weiterhin einmal pro Sekunde. Es gab keinen Attach, weitergehenden State-Export oder IPC-Roundtrip. **M1 bleibt offen.**
