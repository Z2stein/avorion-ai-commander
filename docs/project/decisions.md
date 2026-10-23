# Entscheidungen

## D-001 — Projektmaterial von der Spielinstallation trennen

**Status:** Angenommen

Projektdateien bleiben außerhalb der Spielinstallation. Spiel- und Workshop-Dateien werden im Rahmen der normalen Entwicklung nicht geändert.

## D-002 — Keine Tests auf bestehenden Spielständen

**Status:** Angenommen

Laufzeittests benötigen einen entbehrlichen Spielstand und nachgewiesene Isolation. Eine bestehende Benutzergalaxie ist keine Testumgebung.

## D-003 — Evidenz ausdrücklich kennzeichnen

**Status:** Angenommen

Verwende **BESTÄTIGT**, **DOKUMENTIERT**, **PLAUSIBEL** und **GETESTET**, um direkte Beobachtungen, Dokumentation, Hypothesen und reproduzierbare Laufzeitergebnisse zu unterscheiden. Ein API-Eintrag belegt keine Ausführung; eine empfangene Anfrage belegt keine Spielwirkung.

## D-004 — Aktionen begrenzen, hybride Steuerung bleibt vorläufig

**Status:** Vorläufig

Das LLM darf strukturierte Entscheidungen aus einer Allowlist vorschlagen. Schnelle oder sicherheitskritische Steuerung bleibt deterministisch. Kommunikations-, API- und Aktionsentscheidungen hängen von API- und Sandbox-Evidenz ab.

## D-005 — Datei-IPC ist der vorläufige M1-Kandidat

**Status:** Vorläufig

Versionsbezogene API- und Sicherheitsquellen beschreiben eingeschränkte Dateizugriffe; die konkreten Berechtigungen und Pfade des Zielsystems wurden nicht zur Laufzeit geprüft. M1 untersucht einen bidirektionalen Dateikanal zwischen serverseitiger Mod und externem Prozess. Das ist kein Laufzeitnachweis; siehe [IPC-Recherche](../research/ipc-feasibility.md) und [Isolationsplan](../testing/isolation-plan.md).

## D-006 — AC|1 ist ein begrenztes ASCII-Protokoll für eine No-Action-Probe

**Status:** Vorläufig

M1 verwendet feste ASCII-Records; beide Writer schreiben LF. Der Lua-Inbox-Parser verlangt LF, waehrend der Python-Bridge-Reader fuer Mod-Antworten LF und CRLF akzeptiert und genau ein CR direkt vor LF als Separator behandelt. CR im Recordinhalt bleibt verboten. Exakte Feldzahl und der kleine ASCII-Schemaumfang vermeiden einen ungeprueften JSON-Parser. Der passive Entwurf begrenzt Laeufe auf 50 Probes, 512 Bytes je Record, 106 Records und 64 KiB je Richtung. Er enthaelt keine ShipAI-Aktion. Datei-/Entity-Serialisierung und Mod-Attach sind nicht umfassend zur Laufzeit bestaetigt; jedes Aktionsschema braucht eine eigene Version und Abnahme.
