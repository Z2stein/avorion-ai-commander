# Roadmap

Die statische Discovery und ein Offline-M1-Gerüst liegen vor. In einer aktiven Lua-Session wurden 50 passive M1-Live-Zyklen beobachtet; weitergehendes Laufzeitverhalten nicht. Die Meilensteine unterscheiden Quelltext und Offline-Tests von Avorion-Laufzeitevidenz.

## M0 — Discovery (statisch dokumentiert)

Die versionbezogene API, Lua-Sandbox, mögliche IPC-Wege, öffentliche Lösungen, Risiken und Gates für isolierte Tests dokumentieren. Die statische Arbeit belegt nicht, dass eine API oder ein IPC-Weg zur Laufzeit funktioniert.

## M1 — Kommunikations-Proof of Concept (50 passive Live-Zyklen beobachtet; Abnahme offen)

Das passive Geruest in `avorion-mod/` und `bridge/` verwendet AC|1 ohne JSON-Abhaengigkeit und enthaelt keine ShipAI-Aktion. Die aktuelle Offline-Suite besteht aus 32 Python-Tests gegen Fake-Peers und temporaere Dateien. Separat davon schloss `probe_bridge.py --resume-after-hello` in einer bereits aktiven Lua-Session 50 Sequenzen `PROBE -> STATE -> ACK -> ACKED` mit Exitcode 0 ab. Je Richtung lagen 101 Records vor; alle STATE-IDs stimmten mit der unabhängig bestätigten erwarteten ID überein. Der separate source-only Lua-Injektor brach bereits nach HELLO_ACK an CRLF ab und hat diese 50 Zyklen nicht ausgeführt. Der erfolgreiche Bridge-Lauf belegt 50 passive Zustandstransfers in dieser Sitzung, keine Schiffssteuerung, Fehlerfallabdeckung oder Langzeitstabilität. Der Server war per TCP im LAN erreichbar; technische Isolation ist nicht bestätigt, daher bleibt die formale M1-Abnahme offen. Details: [Isolationsplan](../testing/isolation-plan.md) und [Projektstatus](status.md).

Für die Abnahme muss ein isolierter Lauf belegen: Die Mod wurde geladen; ein No-Action-Inspect identifiziert ein Testschiff; Lua und Python tauschen versionierte, korrelierte Anfragen und Antworten aus; fehlerhafte, wiederholte, fremde Session-, Sequenz- und Schiffs-ID-Nachrichten werden fail-closed behandelt; und der Lauf erzeugt prüfbare Records. M1 darf keine ShipAI-Aktion auslösen. Der Ablauf steht im [Isolationsplan](../testing/isolation-plan.md).

## M2 — Beaufsichtigter Proof einer einzelnen Schiffsaktion (geplant)

Erst nach bestandenem M1 und bestandenen Isolations-Gates wird genau eine begrenzte Bewegungsanfrage auf einem entbehrlichen NPC-Testschiff geprüft. Der Server wählt und validiert das Ziel; Bridge und LLM liefern weder beliebige Koordinaten noch Entity-IDs. Bewegung muss anhand serverseitiger Beobachtungen bestätigt werden, nicht nur anhand eines Dispatch- oder AI-Zustands. Das belegt nur den beaufsichtigten Test, keinen autonomen Betrieb.

## M3 — Deterministischer Commander (geplant)

- Begrenztes, versioniertes Zustandsformat verwenden.
- Vorgeschlagene Aktionen vor der Ausführung validieren.
- Wiederholbare Szenarien in einer isolierten Testumgebung prüfen.

## M4 — LLM-Commander (geplant)

- Nur strukturierte Entscheidungen aus einer Allowlist annehmen.
- Ausgabe validieren und bei Timeout oder Verbindungsverlust deterministisch zurückfallen.
- Dem LLM keinen direkten Datei-, Skript- oder Betriebssystemzugriff geben.

## M5 — Kampf-Prototyp (geplant)

- Verhalten anhand beobachteter Zustände und Bedrohungen definieren.
- Aktionen und Ergebnisse protokollieren.
- Rückzug und deterministischen Fallback in isolierten Szenarien prüfen.

## M6 — Resilienz und Gedächtnis (geplant)

- Fehler, Neustarts und persistenten Zustand begrenzen und dokumentieren.
- Benutzerspielstände schützen.
- Regressionstests weiterhin isoliert ausführen.
