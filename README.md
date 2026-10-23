# Avorion AI Commander

## Ziel

Einen autonomen, LLM-gestützten Commander für Avorion-NPC-Schiffe untersuchen und entwickeln. Der geplante Ablauf liest Spielzustand, wählt aus begrenzten taktischen Möglichkeiten, validiert Anfragen auf dem Server und prüft das Ergebnis.

Das erste Laufzeitziel ist ein nachweisbarer Proof of Concept: Ein externer Prozess erhält den Zustand eines NPC-Schiffs, sendet eine validierte Anfrage, und der Spielserver bestätigt ein beobachtbares Ergebnis.

## Status

Statische Discovery und ein Offline-Protokollgerüst sind dokumentiert. Das Repository enthält eine passive Avorion-Mod, das versionierte AC|1-Textprotokoll, eine Python-Bridge und eine Offline-Fake-Peer-Testsuite. Die zuletzt dokumentierte Offline-Suite umfasst 22 bestandene Tests; sie verwendet Fake-Peers und temporäre Dateien und führt kein Avorion-Lua aus.

**M1 ist nicht nachgewiesen.** Dieser öffentliche Snapshot belegt weder ein Avorion-Modladen noch einen Lua/Python-IPC-Roundtrip, einen exportierten Schiffszustand oder eine externe Spielaktion. Lua wurde nicht geparst oder ausgeführt. Das Attach-Kommando bleibt standardmäßig fail-closed. Ein Laufzeittest erfordert einen entbehrlichen Spielstand und nachgewiesene Daten- und Netzwerkisolation.

Ein Startversuch auf einer separaten Testgalaxie mit Avorion 2.5.13 endete vor `Server startup complete` mit `include error: module 'generator' not found`. Derselbe Fehler trat auch mit entfernter Projekt-Modpfadangabe auf. Die Ursache ist damit nicht bestimmt und wird dem Projekt-Mod nicht zugeschrieben; ein M1-Laufzeitnachweis entstand nicht.

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
