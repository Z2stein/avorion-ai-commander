# Avorion AI Commander

## Ziel

Einen autonomen, LLM-gestützten Commander für Avorion-NPC-Schiffe untersuchen und entwickeln. Der geplante Ablauf liest Spielzustand, wählt aus begrenzten taktischen Möglichkeiten, validiert Anfragen auf dem Server und prüft das Ergebnis.

Das erste Laufzeitziel ist ein nachweisbarer Proof of Concept: Ein externer Prozess erhält den Zustand eines NPC-Schiffs, sendet eine validierte Anfrage, und der Spielserver bestätigt ein beobachtbares Ergebnis.

## Status

Statische Discovery und ein Offline-Protokollgerüst sind dokumentiert. Das Repository enthält eine passive Avorion-Mod, das versionierte AC|1-Textprotokoll, eine Python-Bridge und eine Offline-Fake-Peer-Testsuite. Nach dem Windows-Zeilenende-Fix bestehen beide Offline-Suiten mit jeweils 27 Python-Tests; sie verwenden Fake-Peers und temporäre Dateien und führen kein Avorion-Lua aus. Neue Fälle decken CRLF-Antworten, weiterhin verbotene eingebettete CR-Zeichen und das streng begrenzte Fortsetzen nach HELLO_ACK ab.

**M1: Zwei passive Live-IPC-Zyklen wurden beobachtet; die formale Abnahme bleibt offen.** Im ersten Lauf brach der Bridge-Aufruf nach `HELLO/HELLO_ACK` am CRLF-Parser ab. Nach dem Parserfix wurde dieselbe aktive Lua-Session mit Resume ab `PROBE 1` fortgesetzt und mit STATE, ACK und ACKED beendet (Exitcode 0). Im zweiten Lauf startete die Bridge in der frischen Testkopie mit leeren Kanaldateien und absolvierte `HELLO/HELLO_ACK → PROBE 1 → STATE → ACK 1 → ACKED` in einem Aufruf (Exitcode 0). Der STATE dieses Laufs stimmte mit der unabhängig bestätigten erwarteten Schiff-ID überein und enthielt Hülle, Schildstatus und Position. Der Attach-Befehl meldete, dass die Probe bereits angehängt erscheint; ein neues Attach wurde nicht bestätigt. Das belegt passive Lua-/Python-Datei-IPC für zwei einzelne Sessions, keine ShipAI-Aktion, keinen Kampf und keine Autonomie. Ein nachfolgender read-only Audit bestätigte, dass der TCP-Fallback auf allen Interfaces lauscht; `--ip` gilt laut installierter Serverhilfe nur für Steam Networking. Der frühere LAN-TCP-Test war freigegeben, belegt aber keine Isolation. Nach `AGENTS.md` ist es daher nicht **GETESTET**, solange technische Isolation nicht bestätigt und der Ablauf nicht reproduzierbar in bestätigter Isolation abgenommen ist. Genaue geladene Quellidentität und Langzeitverhalten bleiben offen. Der zweite Testserver läuft noch. Die Ein-Zyklus-Läufe lassen die Probe weiter pollen; eine weitere Wiederholung braucht frische IPC-Kanaldateien, da die vorhandenen Logs Records enthalten.

Der vorhandene read-only Inspect-Handler braucht einen Ingame-Spieler- und Zielkontext; `commands.txt`-Aufrufe liefern `playerIndex == nil`. Eine separate Konsolenabfrage per Entity-ID ist ein ungetesteter API-Kandidat, weil die Verfügbarkeit von `Sector()` im globalen Command-Kontext ungeklärt ist.

Ein späterer Server- und Clientstart auf einer frischen Testkopie mit Avorion 2.5.13 erreichte `Server startup complete`; der Client verband sich und lud die Welt. Der Server meldete Multiplayer aktiviert, nicht gelistet und Steam Networking deaktiviert; der Serverstart war erfolgreich. Der Server läuft weiterhin. Technische Netzisolation ist nicht abgenommen. Frühere Startfehler und ihre offene Ursache sind im [Projektstatus](docs/project/status.md) dokumentiert.

Frühere Chat-Eingabeversuche uebermittelten den vollstaendigen Inspect-Befehl nicht und sind als historische Chronologie dokumentiert. Ein späterer Nutzer-Appshot bestätigt einen erfolgreichen read-only Inspect; der damalige Attach-Versuch wurde durch die leere Allowlist fail-closed gestoppt. Details und Evidenzgrenzen stehen im [Projektstatus](docs/project/status.md).

Hostinventare, lokale Pfade, Serverlogs, Spielstandnamen und Netzwerkdiagnosen sind absichtlich nicht enthalten. Aus ihrem Fehlen lässt sich nichts über einen konkreten Rechner oder Laufzeitstand ableiten.

### Computer-Use-/Vollbild-Befund (2026-10-23)

Ein lesender Fensterinventar-Check fand genau ein Avorion-Fenster (`Avorion`, `steam://rungameid/445220`, Prozess `Avorion.exe`); der Screenshot zeigte den Ladebildschirm mit Space-Hinweis. Zwei gezielt an dieses Fenster gerichtete Space-Eingaben führten zu keinem dauerhaft verifizierten Bildschirmwechsel. Die Zielfenster-Auswahl ist bestätigt, die Annahme der Eingabe durch Avorion nicht. UIA-Fokus lag auf der Avorion-Fläche, nicht auf einem Chatfeld; es wurde kein weiterer Tastendruck ausgelöst. Ein Computer-Use-/Windows-/Vollbild-/Game-Input-Problem ist nur eine Hypothese. Offizielle OpenAI-Seiten ergaben keinen passenden Vollbild-Spiel-Workaround und keinen bestätigten Avorion-spezifischen Fehler. [Community-Berichte zu nicht erkannten oder steuerbaren Windows-Apps](https://community.openai.com/t/computer-use-plugin-stopped-working/1397316/2) und [zu einem Initialisierungsfehler vor der App-Erkennung](https://community.openai.com/t/windows-computer-use-fails-at-initialization-with-eperm-after-repair-reset-and-reinstall/1389280) sind anekdotische Nutzerberichte, keine bestätigte Fehlerursache. **M1 bleibt offen.**

### Follow-up: UI-Fensterreaktivierung (2026-10-23)

Ein erneuter lesender App-Check lieferte genau ein Avorion-Fenster (`steam://rungameid/445220`, Titel `Avorion`, Prozess `Avorion.exe`). Nach einer Minimiert-Meldung wurde die zurückgegebene Referenz aktiviert und erneut geladen. Screenshot und UIA zeigten den Vollbild-Ladebildschirm „Leertaste drücken um fortzufahren“ und Fokus auf der Avorion-Fläche. Es wurde keine Taste gesendet. Die Zielreferenz lässt sich reaktivieren; Annahme einer Eingabe und Ursache früherer Fehlschläge bleiben offen. Die API-Dokumentation beschreibt `key: 'space'` und `press_key` mit derselben Fensterreferenz, belegt aber keine Spieleingabe. M1 bleibt offen.

### Historischer Follow-up: Inspect-Ziel-Guard (2026-10-23)

Ein früherer Nutzer-Appshot zeigte zweimal `No valid selected target was found.`; der Projektquelltext enthaelt dieselbe Meldung an der Guard für `craft.selectedObject`. Das ist bedingter Laufzeitbeleg für Handler-Ausführung bis zu dieser Guard im früheren Zwischenstand. Der neueste Appshot loest diesen Zwischenstand ab: Ein read-only Inspect gelang, der Attach-Versuch wurde an der leeren Allowlist gestoppt. **M1 bleibt offen.**

### Historischer Follow-up: Read-only Inspect und Allowlist-Sperre (2026-10-23, vor den Live-Zyklen)

Der neueste Nutzer-Appshot zeigt ein ausgewähltes AI-eigenes Schiff. Der read-only Inspect gelang und gab eine Schiff-ID, den Serverordner der Testinstanz, `AI-owner=true` sowie `probe_script_path=data/scripts/entity/ai_commander_probe.lua` aus; konkrete IDs und lokale Pfade werden hier ausgelassen. Die Ausgabe belegt die begrenzten Inspect-Metadaten für diese Sitzung. `probe_script_path` ist ein hart codierter vorgesehener Pfad und kein Nachweis, dass das Script angehängt wurde. Der Attach-Versuch endete fail-closed mit `No disposable test ship is allowlisted; no attach was requested.`; es wurde nichts angehängt. Es gab keinen weitergehenden State-Export und keinen IPC-Roundtrip. Die lokale Tastenbelegung ordnet `Nearest Enemy` Scancode 21 (R) zu; das belegt nur eine konfigurierte Taste, nicht dass sie gedrückt wurde oder die Auswahl verursachte. **M1 bleibt offen.**

### Historischer Follow-up: ausgewählte AI-Fregatte und ID-bestätigter Attach-Kandidat (2026-10-23)

Ein neuerer Appshot zeigt eine ausgewählte AI-Fregatte und den erfolgreichen read-only Inspect mit `AI-owner=true`; konkrete Schiff-ID und lokale Pfade werden nicht veröffentlicht. Der Quellkandidat verlangt jetzt exakt `/ai_commander_attach_probe attach confirm <ship-id-from-inspect>` und vergleicht den ID-Token mit dem weiterhin ausgewählten Ziel. Das ist noch nicht im laufenden Server geladen oder ausgeführt; die Argumentübergabe durch Avorion bleibt unbestätigt. Der Probe-Code hat keine automatische Selbstentfernung. Nach einem Bridge-Lauf mit `--cycles 1` bliebe das Script am Schiff und pollte weiter im Sekundentakt. Kein Attach oder IPC-Roundtrip ist erfolgt; M1 bleibt offen.

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
