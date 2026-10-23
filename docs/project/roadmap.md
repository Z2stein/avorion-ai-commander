# Roadmap

Die statische Discovery und ein Offline-M1-Gerüst liegen vor. Laufzeitverhalten ist nicht belegt. Die Meilensteine unterscheiden Quelltext und Offline-Tests von Avorion-Laufzeitevidenz.

## M0 — Discovery (statisch dokumentiert)

Die versionbezogene API, Lua-Sandbox, mögliche IPC-Wege, öffentliche Lösungen, Risiken und Gates für isolierte Tests dokumentieren. Die statische Arbeit belegt nicht, dass eine API oder ein IPC-Weg zur Laufzeit funktioniert.

## M1 — Kommunikations-Proof of Concept (nicht nachgewiesen)

Das passive Gerüst in `avorion-mod/` und `bridge/` verwendet AC|1 ohne JSON-Abhängigkeit. Die Offline-Suite ist mit 22 bestandenen Python-Tests gegen Fake-Peers und temporäre Dateien dokumentiert. Sie testet weder den Avorion-Lua-Parser noch Modladen, Sandbox-Berechtigungen oder echte IPC. Lua wurde nicht geparst oder ausgeführt.

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
