# Projektstatus

## Evidenzübersicht

- **M0 — Statische Discovery:** Recherche und Testplan liegen vor. Das ist ein Dokumentationsergebnis, kein Laufzeitnachweis.
- **M1-Laufzeitbeobachtung:** Zwei getrennte Ein-Zyklus-Läufe schlossen jeweils `HELLO/HELLO_ACK → PROBE 1 → STATE → ACK 1 → ACKED` mit Bridge-Exitcode 0 ab. Im zweiten Lauf stimmte die STATE-ID mit der unabhängig bestätigten erwarteten Schiff-ID überein; IDs, Sessionwerte und lokale Pfade werden nicht veröffentlicht. Der Lauf verwendete eine frische Testkopie mit eigener Mod- und Backup-Konfiguration und vorab leere Kanaldateien. Der Attach-Befehl meldete, dass die Probe bereits angehängt erscheint; ein neues Attach wurde nicht bestätigt. Das belegt passive Lua-/Python-Datei-IPC für zwei einzelne Sessions, nicht ShipAI-Verhalten, Kampf oder Autonomie. Technische Isolation ist nicht bestätigt; daher ist die formale **GETESTET**-Abnahme nach `AGENTS.md` weiterhin offen. Der zweite Testserver läuft noch. Nach den Ein-Zyklus-Läufen pollt die Probe weiter; eine weitere aktive Wiederholung benötigt frische IPC-Kanaldateien, da die vorhandenen Logs Records enthalten.
- **Offline-Tests:** Der aktuelle Offline-Lauf umfasst 27 bestandene Python-Tests mit Fake-Peers und temporaeren Dateien. Sie fuehren Avorion nicht aus und belegen keine Lua-Laufzeit oder echte Moddata-IPC; der Live-Zyklus ist separat dokumentiert.
- **Lua:** Lua wurde im passiven Live-Zyklus ausgefuehrt; der Source-Text wurde nicht separat geparst.
- **M2 und später:** Geplant; keine Schiffssteuerungsaktion ist nachgewiesen.

## Letzter Laufzeitversuch

Die beiden Live-Smoke-Läufe auf separaten Testkopien lieferten jeweils genau einen vollständigen passiven Zyklus und Exitcode 0. Der jüngere Lauf verwendete frische leere IPC-Kanaldateien; die Logs zeigen exakt drei Records je Richtung, keinen Mehrfachzyklus. Er bestätigte einen STATE-Record und den Vergleich mit der erwarteten Schiff-ID. Der Attach-Befehl meldete bereits vorhandene Probe-Präsenz und forderte keinen neuen Attach an. Das belegt weder eine Spielaktion noch dauerhaften Betrieb. Die Probe pollt weiter; der zweite Testserver läuft noch. Genaue Quellidentität, technische Netzisolation und formale M1-Abnahme bleiben offen.

Fruehere Chat-Eingabeversuche uebermittelten den vollstaendigen Inspect-Befehl nicht; der spaetere read-only Inspect und die historische Ablehnung an der damaligen Allowlist sind durch neuere Attach-/IPC-Belege zeitlich ueberholt.

## Hinweise zur M1-Implementierung

Die Bridge akzeptiert ein explizit uebergebenes Moddata-Verzeichnis; sie kann nicht selbst feststellen, ob dieses isoliert ist. Zwei passive Ein-Zyklus-Läufe wurden beobachtet; `--resume-after-hello` ist eine enge Ausnahme zum normalen Fresh-Channel-Start und setzt einen exklusiven einzelnen Bridge-Writer sowie eine aktive Lua-Session voraus. Der Preflight ist kein Lock und keine Concurrent-Writer-Garantie. Der genaue Quell-/Dispatchstand, technische Isolation und laengerfristiger Betrieb bleiben zu bestaetigen.

## Erforderliche Evidenz vor weiteren Laufzeittests

Die Wiederholung lief auf einer separaten Testkopie mit eigener Mod- und Backup-Konfiguration; der Server erreichte den Start und läuft noch. Ein erfolgreicher read-only Handler-Aufruf, der AI-Eignerstatus und ein passiver Lua/Python-Roundtrip wurden in beiden Live-Sessions beobachtet. Die STATE-ID stimmte im jüngsten Lauf mit der unabhängig bestätigten erwarteten ID überein. Das hart codierte `probe_script_path` allein belegt kein Attach; der Attach-Befehl bestätigte nur bereits vorhandene Probe-Präsenz. Zwei Ein-Zyklus-Beobachtungen sind noch keine formale **GETESTET**-Abnahme, weil die technische Isolation nicht bestätigt ist. Genaue Quellidentität, isolierte Reproduzierbarkeit, Fehlerfälle und Langzeitverhalten bleiben offen. Eine nächste aktive Wiederholung braucht frische IPC-Kanaldateien.

Dieser öffentliche Status lässt Hostinventare, lokale Konfiguration, Spielstandnamen, Prozesskennungen, Zeitstempel und Netzwerkdiagnosen absichtlich aus. Aus dieser Auslassung keine Schlussfolgerung über einen konkreten Rechner ziehen.

## Aktualisierung 2026-10-23

## Aktueller Laufzeitbefund 2026-10-23: zweiter passiver Ein-Zyklus-Lauf

Ein zweiter Lauf auf einer frischen Testkopie erreichte `Server startup complete`; der Server meldete Multiplayer aktiviert, nicht gelistet und Steam Networking deaktiviert. Der Server läuft weiter. Eine getrennte Mod- und Backup-Konfiguration belegt keine technische Netzisolation.

Der read-only Inspect bestätigte ein AI-eigenes Ziel und die erwartete Ship-ID. Ein Attach-Aufruf ohne Bestätigung gab nur Usage aus; `attach confirm <id>` antwortete, die Probe erscheine bereits angehängt, und forderte keinen neuen Attach an. Beide IPC-Dateien waren vor Lua-Initialisierung leer. Die Bridge lief mit einem Zyklus, Exitcode 0: HELLO_ACK, STATE mit passiven Zustandsfeldern und passender ID, danach ACKED. Die geprüften Logs enthalten exakt drei Records pro Richtung und keinen Mehrfachzyklus. Der Lua-Injektor mit 50 Zyklen wurde nicht ausgeführt.

Zusammen mit dem früheren Durchstich sind zwei passive Datei-IPC-Zyklen in getrennten Sessions beobachtet. Die folgenden, zeitlich älteren Unterabschnitte dokumentieren frühere Prüfstände; für den aktuellen Stand gelten die Evidenzübersicht und dieser Laufzeitbefund. Es erfolgte keine ShipAI-Aktion, kein Kampf und keine autonome Steuerung. Da die technische Isolation nicht bestätigt wurde, ist die formale **GETESTET**-Kategorie nach `AGENTS.md` offen. Eine weitere aktive Wiederholung muss frische Kanaldateien verwenden; bestehende Logs werden nicht geleert oder überschrieben.

- Die Offline-Suite wurde erneut mit Python 3.14.5 ausgeführt: 22/22 Tests bestanden, Exitcode 0. Sie verwendet Fake-Peers, temporäre Dateien, Mock-Kanäle und eine Fake-Uhr; sie belegt keine Lua-Laufzeit oder echte Avorion-IPC.
- Laut installierter API-Dokumentation erhält ein Konsolen-/RCON-Command `playerIndex == nil`. Der bestehende read-only Inspect-Handler benötigt Ingame-Spieler- und Zielkontext; `commands.txt` kann diesen Kontext nicht bereitstellen.
- Eine separate read-only Konsolenabfrage per Entity-ID ist als API-Kandidat dokumentiert. Ob `Sector()` im globalen Command-Kontext verfügbar ist, bleibt unbestätigt. Die dokumentierte Sektor-Auflistung liefert alle Treffer ohne eingebaute Obergrenze und ist nicht implementiert.
- Die API-Dokumentation beschreibt keinen Hot-Reload für Command-Scripts. Der laufende Server wurde nicht für diese Prüfung verändert oder neu gestartet.
- **Historischer UI-Stand vor dem Live-Durchstich:** Eine damalige lesende Spielansicht zeigte eine leere Chatzeile. Inspect, Attach und IPC-Roundtrip wurden zu diesem Zeitpunkt nicht ausgeführt; der aktuelle Laufzeitstand steht oben.

## Historische Aktualisierung 2026-10-23: Computer-Use-/Vollbild-Befund

- Ein lesender Fensterinventar-Check fand genau ein Avorion-Fenster (`Avorion`, `steam://rungameid/445220`, Prozess `Avorion.exe`). Der Screenshot zeigte den Ladebildschirm mit Space-Hinweis.
- Zwei gezielt an dieses Fenster gerichtete Space-Eingaben führten zu keinem dauerhaft verifizierten Bildschirmwechsel. Die Zielfenster-Auswahl ist bestätigt; ob Avorion die Eingabe annahm, ist nicht bestätigt. UIA-Fokus lag auf der Avorion-Fläche, nicht auf einem Chatfeld. Es wurde kein weiterer Tastendruck ausgelöst.
- Computer-Use/Windows/Vollbild/Game-Input bleibt eine mögliche, unbewiesene Ursache. Offizielle OpenAI-Seiten ergaben keinen passenden Vollbild-Spiel-Workaround und keinen bestätigten Avorion-spezifischen Fehler. [Community-Berichte zu Windows-App-Erkennung/-Steuerung](https://community.openai.com/t/computer-use-plugin-stopped-working/1397316/2) und [zu einem Initialisierungsfehler vor der App-Erkennung](https://community.openai.com/t/windows-computer-use-fails-at-initialization-with-eperm-after-repair-reset-and-reinstall/1389280) sind anekdotische Nutzerberichte, keine bestätigte OpenAI-Fehlerursache.
- Inspect, Attach und IPC-Roundtrip wurden nicht ausgeführt. **M1 bleibt offen.**

## Historischer Follow-up 2026-10-23: Inspect-Ziel-Guard im früheren Appshot

- Ein früherer Nutzer-Appshot zeigte zweimal `No valid selected target was found.`; derselbe Wortlaut steht an der Guard für `craft.selectedObject`. Das ist bedingter Laufzeitbeleg, dass der Handler im früheren Zwischenstand bis zu dieser Guard ausgeführt wurde, sofern die Quelle geladen war.
- Der neueste Nutzer-Appshot supersedes diesen Zustand: Er zeigt einen erfolgreichen read-only Inspect mit begrenzten Metadaten für ein ausgewähltes AI-eigenes Schiff. Der Attach-Versuch stoppte an der leeren Allowlist. **M1 bleibt offen.**

## Historischer Follow-up 2026-10-23: UI-Fensterreaktivierung

- Ein erneutes `list_apps()` lieferte genau ein Avorion-Fenster (App-ID `steam://rungameid/445220`, Titel `Avorion`, Prozess `Avorion.exe`). `get_window_state` meldete zunächst, dass es minimiert sei. Die zurückgegebene Referenz wurde aktiviert und mit `sky.get_window` rehydratisiert.
- Frischer Screenshot/UIA zeigten den Vollbild-Ladebildschirm „Leertaste drücken um fortzufahren“ und Fokus auf der Avorion-Fläche. Es wurde keine Taste gesendet. Damit ist die Reaktivierbarkeit der Zielreferenz bestätigt, nicht die Annahme einer Spieleingabe oder die Ursache früherer Fehlschläge.
- Laut API-Dokumentation sind `key: 'space'` und `press_key` mit derselben Window-Referenz gültig. Da keine Taste gesendet wurde, ist dies kein Laufzeitnachweis. Inspect, Attach und IPC-Roundtrip bleiben offen; **M1 bleibt offen.**

### Historischer Follow-up: Read-only Inspect und Allowlist-Sperre (2026-10-23)

Der neueste Nutzer-Appshot zeigt ein ausgewähltes AI-eigenes Schiff. Der read-only Inspect gelang und gab eine Schiff-ID, den Serverordner der Testinstanz, `AI-owner=true` sowie `probe_script_path=data/scripts/entity/ai_commander_probe.lua` aus; konkrete IDs und lokale Pfade werden hier ausgelassen. Die Ausgabe belegt die begrenzten Inspect-Metadaten für diese Sitzung. `probe_script_path` ist ein hart codierter vorgesehener Pfad und kein Nachweis, dass das Script angehängt wurde. Der Attach-Versuch endete fail-closed mit `No disposable test ship is allowlisted; no attach was requested.`; es wurde nichts angehängt. Es gab keinen weitergehenden State-Export und keinen IPC-Roundtrip. Die lokale Tastenbelegung ordnet `Nearest Enemy` Scancode 21 (R) zu; das belegt nur eine konfigurierte Taste, nicht dass sie gedrückt wurde oder die Auswahl verursachte. **M1 bleibt offen.**

### Historischer Follow-up: ausgewählte AI-Fregatte und ID-bestätigter Attach-Kandidat (2026-10-23)

Ein neuerer Appshot zeigt eine ausgewählte AI-Fregatte und einen erfolgreichen read-only Inspect mit `AI-owner=true`; konkrete Schiff-ID und lokale Pfade werden nicht veröffentlicht. Der Quellkandidat verlangt exakt `attach confirm <ship-id-from-inspect>` und vergleicht den ID-Token mit dem aktuell ausgewählten Ziel. Die Argumentübergabe an den Handler und die geänderte Quelldatei im Server bleiben zur Laufzeit unbestätigt. Eine akzeptierte Probe entfernt sich nicht nach `--cycles 1`: Sie bleibt am Entity und pollt weiterhin einmal pro Sekunde. Es gab keinen Attach, weitergehenden State-Export oder IPC-Roundtrip. **M1 bleibt offen.**

## Historischer Follow-up 2026-10-23: erster beobachteter passiver Live-IPC-Zyklus

Die Ingame-Antwort meldete, dass die Probe am ausgewaehlten AI-Schiff bereits angehaengt erscheint. Nach HELLO/HELLO_ACK brach der erste Bridge-Lauf vor PROBE an einer CRLF-Antwort ab. Nach dem Parserfix wurde dieselbe aktive Session mit `--resume-after-hello` fortgesetzt: genau ein `PROBE 1 -> STATE -> ACK 1 -> ACKED`, Bridge-Exitcode 0. STATE entsprach der unabhaengig bestaetigten erwarteten Schiff-ID; konkrete IDs und lokale Pfade werden nicht veroeffentlicht.

Damit sind Lua-Ausfuehrung und ein vollstaendiger passiver Zustandszyklus belegt. Steuerungs-/Kampfverhalten, laengerfristige Stabilitaet und die genaue geladene Quellidentitaet bleiben offen. Die Probe bleibt angehaengt und pollt weiter. Resume setzt einen exklusiven einzelnen Bridge-Writer und eine aktive Lua-Session voraus; Snapshot-Vergleiche sind kein Lock und keine Concurrent-Writer-Garantie. Der Offline-Harness belegt nur Parser-/Resume-Regressionen und enthaelt keine Live-Claims.
