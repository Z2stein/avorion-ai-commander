# Offline-Protokolltest

## Umfang

Für die Python-Bridge und den source-only Lua-Protokoll-Injektor liegt eine Offline-Testsuite vor. Das Projekt dokumentiert 22 bestandene Python-Tests. Die Protokolltests verwenden Fake-Peers und temporäre Dateien; Deadline-Tests des Injektorplans verwenden Fake-Uhren und Fake-Kanäle.

Die Suite deckt gültige Protokollabläufe, Session- und Sequenzvalidierung, fehlerhafte Records, falsche Schiffskennungen, doppelte/wiederholte Nachrichten, Timeout-Behandlung und CLI-Eingabevalidierung ab. Sie führt Avorion nicht aus, parst kein Lua, lädt keine Mod, prüft keine Sandbox-Berechtigungen und belegt keine echte Moddata-IPC.

## Reihenfolge für einen künftigen Live-Smoke-Test

Bei einem späteren isolierten Lauf muss die Lua-Probe zuerst mit fehlenden oder leeren Kanaldateien initialisieren. Danach `probe_bridge.py --cycles 1` mit einem unabhängig bestätigten Moddata-Pfad des entbehrlichen Testspielstands starten. Ein früherer Bridge-Start schreibt HELLO in den Kanal; die Lua-Initialisierung ist darauf ausgelegt, einen nicht leeren Eingang abzulehnen.

Der Live-Smoke-Test ist nur ein Plan. Hiermit sind weder Modladen, Attach, Roundtrip, Zustandsausgabe noch Spielaktion belegt. Siehe [Injektorhinweise](lua-protocol-injector.md), [Projektstatus](../project/status.md) und [Isolationsplan](isolation-plan.md).
