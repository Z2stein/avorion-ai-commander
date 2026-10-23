# Offline-Protokolltest

## Umfang

Für die Python-Bridge und den source-only Lua-Protokoll-Injektor liegt eine Offline-Testsuite vor. Beide synchronen Repositories bestehen derzeit 27 Python-Tests (19 Bridge + 8 Injektor). Die Protokolltests verwenden Fake-Peers und temporäre Dateien; Deadline-Tests des Injektorplans verwenden Fake-Uhren und Fake-Kanäle.

Die Suite deckt gültige Protokollabläufe, Session- und Sequenzvalidierung, LF-/CRLF-Zeilenenden, weiter abgelehnte CR-Zeichen innerhalb eines Records, fehlerhafte Records, falsche Schiffskennungen, doppelte/wiederholte Nachrichten, Timeout-Behandlung, CLI-Eingabevalidierung sowie den strikt begrenzten Resume-Pfad nach HELLO_ACK ab. Sie führt Avorion nicht aus, parst kein Lua, lädt keine Mod, prüft keine Sandbox-Berechtigungen und belegt keine echte Moddata-IPC.

`--resume-after-hello` ist ausdrücklich opt-in. Das Preflight akzeptiert ausschließlich eine vollständige LF-HELLO-Zeile und das dazu passende einzelne HELLO_ACK mit LF oder CRLF; jeglicher Zusatzrecord oder Zusatzbyte stoppt vor PROBE. Es prüft stabile Dateisnapshots, ist aber kein Lock und garantiert keine Sicherheit gegen concurrente Schreiber. Eine Fortsetzung verlangt einen exklusiven Bridge-Writer und eine im Spiel weiterhin aktive Lua-Session. Die vorhandenen IPC-Logs werden nicht geleert oder rotiert.

## Reihenfolge für einen künftigen Live-Smoke-Test

Bei einem späteren isolierten Lauf muss die Lua-Probe zuerst mit fehlenden oder leeren Kanaldateien initialisieren. Danach `probe_bridge.py --cycles 1` mit einem unabhängig bestätigten Moddata-Pfad des entbehrlichen Testspielstands starten. Ein früherer Bridge-Start schreibt HELLO in den Kanal; die Lua-Initialisierung ist darauf ausgelegt, einen nicht leeren Eingang abzulehnen.

Der Live-Smoke-Test ist ein Plan für eine weitere isolierte Wiederholung; dieser Offline-Harness selbst belegt weder Modladen noch Attach oder Live-Roundtrip. Zwei passive Ein-Zyklus-Läufe sind separat im Projektstatus dokumentiert; technische Isolation und formale M1-Abnahme bleiben offen. Die formale M1-Abnahme bleibt offen, bis technische Isolation, genaue Quellidentität und Wiederholbarkeit in einem frischen Testpfad bestätigt sind. Die Offline-Suite wurde mit `python -m unittest discover -s tests -v` in beiden Repositories ausgeführt: 27/27 Tests bestanden. Siehe [Injektorhinweise](lua-protocol-injector.md), [Projektstatus](../project/status.md) und [Isolationsplan](isolation-plan.md).
