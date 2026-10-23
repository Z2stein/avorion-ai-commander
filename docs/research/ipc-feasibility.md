# Machbarkeit von Mod-IPC und externem Prozess

## Umfang und Evidenz

Dies ist eine statische, versionsbezogene Recherche. Sie belegt kein Laufzeitverhalten auf einem konkreten Rechner. Diese statische Recherche führte selbst keinen IPC-Lauf aus; zwei frühere passive Ein-Zyklus-Läufe und danach 50 Zyklen in einer aktiven Lua-Session sind im `docs/project/status.md` dokumentiert.

Verwende die Evidenzstufen des Projekts: **DOKUMENTIERT** bezeichnet eine passende Quelle, **PLAUSIBEL** eine noch nicht nachgewiesene Möglichkeit und **GETESTET** ein reproduzierbares Laufzeitergebnis.

## Dateizugriff und Pfade

- **DOKUMENTIERT:** Avorions [Lua-Sicherheitsnotiz](https://store.steampowered.com/news/posts/?appids=445220&enddate=1568124976&feed=steam_community_announcements) beschreibt eingeschränkten Lua-Dateizugriff und nennt entfernte Prozessfunktionen wie `os.execute()`. Die Notiz führt zulässige Lese-/Schreibbereiche auf; das konkrete Verhalten muss für die Zielspielversion geprüft werden.
- **DOKUMENTIERT:** Die versionsbezogene API-Dokumentation beschränkt `createDirectory`, `listFilesOfDirectory` und `removeDirectory` auf `moddata/` im Avorion-Einstellungsordner. Das ist enger formuliert als die Sicherheitsnotiz, die zusätzlich den Galaxy-Ordner nennt. Dateizugriffe auf Galaxy-Moddata benötigen daher einen isolierten Laufzeittest.
- **PLAUSIBEL:** Ein externer Prozess auf demselben Rechner könnte Dateien mit einer Mod austauschen, sofern beide Prozesse auf das gemeinsame Verzeichnis zugreifen dürfen. Eine serverseitige Mod und ein Unterordner unter dem aufgelösten `Server().folder` sind Kandidaten, aber nicht bestätigte Pfade. `Server().folder` ist als schreibgeschützte Zeichenkette dokumentiert; der Laufzeitwert und Schreibrechte sind hier nicht geprüft.

Datei-IPC ist ein begrenzter Anfrage-/Antwortkanal, kein direkter Datenbankzugriff auf Spielstände. Getrennte Request- und Response-Dateien, Größenlimits, Session-/Sequenzkennung, vollständige Schreibmarker und strikte Validierung verwenden. Eingehenden Text niemals als Lua-Code ausführen. JSON nur verwenden, wenn ein Parser/Serializer verfügbar und geprüft ist; ein kleines festes Textschema kann einfacher sein.

## JSON, Sockets, HTTP und Prozesszugriff

- Die für dieses Projekt untersuchten versionierten API- und Vanilla-Skriptquellen dokumentieren keine JSON-, HTTP- oder LuaSocket-API. Das beweist nicht, dass ein undokumentiertes Interpretermodul unmöglich ist.
- Die Sicherheitsnotiz beschreibt entfernte Prozessstartfunktionen. Die Mod darf daher keinen externen Prozess starten.
- Ein JSON-Dateiformat ist grundsätzlich denkbar; ein Parser im Mod-Kontext ist durch diese Recherche nicht belegt.
- Socket- oder HTTP-Zugriff aus Mod-Lua nicht für M1 voraussetzen, solange keine passende versionierte Quelle oder ein isolierter Laufzeittest die Verfügbarkeit belegt.

## RCON und Befehlsdateien

- **DOKUMENTIERT:** Avorion-Serverdokumentation beschreibt RCON als TCP-Administrationsschnittstelle mit Passwortschutz. RCON ist privilegiert zu behandeln und der Zugriff muss begrenzt werden.
- **DOKUMENTIERT:** Die Serverdokumentation beschreibt eine Befehlsdatei, die nach einem kurzen Zeitraum unveränderten Inhalts gelesen und anschließend geleert wird. Das ist ein einseitiger Weg für Server-Konsolenbefehle, kein strukturierter Modzustandskanal.
- **PLAUSIBEL:** RCON und Befehlsdateien können für Serveradministration oder einfache Befehle genügen. Keiner der Wege liefert die für M1 nötige bidirektionale strukturierte Modzustandskommunikation.
- Die [Avorion-Announcer-Workshopseite](https://steamcommunity.com/sharedfiles/filedetails/?id=2032319866) beschreibt eine Community-Integration mit Python und RCON. Die Kompatibilität mit dem Ziel-Build ist hier nicht belegt.

## Client-/Server-RPC, Logs und Statistiken

- **DOKUMENTIERT:** Avorions Skript-API beschreibt Funktionsaufrufe zwischen Client- und Serverinstanz. Sie verbinden keinen beliebigen externen Prozess. Eine Antwort benötigt einen weiteren RPC-Aufruf; der Server muss Identität und Eingaben prüfen.
- **DOKUMENTIERT:** Die Serverdokumentation beschreibt Statistik- und Serverlogs. Sie können lesendes Monitoring unterstützen, sind aber kein bidirektionaler Befehlskanal. Textformate können sich zwischen Versionen oder Mods ändern.

## Vergleich

| Weg | Eignung für M1 | Wesentliche Grenzen |
|---|---|---|
| Datei-IPC | Vorläufiger lokaler Request-/Response-Kandidat | Sandboxpfad und Berechtigungen, Teilreads, Serialisierung und Polling müssen zur Laufzeit geprüft werden. |
| RCON | Serveradministration | Privilegiert und befehlsorientiert; kein strukturierter Modzustandskanal. |
| Befehlsdatei | Einfache einseitige Befehle | Keine strukturierte Modantwort; Eingabedatei schützen. |
| Client-/Server-RPC | Kommunikation innerhalb Avorions | Erreicht keinen externen Prozess direkt. |
| Logs/CSV | Lesendes Monitoring | Formatänderungen und begrenzter strukturierter Zustand; keine Befehlsantwort. |
| Socket/HTTP oder Prozessstart aus Mod-Lua | Nicht belegt | API-Verfügbarkeit und Sandboxunterstützung sind unbestätigt. |

## Vorläufige Empfehlung

Begrenzte Datei-IPC bleibt M1-Kandidat. Zwei frühere Ein-Zyklus-Läufe und danach 50 Bridge-Zyklen in einer aktiven Lua-Session bestätigten einen begrenzten bidirektionalen Entity-State-Austausch; ein reproduzierbarer Lauf in bestätigter Isolation sowie allgemeine Pfad-, Berechtigungs- und Fehlergarantien sind nicht belegt. RCON für Serveradministration und Befehlsdateien für einfache einseitige Kommandos verwenden. Latenz messen, statt ein Pollingintervall vorauszusetzen.

Dieser statische Recherchebericht enthält selbst keinen Live-Test oder hostbezogene Netzwerkanalyse; zwei separat beobachtete passive Ein-Zyklus-Läufe und danach 50 Bridge-Zyklen in einer aktiven Session sind im öffentlichen Projektstatus dokumentiert. Sie belegen keine bestätigte Netzisolation oder formale M1-Abnahme.
