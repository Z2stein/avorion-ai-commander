# Avorion Commander: hybrider Architekturentwurf

**Status:** Statischer Entwurf. M1-Laufzeitverhalten ist nicht nachgewiesen; autonome oder unbeaufsichtigte Schiffssteuerung ist nicht belegt.

M0 fasst eine statische Dokumentationsprüfung zusammen. Das ist kein Laufzeitnachweis und keine Freigabe für einen Live-Test. Die offenen M1-Isolationsgates stehen im [Isolationsplan](../testing/isolation-plan.md) und [Projektstatus](../project/status.md).

## Ziel und Abgrenzung

Ein serverseitiges Mod-Script veröffentlicht einen eng begrenzten Zustand eines ausdrücklich gebundenen NPC-Schiffs. Ein externer Python-Prozess verwaltet Protokoll, Sicherheitsregeln und später optional einen LLM-Taktikvorschlag. In M1 validiert die Mod ausschließlich Probe-/Bestätigungsnachrichten und ruft keine ShipAI-Aktion auf. Aktionsbefehle sind frühestens Gegenstand eines separat versionierten M2-Protokolls.

Das LLM erhält weder direkten Zugriff auf Lua, Dateisystem, Avorion-Serverbefehle noch Betriebssystemfunktionen. In M0 und M1 wird kein LLM benötigt und keine Spielaktion ausgelöst. M1 weist ausschließlich bidirektionale Kommunikation nach. Der Entwurf setzt keine Änderungen an der Spielinstallation und keine zusätzliche Parser-/JSON-Abhängigkeit voraus; ein Laufzeittest darf erst nach Bestätigung der Isolation und Freigabe des Testservers stattfinden. Eine externe Nachricht, die tatsächlich eine Schiffsaktion und deren Wirkung belegt, gehört zu M2.

## Evidenzlage

Die Kategorien folgen [AGENTS.md](../../AGENTS.md). API-Dokumentation und Codebeispiele sind keine Laufzeittests.

| Aussage | Status | Beleg und Grenze |
|---|---|---|
| Die versionierte API-Dokumentation benennt Avorion 2.5.13 / Commit 0417ab29738c. | **DOKUMENTIERT** | [API-Capability-Matrix](../research/avorion-api.md); kein Laufzeitbeleg. |
| Die versionierte API-Dokumentation beschreibt ShipAI-Aktionen, Gegnerabfragen, Entity-Zustand, Script-Callbacks, `valid()` und `Sector():exists(id)`. | **DOKUMENTIERT** | [API-Capability-Matrix](../research/avorion-api.md). Das belegt weder Laufzeitverhalten noch Kampfwirkung. |
| Die Security-Notiz und API-Dokumentation beschreiben eingeschränkte Dateioperationen. | **DOKUMENTIERT** | [IPC-Forschungsbericht](../research/ipc-feasibility.md); konkreter Modzugriff bleibt ungetestet. |
| Ein externer Prozess kann mit der Mod über Dateien im konkreten Galaxy-/Moddata-Pfad kommunizieren. | **PLAUSIBEL** | OS-Zugriff, Mod-Sandbox, Flush-/Close-Verhalten und Polling müssen isoliert bestätigt werden. |
| Lua stellt im untersuchten Bestand JSON, Socket oder HTTP für diesen Zweck bereit. | **Nicht belegt** | [IPC-Forschungsbericht](../research/ipc-feasibility.md). JSON erfordert einen mitgelieferten Parser/Serializer oder ein begrenztes Textschema. |
| Bidirektionale Kommunikation und NPC-Aktion wurden ausgeführt. | **GETESTET: nein** | [API-Bericht](../research/avorion-api.md) und [IPC-Forschungsbericht](../research/ipc-feasibility.md) dokumentieren keine Laufzeittests. |

Die versionierte API-Dokumentation weist Avorion 2.5.13 / Commit 0417ab29738c aus. Build- und Spielversionsangaben sind getrennt zu behandeln. Keine bestehende Benutzergalaxie ist eine Testumgebung; ein isolierter Laufzeitnachweis ist nicht Teil dieses öffentlichen Snapshot ([Environment](../research/environment.md), [Entscheidung D-002](../project/decisions.md)).

## Systemgrenze

~~~text
Avorion-Server
  serverseitiges Entity-Script
    ├─ begrenzte Beobachtung und Sequenzierung
    ├─ Parser + unabhängige Validierung
    └─ schmaler ShipAI-Adapter
          │
          │ getrennte Request-/Response-Dateien
          │ Kandidat; Pfad und Atomizität noch zu testen
          ▼
Externer Python-Prozess
  Datei-Bridge → Zustands-/Sequenzverwaltung → deterministische Sicherheitsregeln
                                                │
                                      später: LLM-Taktikvorschlag
~~~

Datei-IPC ist der vorläufige M1-Kandidat: Die Dateizugriffe und Sandboxgrenzen sind in versionierten Quellen beschrieben, aber im Avorion-Laufzeitpfad nicht bestätigt. RCON ist ein externer Server-Befehlskanal, aber kein strukturierter Modzustandskanal; commandsFile ist auf Serverbefehle ausgerichtet. Keiner dieser Wege ersetzt den Request-/Response-Vertrag für Wahrnehmung und Status ([IPC-Vergleich](../research/ipc-feasibility.md)).

Vorgesehen sind zwei feste Kanaldateien in der Moddata der bestätigten Test-Galaxy; Nachrichten bestimmen weder Pfade noch Dateinamen. Append-Modus, Tail-Reads, Pfadauflösung und Dateiwachstum sind noch nicht getestet. M1 setzt deshalb frische Testdaten und eine harte Zyklenbegrenzung voraus.

## Minimale Wahrnehmung

Die erste Beobachtung enthält nur den Zustand des freigegebenen Schiffs:

- Entity-ID in einer noch festzulegenden Wire-Darstellung der dokumentierten Uuid;
- durability, maxDurability, shieldDurability, shieldMaxDurability und isShieldActive;
- Position als x/y/z aus `translationf` (der M1-Source-Entwurf verwendet `translationf.x/y/z`; Komponenten-Zugriff ist nicht laufzeitgeprüft);
- session_id und observation_sequence.

Die API-Dokumentation beschreibt getEnemies(), getEnemyShips() und getNearestEnemy() sowie state, isAttackingSomething und attackedEntity. Diese Felder können später für Kandidaten und Rückmeldungen geprüft werden. Ausgabeform, Typen, Zielsemantik und Verhalten im Ziel-Build müssen vor Verwendung bestätigt werden. In der ersten Version werden keine Gegner außerhalb des aktuellen, vom Server geprüften Sektors vorausgesetzt ([API-Capability-Matrix](../research/avorion-api.md)).

Python veröffentlicht an ein späteres LLM ausschließlich dieses explizit begrenzte Schema. Sicherheitsregeln bleiben deterministisch: fehlender oder veralteter Zustand darf keinen neuen offensiven Befehl auslösen. Ein sicherer Rückzug oder eine Rückgabe an Vanilla-AI wird daraus nicht abgeleitet; ein belegter Stop-/Handover-Mechanismus fehlt noch.

## M1-Protokoll: No-Action-Probe AC|1

M1 verwendet ein festes, ASCII-basiertes Zeilenformat. JSON wird bewusst nicht vorausgesetzt: die Recherche fand keine aktuelle Lua-JSON-API, und M1 benötigt weder JSON noch eine externe Parser-Abhängigkeit. Der vorgesehene Mini-Parser ist auf feste Feldzahl, bekannte Recordtypen und eingeschränkte Werte begrenzt; seine Implementierung und Fehlerbehandlung sind noch nicht laufzeitbestätigt. Ein späteres Aktionsprotokoll kann JSON oder ein anderes Format erhalten, aber erst nach eigener Parser-/Lizenzprüfung und neuer Protokollversion.

Jeder Record ist genau eine ASCII-Zeile mit LF am Ende und der Struktur `AC|1|TYPE|FELDER`. Das Trennzeichen ist `|`. Freie Texte, Escapes, unbekannte Felder und beliebige Befehle sind nicht erlaubt. CR, NUL und zusätzliche Separatoren führen zur Ablehnung; eine unvollständige letzte Zeile bleibt bis zu einem folgenden Poll unbearbeitet. Ein kompletter Record einschließlich LF darf höchstens 512 Bytes belegen. Diese Zeilenregeln und das Verhalten bei Teilreads sind ein Laufzeit-Gate, kein bestätigtes Verhalten der Lua-Datei-API im Ziel-Build.

| Richtung | Record | Felder nach Typ |
|---|---|---|
| Bridge → Mod | `AC\|1\|HELLO\|<session_id>` | session_id |
| Mod → Bridge | `AC\|1\|HELLO_ACK\|<session_id>` | session_id |
| Bridge → Mod | `AC\|1\|PROBE\|<session_id>\|<seq>` | session_id, seq |
| Mod → Bridge | `AC\|1\|STATE\|<session_id>\|<seq>\|<ship_id>\|<durability>\|<max_durability>\|<shield_durability>\|<shield_max_durability>\|<shield_active>\|<x>\|<y>\|<z>` | Session und seq echoen; danach Entity-ID, vier dokumentierte Hull-/Shieldwerte, shield_active als 0/1 und translation x/y/z |
| Bridge → Mod | `AC\|1\|ACK\|<session_id>\|<seq>` | Bestätigung, dass Bridge die STATE-Zeile vollständig geparst und der Probe zugeordnet hat |
| Mod → Bridge | `AC\|1\|ACKED\|<session_id>\|<seq>` | Bestätigung der Bridge-ACK |
| Mod → Bridge | `AC\|1\|ERROR\|<session_id>\|<seq-or-0>\|<code>` | Fester Fehlercode: `invalid_entity`, `invalid_session`, `malformed_record`, `state_unavailable`, `unexpected_sequence` oder `unknown_type`; `seq=0` ist ein nicht korrelierter Diagnosefehler und keine Probe-ID |

Die Form der Entity-ID im Wireformat ist noch zu bestätigen. Die API dokumentiert Entity-ID als Uuid, aber keine geprüfte Lua-Textserialisierung. Ein solcher ID-Wert darf keine Separatoren oder Steuerzeichen enthalten; bei ungültiger Serialisierung wird der Probe abgebrochen. Zahlen werden als finite ASCII-Dezimalwerte mit Punktserialisierung übertragen, niemals als NaN/Inf oder localeabhängige Dezimalkommas. Die verfügbare Lua-Formatierung ist im Zielkontext noch nicht getestet. shield_active ist genau 0 oder 1. Hull-/Shieldwerte müssen endlich und nicht negativ sein; Maximalwerte müssen nicht negativ sein; Positionswerte müssen endlich sein.

Die Korrelations-ID ist das Tupel session_id + seq. In M1 ist seq in HELLO-unabhängigen Probe-/Antwortrecords eine strikt steigende positive Dezimalzahl von 1 bis höchstens 50 pro Session; der Bridge-Prozess vergibt seq=1 für den ersten PROBE. Jede normale Antwort übernimmt dieselbe Session und Sequenz. Für nicht korrelierbare Fehler darf `ERROR` seq=0 tragen; diese Fehlerzeile bestätigt oder beantwortet keinen Probe. message_id muss nicht separat übertragen werden: Richtung + Session + Recordtyp + seq identifizieren die Nachricht. Die Session-ID wird vom Python-Prozess pro Lauf als 32 kleingeschriebene Hex-Zeichen erzeugt. Sie verhindert die Annahme alter Session-Replays, ist aber kein Authentifizierungsmerkmal.

### M1-Ablauf

1. Vor dem Lauf prüfen Bridge und Mod beide festen Kanaldateien. Beide müssen neu oder leer sein; jede nicht leere Datei führt zum Abbruch. Der Aufrufer übergibt Python den Pfad mit `--moddata-dir`; der aktuelle CLI-Code prüft nur, dass das Verzeichnis existiert, nicht dass es zur freigegebenen Test-Galaxy gehört. Erst nach unabhängiger Pfadprüfung darf Python genau ein HELLO(session_id) anhängen.
2. Das Mod-Script akzeptiert genau eine Session und hält sie nur im Arbeitsspeicher. Ein zweites HELLO oder ein Request mit anderer Session wird mit `ERROR|invalid_session` zurückgewiesen; im aktuellen Source deaktiviert erst das Überschreiten des Fünf-Fehler-Limits den Kanal. `negativeInputCount` und `errorOutputCount` werden bei `initialize` auf 0 gesetzt und bei HELLO nicht zurückgesetzt, daher gilt das Limit je Skriptinitialisierung/Lauf. Ein neuer Lauf benötigt frische leere Dateien.
3. Nach HELLO_ACK sendet die Bridge genau einen PROBE(session_id, seq). Es gibt höchstens einen offenen Probe; der nächste seq beginnt erst nach ACKED des vorherigen.
4. Der Probe enthält keinen ship_id-Selektor, kein action-Feld und keinen Lua-Ausdruck. Der Source-Entwurf ruft `Entity()` aus einem Entity-Script auf und beabsichtigt damit, die Entity des Scriptkontexts zu lesen; der tatsächliche Attachment-/Loading-Punkt ist noch nicht implementiert oder nachgewiesen. Bei ungültiger Entity versucht der aktuelle Source-Entwurf `ERROR|invalid_entity` zu schreiben und kehrt ohne STATE zurück. Scheitert der ERROR-Outbox-Append, wird der Kanal fail-closed deaktiviert und der Fehler per `print` gemeldet; der ERROR-Record ist nicht garantiert. Bei gültiger Entity liest er die Zustandsfelder und schreibt genau eine STATE-Antwort. Er ruft ShipAI nicht auf.
5. Die Bridge prüft Version, Session, Sequenz, Entity-ID, Feldanzahl, Zahlenwerte und Frische des Probes. Sie verlangt `--expected-ship-id`, prüft den STATE-Wert dagegen und hängt erst bei Übereinstimmung ACK(session_id, seq) an. Die CLI kann nicht beweisen, dass der Aufrufer diese ID unabhängig vom genehmigten Testschiff ermittelt hat.
6. Das Mod schreibt ACKED. Damit ist die bidirektionale Probe beendet. ACKED bestätigt den Transport und das Parsing, keine Spielaktion.
7. Unbekannte Recordtypen (einschließlich ACTION oder COMMAND), Versionen, Sequenzen und unzulässige Entity-Bindungen werden fail-closed behandelt. Keine Eingabe kann eine ShipAI-Funktion auswählen oder auslösen. In AC|1 wird nach einem Timeout nicht automatisch erneut gesendet.

Die versionierte API-Dokumentation beschreibt `Entity(id)` zur ID-Auflösung und `valid(entity)` zur Entity-Prüfung. Der aktuelle Source-Entwurf ruft stattdessen `Entity()` ohne ID im Entity-Scriptkontext auf; dieser Aufruf und die Zuordnung zu einem genehmigten Testschiff sind nicht laufzeitgeprüft. Er liest `durability`, `maxDurability`, `shieldDurability`, `shieldMaxDurability`, `isShieldActive` und `translationf.x/y/z`. Diese Felder und Typen sind **DOKUMENTIERT** für Avorion 2.5.13 / Commit 0417ab29738c; ihr Export durch diesen M1-Scriptpfad bleibt **nicht GETESTET**. Die Server-Script-Callbacks `initialize`, `getUpdateInterval()` und `updateServer(timeStep)` sind dokumentiert. 1 Hz ist ein Startvorschlag, keine belegte Tickrate.

### Datei- und Framing-Vertrag

Als vorläufige feste Pfade sind vorgesehen:

- `Server().folder .. "/moddata/avorion-ai-commander/bridge-to-mod.log"`: alleiniger Writer ist Python; Lua liest.
- `Server().folder .. "/moddata/avorion-ai-commander/mod-to-bridge.log"`: alleiniger Writer ist Lua; Python liest.

Der Lua-Source setzt den Basisordner auf `Server().folder .. "/moddata/avorion-ai-commander"`; er legt diesen Ordner nicht selbst an. Python erhält ihn über `--moddata-dir` und prüft nur, dass ein Verzeichnis mit diesem Namen existiert. Die CLI vergleicht den übergebenen Pfad **nicht** mit `Server().folder` oder einer isolierten Testumgebung und beweist keine Isolation. Der Aufrufer muss den korrekten absoluten Pfad liefern; M1 ist erst abnahmefähig, wenn dieser Pfad unabhängig mit der genehmigten Test-Galaxy abgeglichen wurde. Keine Datei darf in einem bestehenden Benutzerspielstand, globalem Profil-moddata oder dem Installationsverzeichnis liegen.

Jede Seite hängt einen vollständig serialisierten Record mit abschließendem LF an ihre eigene Datei und schließt die Datei, bevor die Gegenseite ihn verwenden darf. Die Gegenseite verarbeitet nur vollständige Zeilen. Das vermeidet Umbenennen/Tempdateien als vorausgesetzte API, beweist aber keine Atomizität oder Flush-/Close-Sichtbarkeit: beides bleibt Laufzeit-Gate. Die Sandbox-Dokumentation beschreibt begrenzte Dateioperationen; konkrete Pfade und Berechtigungen bleiben ein Laufzeit-Gate. Append-Modus, begrenztes Einlesen/Zeilenframing, Umgang mit Teilreads, Lua-Serialisierung, Pfadauflösung und externer OS-Zugriff sind nur **PLAUSIBEL** und müssen isoliert geprüft werden. Der aktuelle Scaffold-Entwurf hält in Python einen Byte-Offset für die Mod→Bridge-Datei; Lua liest die Bridge→Mod-Datei jeweils vom Anfang mit einem 64-KiB-Limit und verarbeitet nur Zeilen hinter einem flüchtigen Zähler vollständiger Records. Damit wird kein `seek` in Lua vorausgesetzt, aber wiederholtes vollständiges Lesen kann dieselben Bytes oft lesen; die Last ist nicht gemessen. Der Offset/Zähler, Umgang mit einem unvollständigen Tail und Dateisichtbarkeit bei gleichzeitiger Nutzung sind ebenfalls Laufzeit-Gates. Python verlangt ein bereits existierendes IPC-Verzeichnis; der Lua-Source legt den Unterordner nicht an. Die Mod prüft nichtleere Dateien durch lesenden Zugriff, aber ein nicht öffnbares File kann dabei wie ein fehlendes/Leeres erscheinen; ein tatsächlicher Pfad-/Rechtefehler muss im isolierten Lauf abgefangen werden. Das M1-Protokoll behauptet daher noch keine funktionierende IPC.

Der Reader darf höchstens 64 KiB je Richtung lesen; dieser Grenzwert gilt auch für die gesamte Datei. Jeder Lauf darf pro Richtung höchstens 106 Records enthalten: HELLO + bis zu 50 PROBEs + 50 ACKs + bis zu fünf negative/replay Eingaben auf Bridge→Mod sowie HELLO_ACK + bis zu 50 STATEs + 50 ACKEDs + bis zu fünf ERRORs auf Mod→Bridge. Bei maximal 512 Bytes einschließlich LF belegt das höchstens 54.272 Bytes und bleibt unter der 64-KiB-Dateigrenze. Bridge und Mod müssen bei einer überschrittenen Record-, Byte- oder Dateigrenze fail-closed abbrechen. Ein M1-Lauf hat höchstens 50 gültige Probezyklen und fünf negative/replay Fälle; das ist eine harte Grenze, keine Dauernutzungsempfehlung. Es gibt keine angenommene Lua-Lösch-, Truncate- oder Rotation-API. Jeder Lauf startet mit frischen, leeren Kanaldateien in einem neuen oder nachweislich leeren Moddata-Pfad einer eigens genehmigten Test-Galaxy. Nicht leere Dateien werden nicht fortgesetzt oder bereinigt, sondern führen zum Abbruch; ihr Testdatenpfad bleibt zur Analyse getrennt erhalten.

### Aktueller Source-Skeleton: bekannte Grenzen

Die folgenden Punkte beschreiben den Code-Stand statisch; sie sind nicht als Laufzeitnachweis zu lesen:

- Lua verwendet die oben genannten Pfade, erstellt aber weder das Verzeichnis `moddata/avorion-ai-commander` noch einen automatischen Attach-Punkt für `ai_commander_probe.lua`. Ein source-only Kommando-Kandidat liegt unter `avorion-mod/data/scripts/commands/ai_commander_attach_probe.lua`; ob Avorion solche Mod-Kommandodateien automatisch entdeckt und lädt, ist nicht dokumentiert. Der Kandidat übergibt `data/scripts/entity/ai_commander_probe.lua`. `getScriptPath()` dokumentiert, dass der an `Entity:addScript` übergebene Pfad als Top-Level-Scriptpfad verwendet wird, ohne dessen mod-relative Auflösung zu erklären. Das Format `data/scripts/path/to/file.lua` und Mod-Dateien sind für `asyncf` dokumentiert; das Format `data/scripts/path/to/file.lua` ist für `asyncf` dokumentiert. Dies belegt keine Mod-relative Auflösung für `Entity:addScript` oder einen Attach zur Laufzeit; das Probe-Mapping bleibt unbestätigt. Die Probe bleibt ein nicht automatisch angehängtes Entity-Script-Template.
- Der Lua-Code ruft `Entity()` im Entity-Scriptkontext auf, nicht die dokumentierte `Entity(id)`-Auflösung. Welche Entity `Entity()` zur Laufzeit liefert und ob das Script tatsächlich am genehmigten Testschiff hängt, ist offen.
- Die Python-CLI akzeptiert jedes bereits existierende Verzeichnis als `--moddata-dir`; sie prüft nicht, dass es zu `Server().folder`, der freigegebenen Test-Galaxy oder einem isolierten Server gehört. M1-Isolation wird durch die CLI daher nicht erzwungen.
- Lua und Python beschränken Session-IDs derzeit beide auf 32 kleingeschriebene Hex-Zeichen. Die Bridge bricht bei einer Antwort mit fremder Session sofort mit einem Bridge-Fehler ab; sie validiert dadurch aber weiterhin nicht, ob das Verzeichnis selbst isoliert ist. Lua weist falsche Sessions als `invalid_session` zurück, deaktiviert den Kanal aber erst nach mehr als fünf negativen Eingaben je Skriptinitialisierung/Lauf; die Zähler werden bei `initialize`, nicht bei HELLO, zurückgesetzt.
- Der Source verwendet die unten aufgeführten kleingeschriebenen ERROR-Codes. `seq=0` kennzeichnet einzelne nicht korrelierbare Fehler und ist kein gültiger Probe-Schlüssel. Python prüft STATE-IDs auf 1–128 druckbare ASCII-Zeichen und vergleicht sie vor ACK mit `--expected-ship-id`; diese Prüfung beweist nicht, dass der Aufrufer den Parameter korrekt und unabhängig vom genehmigten Testschiff erhoben hat. Lua verwirft vor STATE statisch IDs, die nicht 1–128 Bytes lang sind, Bytes außerhalb `0x21–0x7E` enthalten oder `|` enthalten; es versucht dann `state_unavailable` mit derselben Sequenz zu schreiben und kehrt ohne STATE zurück. Scheitert der ERROR-Outbox-Append (etwa beim Öffnen, Schreiben oder Schließen), wird der Kanal fail-closed deaktiviert und der Fehler per `print` gemeldet; der ERROR-Record ist nicht garantiert. Das bestätigt weder das Textformat der UUID noch, dass die tatsächliche Entity-ID die Grenzen erfüllt oder den Lua↔Python-Roundtrip besteht.
- Lua schreibt positive STATE-/ACKED-Records in die Mod→Bridge-Datei, gibt sie aber nicht als positive Konsolenlogs aus. Vor erfolgreichem HELLO können abgelehnte Records zudem keine session-korrelierte ERROR-Antwort tragen. Die M1-Abnahme muss Kanaldateien und Bridge-Ausgabe sichern; positive Mod-Protokollierung ist im Skeleton noch nicht enthalten.
- Python hat derzeit einen 1,0-Sekunden-Probeabstand und 0,1 Sekunden Pollabstand als CLI-Defaults; das sind implementierte Startwerte, keine gemessenen Laufzeitwerte. Lua fordert ein Update-Intervall von 1,0 Sekunden an.

### Sequenz, Replay und Deduplizierung

- Innerhalb einer laufenden Session akzeptiert das Mod nur den nächsten erwarteten seq. Ein Rücksprung, übersprungener Wert oder Duplikat erzeugt `ERROR|unexpected_sequence` und keine STATE-Antwort. Die Bridge weist Duplikate und fremde Session-Records zurück, wenn sie während Handshake/Roundtrips eingelesen oder beim finalen einmaligen Drain nach dem letzten ACKED gelesen werden. Records, die erst nach diesem Drain angehängt werden, liegen außerhalb der Erkennungsgarantie dieses endlichen Laufs.
- Kein Record wird zur automatischen Wiederholung freigegeben. Ein fehlender oder nur teilweise sichtbarer Record führt zum Timeout bzw. Abbruch. Die negativen/replay Fälle der M1-Abnahme sind absichtlich begrenzte Testeingaben, die höchstens einen ERROR-Record je Fall erzeugen; sie sind keine automatische Retry-Logik.
- Die Sequenz-/Deduplizierungsdaten leben nur im RAM. Nach Neustart einer Seite wird der Lauf abgebrochen; ein Fortsetzen desselben Logs ist nicht erlaubt. Ein neuer Versuch benötigt eine neue Session-ID und frische leere isolierte Kanaldateien, damit bereits angehängte PROBE-/STATE-Records nicht wieder abgespielt werden.
- Ein Angreifer mit OS-Schreibzugriff auf die Kanaldatei kann HELLO fälschen. Session-ID ist keine Sicherheitsauthentifizierung. M1 enthält keine Aktion, verwendet nur einen isolierten Testpfad und setzt OS-Rechte voraus. Für M2 ist ein separates Bedrohungsmodell erforderlich.

### Grenze zu JSON und M2-Aktionen

JSON ist in AC|1 nicht erlaubt. Die geprüften versionierten Quellen dokumentieren keine Lua-JSON-API; kein Parser wird vorausgesetzt. Für eine spätere JSON-Variante wären Parserquelle, Lizenz, Größen-/Tiefenlimits und Fehlerverhalten vorab zu prüfen. Ein M2-Aktionsschema muss separat versioniert werden; unbekannte Aktionen bleiben in AC|1 grundsätzlich ungültig.

M2 ist separat zu versionieren; AC|1 bleibt No-Action. Die ursprüngliche Projektpriorität ist einfache Bewegung, dann Zielauswahl, dann Angriff. Deshalb ist `setFly(...)` der erforderliche erste M2-Aktionskandidat. `setPassive()` darf optional in einem separaten Smoke-Test mit frischer Test-Entity ausgeführt werden, ist aber nicht Teil von M2 und kann den Bewegungsnachweis nicht ersetzen. `setAttack(target)` und `setAggressive(...)` bleiben spätere Schritte.

### M2 – erste Bewegungsaktion: kurzer serverseitiger Wegpunkt

Dieser Entwurf beschreibt nur die statische Wahl und Abnahmebedingungen; er autorisiert keinen Lauf. M2 darf erst nach bestandenen M1-Isolations-Gates und ausdrücklicher Projektfreigabe ausgeführt werden. Der einzelne Versuch muss während des gesamten Ablaufs direkt beaufsichtigt werden. Er beweist keine unbeaufsichtigte oder autonome Steuerung. Bestehende Galaxien bleiben ausgeschlossen.

Der erste erforderliche Befehl ist genau ein `ShipAI(boundShipId):setFly(waypoint, arrivalRadius, nil, nil, false)` auf einem dedizierten, entbehrlichen NPC-Testschiff. Die versionierte API-Dokumentation beschreibt `ShipAI(id)` für ein bestehendes Entity oder dessen ID; `setFly` hat fünf Parameter und gibt nichts zurück. Der Wegpunkt liegt im selben Sektor und wird serverseitig aus einer vorab geprüften Testkonfiguration bestimmt. Die Bridge/LLM darf keine freien Zielkoordinaten oder Entity-ID übermitteln. `collisionException` bleibt `nil`; Fighter-Orders werden nicht gesetzt; `lenientArrivalAllowed` ist `false`. Wegpunktdistanz und `arrivalRadius` müssen serverseitig begrenzt werden; sichere Bewegungs-/Radiuswerte sind bisher weder kalibriert noch getestet.

Vor Dispatch bindet der Server den Scriptkontext an die Test-Entity und prüft erneut `valid(entity)`, die Übereinstimmung mit der serverseitig gehaltenen Entity-ID sowie `entity.isShip`. Kein Request darf die Aktion auf eine beliebige Entity umlenken. Besitz-/Spielerkontrollstatus müssen für den Testaufbau unabhängig ausgeschlossen werden; Eigentumsfelder sind kein Laufzeitnachweis dafür, dass kein Spieler aktiv steuert. Während des gesamten Beobachtungsfensters darf kein anderes AI-Skript konkurrierende ShipAI-Orders an dieselbe Entity senden, damit der Einzelauftrag nicht überschrieben wird. Zusätzlich müssen Session, nächste Sequenz und die neueste Beobachtungssequenz passen. Ablehnung, veraltete Beobachtung, Replay oder unbekannte Aktion führen vor dem ShipAI-Aufruf zum Abbruch.

Aktionsstatus bleiben getrennt: `received`, `validated`, `dispatched`, `effect_confirmed`, `rejected`, `failed`. `dispatched` bedeutet nur, dass der Aufruf erfolgte; `setFly` liefert keinen Rückgabewert. `state == AIState.Fly` und ein mit festgelegter Toleranz verglichenes `flyTarget` sind Auftragsbelege; ein exakter Vektorvergleich `flyTarget == waypoint` ist nicht dokumentiert. `flyTarget` beschreibt das aktuelle Flugziel nur in `Fly` oder `FlyLinear`. `effect_confirmed` darf erst gesetzt werden, wenn mehrere unabhängige, serverseitige Positionsproben tatsächlichen Fortschritt zum Wegpunkt zeigen und eine spätere Probe die Entity innerhalb des gewählten `arrivalRadius` beobachtet. Ein einzelner Positionssample oder gesetztes Ziel genügt nicht. Sichere Bewegungs-/Radiuswerte und die konkrete Kalibrierung wurden noch nicht getestet. Ob AIState nach Ankunft zu Idle wechselt, wird nicht vorausgesetzt.

Bei `isStuck`, ausbleibendem Positionsfortschritt oder Ablauf eines vorab festgelegten, noch zu kalibrierenden Beobachtungsfensters endet der Versuch mit `failed`. Nicht erneut senden und keine Folgeaktion automatisiert auslösen. Die API-Doku beschreibt, dass `setFly` bei potenziell kollisionsgefährlichen Wegen stehen bleibt; das ist kein Laufzeitbeweis für Kollisionsfreiheit oder für einen sicheren Rückfall. Geschwindigkeit, Wegpunkt-/Radiuswerte, Ankunftszeit, tatsächlicher Bewegungsverlauf und Übergabe an Vanilla-AI bleiben offen, bis sie isoliert gemessen sind.

**Statische Evidenz:** `{AVORION_INSTALL}\Documentation\ShipAI.html:203-219,244-276,783-810` dokumentiert den Konstruktor, Fly, `flyTarget`, `isStuck`, `state`, Hindernisvermeidung, Ankunftsradius und den fehlenden Rückgabewert. `{AVORION_INSTALL}\Documentation\Entity.html:795-799,885-889,1119-1122`, `Functions.html:1296-1316,3515-3523` und `Sector [Server].html:890-908` belegen Entity-ID/Schiffsfeld, Position, Distanzvergleich, `valid()` und Sektor-ID-Prüfung. Das Vanilla-Muster `{AVORION_INSTALL}\data\scripts\entity\ai\patrol.lua:47-72` setzt `setFly()` mit einem Wegpunkt und dem Schiffsradius als Ankunftsradius ein. Diese Quellen sind **DOKUMENTIERT** bzw. statische **VANILLA-SKRIPTBELEGE**; M2-Dispatch, Bewegung und Ankunft bleiben **PLAUSIBEL**, nicht **GETESTET**.

`setPassive()` ist außerhalb von M2 optional und kann in einem separaten Lauf auf einer frischen Test-Entity den Action-Pipeline-Smoke-Test abdecken: vor/nach Zustand protokollieren und einen Wechsel zu Passive beobachten. Das beweist weder Bewegung noch das M2-Ziel und ist daher keine M2-Abnahme. Im M2-Lauf wird ausschließlich die eine vorgesehene Bewegungsaktion ausgelöst.

Vor einer späteren Ziel- oder Kampfaktion wären weiterhin gebundene Schiff-ID, Zielmitgliedschaft, `valid(entity)`, `Sector():exists(id)`, Fraktions-/Zivilistenschutz und Replay-Schutz serverseitig zu prüfen. Eine AI-Zielzuordnung ist kein bestätigter Treffer oder Waffenschaden. Ein geprüfter Stop-/Handover an Vanilla-AI ist kein M2-Abnahmekriterium für diesen direkt beaufsichtigten Einzelversuch. Er bleibt aber ein zwingendes Gate vor unbeaufsichtigtem Betrieb und vor weiterem Commander-Ausbau ab M3.

## Validierungsregeln

Für M1 validiert die Bridge jeden Probe-Record und jede STATE-Antwort. Das Mod validiert jede HELLO-, PROBE- und ACK-Zeile selbst; die Bridge darf durch Fehler oder Parser-Ausnahmen keinen automatischen Retry auslösen.

1. Nur ASCII-Records bis 512 Bytes, exakte Feldzahl, bekanntes AC|1-Recordtyp-Token und LF-Abschluss akzeptieren.
2. Session-ID muss dem beim ersten HELLO festgelegten, Bridge-generierten Hexwert entsprechen. Ein zweites HELLO oder ein Request mit anderer/alter Session wird abgelehnt und darf die aktive Session nicht zurücksetzen; nur ein neuer Lauf mit frischen leeren Kanaldateien darf eine neue Session beginnen. Die Bridge bricht bei einem abweichenden Response-Sessionwert sofort ab und protokolliert den Fehler lokal.
3. seq muss eine positive Ganzzahl im definierten Bereich sein; nur nächster Wert wird angenommen. Duplikate werden nach obiger Regel behandelt, rückläufige/übersprungene Werte abgelehnt.
4. Das Mod hat genau eine lokal gebundene Entity. Keine Nachricht darf eine beliebige Entity auswählen. Vor Zugriff valid(entity); wenn die Referenz per ID neu aufgelöst werden muss, zusätzlich Sector():exists(id), solange das Objekt im aktuellen Sektor erwartet wird.
5. State-Datensatz muss Entity-ID, finite Werte, erlaubte bool-Darstellung und erwartete Recordlänge enthalten. Durability/Shieldwerte dürfen nicht negativ, Positionen nicht NaN/Inf sein. Lehnt die Mod-Eingabevalidierung einen Record ab, versucht sie nur bei aktiver Session einen ERROR-Record zu schreiben; die Sequenz ist dabei parsebar oder wird mit `seq=0` als nicht korrelierbar markiert. Scheitert dieser ERROR-Outbox-Append, wird der Kanal fail-closed deaktiviert und der Fehler per `print` gemeldet. Ohne aktive Session wird kein ERROR-Record versucht: die Ablehnung zählt nur gegen das Negativlimit, und erst beim Überschreiten wird der Kanal lokal geschlossen/gemeldet. Ein Fehler beim Parsen/Validieren eines empfangenen STATE stoppt und protokolliert die Bridge lokal, sendet keinen ACK und erzeugt keinen Mod-ERROR-Record.
6. Python verlangt `--expected-ship-id` mit 1–128 druckbaren ASCII-Zeichen ohne das reservierte `|` und vergleicht die ID in STATE vor ACK. Der CLI-Parameter muss vom Aufrufer unabhängig am genehmigten Testschiff verifiziert werden; der Bridge-Prozess kann diese Herkunft nicht belegen. Doppelte STATE-Zeilen werden nur zurückgewiesen, wenn sie während der laufenden Roundtrips oder am finalen Drain sichtbar sind.
7. Jegliche zusätzlichen Felder oder Aktionstokens werden abgelehnt. Im Mod gibt es für AC|1 keinen ShipAI-Adapter-Aufruf.

### Statusstufen

| Status | Was er in M1 belegt |
|---|---|
| HELLO_ACK | Mod hat die Sessionkennung syntaktisch akzeptiert; keine Authentifizierung. |
| STATE | Mod hat die Entity geprüft und ihre Zustandsfelder in einen Record serialisiert; kein Laufzeitbeweis bis isoliert getestet. |
| ACK | Bridge hat STATE geparst und der Probe zugeordnet; noch keine Mod-Bestätigung. |
| ACKED | Mod hat ACK zur passenden Session/Sequenz gelesen. Dies ist der Endpunkt des M1-Roundtrips, keine Aktion. |
| ERROR | Record abgelehnt; Fehlercode gibt nur die Protokollursache an. |

Im M1-Pfad existieren weder dispatched noch effect_confirmed; diese Begriffe dürfen nicht für Probe-/State-Ergebnisse verwendet werden.

## Takt, Timeout und Rückfall

- **Vorgeschlagene Startwerte, keine Messwerte:** Lua fordert in `getUpdateInterval()` 1,0 Sekunden an; Python hat derzeit 1,0 Sekunden Probeabstand und 0,1 Sekunden Pollabstand als CLI-Defaults. Keiner dieser Werte ist gemessen; `updateServer`/`getUpdateInterval()` sind dokumentiert, ihre tatsächliche Frequenz und Last bleiben im isolierten Aufbau zu prüfen.
- **Timeout-Implementierung im Bridge-Skeleton, nicht zur Laufzeit gemessen:** HELLO_ACK hat eine eigene monotone 5-Sekunden-Deadline. Für jede vollständige PROBE→STATE→ACK→ACKED-Transaktion gilt eine gemeinsame monotone 5-Sekunden-Deadline; sie umfasst PROBE-Anhang, Empfang und Parsing/Validierung von STATE einschließlich des Vergleichs mit `--expected-ship-id`, ACK-Anhang und Empfang von ACKED. Ein Timeout oder Validierungsfehler schließt den Lauf fail-closed. **Vorgeschlagene Startziele, keine Messwerte:** 1-Hz-Probeabstand und p95-Roundtrip höchstens 2 Sekunden; kein vollständiger Probe-Roundtrip über 5 Sekunden. Kein LLM-Aufruf und keine gemeinsame Systemuhr erforderlich; Session/seq korrelieren die Schritte.
- Bei fehlender Datei, offenem/teilweisem Record, unerwarteter Version, Sequenzfehler, fehlender Entity oder Timeout werden keine Spielaktionen ausgelöst. Bridge protokolliert den Fehler und beendet den Lauf bei Protokollabweichung; kein automatisches Replay.
- Die append-only Logs werden nicht rotiert oder gelöscht. 50 Zyklen, fünf negative/replay Fälle, 106 Records und 64 KiB pro Richtung sind harte M1-Begrenzungen. An der ersten erreichten Grenze stoppt der Lauf und der Testdatensatz wird zur Analyse aufbewahrt; ein Folgelauf braucht neue leere Kanaldateien in einem frischen Testpfad.
- M1 ist passiv. Für M2 ist „keinen neuen Befehl senden“ allein kein sicherer Fallback: eine zuvor ausgelöste ShipAI-Order könnte weiterlaufen. Rückgabe an Vanilla-AI, Stop-Befehl oder Wiederherstellung einer vorherigen Order sind nicht belegt. Der einzelne M2-Bewegungs-Proof bleibt direkt beaufsichtigt und löst keine Wiederholung oder Folgeaktion aus. Unbeaufsichtigter Betrieb und weiterer Commander-Ausbau ab M3 bleiben gesperrt, bis Stop/Handover und Bridge-Ausfall isoliert getestet sind.

## Gedächtnis

In M0 und M1 wird kein persistentes Commander- oder LLM-Gedächtnis angelegt. Flüchtige Sequenz-, Deduplizierungs- und Zustandsdaten dienen nur der Protokollverwaltung. Diagnoseprotokolle speichern die nötigen IDs, Statusstufen und Fehler, keine vollständigen Spielstände.

Persistente Erfahrung gehört frühestens in M6 und braucht eine eigene Abnahme. Beobachtung, abgeleitete Hypothese und Entscheidung sind zu trennen; Umfang, Aufbewahrung, Neustart- und Löschverhalten sind zu begrenzen und zu testen ([Roadmap](../project/roadmap.md)).

## M0/M1-Abnahmekriterien

Das sind Sollkriterien, keine ausgeführten Tests.

### M0 – Discovery konsolidieren

M0 gilt erst als abgenommen, wenn:

- die versionierte API-Dokumentation und ihre Spielversion nachvollziehbar referenziert sind;
- jede für M2 vorgesehene API-Signatur, Script-Kontext und relevante Parameter in der API-Recherche belegt ist; Unbekanntes bleibt offen;
- vorläufiger IPC-Pfad und Protokollformat/Parser festgelegt oder begründet offen sind; ungeprüfte Dateisemantiken (OS-Zugriff, vollständiges Schreiben/Lesen, Rename/Marker, Teilread) werden mit Evidenzstatus dokumentiert und als M1-Vorbedingungen ausgewiesen;
- Zielberechtigung, Session-Neustart, Deduplizierung und Antwortstatus als prüfbare Verträge vorliegen;
- ein konkreter Plan für einen isolierten Testserver und ein separates, entbehrliches Savegame vorliegt ([isolation-plan.md](../testing/isolation-plan.md)); vor M1 muss die Isolation nachgewiesen sein;
- bestehende Mods nur als Designreferenz verwendet werden, solange Kompatibilität und Lizenz nicht geklärt sind ([Existing Solutions](../research/existing-solutions.md)).

M0 ist Recherche und Entscheidung. Die Research-Berichte enthalten keinen Laufzeitnachweis; der Status einer Phasenabnahme steht in [status.md](../project/status.md).

### M1 – Communication Proof of Concept

M1 wird ausschließlich auf dem ausdrücklich genehmigten, bestätigten isolierten Testserver und Spielstand abgenommen:

1. Ein genehmigter Attachment-Punkt bindet das Entity-Script nachweisbar an das Testschiff. Der Aufrufer übergibt eine unabhängig am genehmigten Testschiff geprüfte `--expected-ship-id` mit 1–128 druckbaren ASCII-Zeichen ohne `|`. Mod und Python schließen HELLO/HELLO_ACK ab und führen danach den festen AC|1-Ablauf PROBE → STATE → ACK → ACKED aus; bei ID-Abweichung stoppt die Bridge vor ACK. Der Record enthält exakt die dokumentierten Entity-Felder und keine Aktion.
2. Die dokumentierte Offline-Suite umfasst 22 Python-Tests gegen Fake-Peers und temporäre Dateien. Sie prüft weder Lua/Avorion-Laufzeit noch reale IPC. Der source-only Lua-Injektor beschreibt 50 erfolgreiche Zyklen und repräsentative Negativfälle, wurde aber nicht gegen Avorion ausgeführt ([Injector-Protokoll](../testing/lua-protocol-injector.md)).
3. Falsche Version, fremde Session, Duplikat, Sequenzsprung/-rücklauf, fehlerhafte Feldzahl und unbekannter Nachrichtentyp müssen gemäß Schema abgelehnt werden. Der aktuelle Injektor prüft Version, einen vorzeitigen nächsten PROBE vor ACK, Fremd-Session, unbekannten Typ und ein wiederholtes ACK. Der frühe PROBE prüft den Stop-and-wait-Guard, nicht einen Sequenzsprung oder ein Duplikat/Replay nach bereits verarbeitetem PROBE; falsche PROBE-Feldzahl bleibt ebenfalls außerhalb der fünf injizierten Fälle. Das Lua-Limit wird bei `initialize`, nicht bei HELLO, zurückgesetzt. Ein unvollständiger Tail-Record wird bis zum abschließenden LF nicht verarbeitet; der Injektor beobachtet bei der ersten PROBE ein konfiguriertes Stillefenster per Polls plus finalem Outbox-Read und vervollständigt dann mit LF. Ein Rennen zwischen finalem Read und LF bleibt möglich; seine Dauer ist nicht gemessen, und dies ist kein Nachweis des Lua-Pollings. Wenn eine erwartete Antwort ausbleibt, muss die Bridge-Deadline separat fail-closed enden. Der Lua-Reader selbst hat für den Tail keinen Timeout. Duplikat- und Fremdrecord-Erkennung gilt für Records, die während der Handshake-/Probe-Roundtrips eingelesen oder beim finalen einmaligen Drain nach dem letzten ACKED sichtbar sind. Nach diesem Drain angehängte Records sind außerhalb der Garantie. Die Mod schreibt einen ERROR-Record nur bei aktiver Session; wenn kein seq parsebar ist, verwendet sie `seq=0` als nicht korrelierbaren Diagnosewert. Ohne aktive Session gibt es keinen ERROR-Record; die Eingabe zählt gegen das Negativlimit, und bei dessen Überschreitung wird der Kanal lokal geschlossen/gemeldet. Ein Bridge-Fehler bei fremder Response-Session oder fehlerhaftem STATE wird lokal ausgegeben, beendet den Bridge-Lauf und erzeugt keinen Mod-ERROR-Record. Ein abweichender STATE-Ship-ID-Wert wird in der Bridge vor ACK abgelehnt. Es wird kein ShipAI-Aufruf ausgeführt.
4. Die Kanaldateien und Bridge-Ausgabe belegen denselben Session-/Sequenzschlüssel; ein erfolgreicher ACKED-Zyklus belegt nur, dass Bridge den Zustand gelesen hat und Mod ihre ACK verarbeitet hat. Er wird nicht als NPC-Aktion oder Wirkungsnachweis ausgegeben.
5. **Timeout-Kriterium:** HELLO_ACK muss innerhalb seiner eigenen monotonen 5-Sekunden-Deadline eintreffen. Jede PROBE→STATE→ACK→ACKED-Transaktion muss innerhalb einer gemeinsamen monotonen 5-Sekunden-Deadline abgeschlossen sein; diese schließt PROBE-/ACK-Anhang, STATE-Empfang und -Parsing/Validierung einschließlich Prüfung gegen die unabhängig verifizierte `--expected-ship-id` sowie ACKED-Empfang ein. Das sind implementierte Grenzen des Bridge-Skeletons, keine Laufzeitmesswerte. **Vorgeschlagene Startziele, keine Messwerte:** 1-Hz-Probeabstand, derzeit 0,1 Sekunden Pollabstand als Bridge-Startwert und p95-Roundtrip höchstens 2 Sekunden. Fehler- und Timeoutfälle enden fail-closed.
6. Ein Neustart beendet den Lauf. Ein neuer Test verwendet eine neue Session und frische leere isolierte Kanaldateien; Dateien mit alten Records werden abgewiesen und nicht fortgesetzt.
7. Der Lauf bestätigt, dass kein ShipAI-Aufruf erfolgte. Alle IPC-Dateien liegen ausschließlich im freigegebenen isolierten Testpfad; keine bestehende Galaxy-Datei wurde verändert.

### Abgrenzung zu M2

Nach M1 ist M2 zunächst genau ein kurz begrenzter, direkt beaufsichtigter `setFly`-Proof auf einem entbehrlichen NPC in einem isolierten Sektor. Er verlangt einen reproduzierbaren Pfad von `received` → `validated` → `dispatched` → beobachtetem Bewegungsfortschritt und Ankunft; bei Ablehnung, Fehler oder fehlendem Fortschritt endet der Lauf ohne Retry und Folgeaktion. M2 weist weder autonome noch unbeaufsichtigte Steuerung nach; Eingang oder gesetzter ShipAI-Zustand allein belegen keine Bewegung. Ein isoliert geprüfter Stop-/Handover bleibt zwingendes Gate vor unbeaufsichtigtem Betrieb und weiterem Commander-Ausbau ab M3.

## Offene Punkte und Risiken

- **Dateiatomizität:** Erlaubte Datei-IO beweist weder Rename-Atomizität noch Flush-/Close-Reihenfolge oder Verhalten bei gleichzeitiger Nutzung. Polling, Marker und Größenlimits sind isoliert zu untersuchen.
- **Externer Zugriff:** Lua-Schreibzugriff im Modpfad beweist nicht den Dateizugriff des externen Bridge-Prozesses.
- **Zielberechtigung:** Enemy-API und Sector():exists(id) belegen nicht automatisch Allianz-/Zivilistenausnahmen oder den Schutz einer Handelsflotte.
- **Fallback:** Kontrollierter Übergang zur vorherigen/Vanilla-AI bei veralteten Daten oder Bridge-Ausfall ist nicht dokumentiert oder getestet.
- **Aktionswirkung:** AI-Auftrag oder Zielzuordnung ist nicht gleich tatsächlichem Feuern, Treffer oder Schutzwirkung.
- **Takt und Last:** 1,0 Sekunden Mod-Update-/Probeabstand und 0,1 Sekunden Python-Pollabstand sind Startwerte aus dem Source-Skeleton, keine Messwerte; tatsächliche Taktung, Pollinglast und Reaktionszeit wurden nicht geprüft.
- **Parser und IDs:** Lua-JSON-Support und Wire-Kodierung der Entity-Uuid sind offen; Parser-Limits und ID-Roundtrip müssen vor M1 geprüft werden.
- **Sektor-/Entitywechsel:** Callback-Registrierungen sind an Sektor und Entity-Lebensdauer gebunden. Bei Wechsel oder Zerstörung müssen Beobachtung und Bindung verworfen und neu validiert werden ([API-Capability-Matrix](../research/avorion-api.md)).
