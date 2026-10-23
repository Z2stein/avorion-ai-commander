# Projektstatus

## Evidenzübersicht

- **M0 — Statische Discovery:** Recherche und Testplan liegen vor. Das ist ein Dokumentationsergebnis, kein Laufzeitnachweis.
- **M1 — Nicht nachgewiesen:** Passives Mod-/Bridge-Gerüst und AC|1-Protokollkandidat liegen vor. Dieser öffentliche Snapshot belegt weder Modladen noch Lua/Python-IPC-Roundtrip, exportierten Schiffszustand oder externe Spielaktion.
- **Offline-Tests:** Das Projekt dokumentiert 22 bestandene Python-Tests mit Fake-Peers und temporären Dateien. Sie führen Avorion nicht aus, parsen kein Lua und validieren keine echte Moddata-IPC.
- **Lua:** Nicht geparst oder ausgeführt.
- **M2 und später:** Geplant; keine Schiffssteuerungsaktion ist nachgewiesen.

## Letzter Laufzeitversuch

Ein Startversuch auf einer separaten Testgalaxie mit Avorion 2.5.13 endete vor `Server startup complete` mit `include error: module 'generator' not found`. Derselbe Fehler trat auch mit entfernter Projekt-Modpfadangabe auf. Der genaue Aufrufer und die Ursache sind damit nicht bestimmt; der Fehler wird dem Projekt-Mod nicht zugeschrieben. Es gab keinen Modlade-, IPC- oder Spielaktionsnachweis.

## Hinweise zur M1-Implementierung

Die Bridge akzeptiert ein explizit übergebenes Moddata-Verzeichnis; sie kann nicht selbst feststellen, ob dieses Verzeichnis zu einem isolierten Testspielstand gehört. Die Lua-Probe erwartet bei der Initialisierung fehlende oder leere Kanaldateien. Zuerst die Mod initialisieren, danach die Bridge für einen einzelnen Probe-Zyklus starten. Das Attach-Kommando ist mit leerer fester Test-ID-Allowlist standardmäßig fail-closed. Der `inspect`-Modus soll schreibgeschützten Kontext liefern und den Attach-Zweig umgehen, wurde aber nicht in Avorion ausgeführt.

## Erforderliche Evidenz vor einem Laufzeittest

Einen entbehrlichen Spielstand verwenden und die Trennung von Spielstanddaten, Modkonfiguration, Backups und Netzwerkzugriff nachweisen. Zielspielversion, Modladen, Kommandoerkennung, `Server().folder`-Zuordnung und IPC-Dateiberechtigungen in dieser Umgebung bestätigen. Solange eine Grenze unklar ist, keinen Live-Test ausführen.

Dieser öffentliche Status lässt Hostinventare, lokale Konfiguration, Spielstandnamen, Prozesskennungen, Zeitstempel und Netzwerkdiagnosen absichtlich aus. Aus dieser Auslassung keine Schlussfolgerung über einen konkreten Rechner ziehen.
