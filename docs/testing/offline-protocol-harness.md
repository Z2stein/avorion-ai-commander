# Offline-Protokolltest

## Umfang

Für die Python-Bridge und den source-only Lua-Protokoll-Injektor liegt eine Offline-Testsuite vor. Beide synchronen Repositories bestehen derzeit 32 Python-Tests (19 Bridge + 13 Injektor). Die Protokolltests verwenden Fake-Peers und temporäre Dateien; Deadline-Tests des Injektorplans verwenden Fake-Uhren und Fake-Kanäle.

Die Suite deckt gültige Protokollabläufe, Session- und Sequenzvalidierung, LF-/CRLF-Zeilenenden einschließlich eines über zwei Reads geteilten CRLF, weiter abgelehnte eingebettete oder doppelte CR-Zeichen und NUL, die 512-Byte-Recordgrenze, fehlerhafte Records, falsche Schiffskennungen, doppelte/wiederholte Nachrichten, Timeout-Behandlung, CLI-Eingabevalidierung sowie den strikt begrenzten Resume-Pfad nach HELLO_ACK ab. Sie führt Avorion nicht aus, parst kein Lua, lädt keine Mod, prüft keine Sandbox-Berechtigungen und belegt keine echte Moddata-IPC.

`--resume-after-hello` ist ausdrücklich opt-in. Das Preflight akzeptiert ausschließlich eine vollständige LF-HELLO-Zeile und das dazu passende einzelne HELLO_ACK mit LF oder CRLF; jeglicher Zusatzrecord oder Zusatzbyte stoppt vor PROBE. Es prüft stabile Dateisnapshots, ist aber kein Lock und garantiert keine Sicherheit gegen concurrente Schreiber. Eine Fortsetzung verlangt einen exklusiven Bridge-Writer und eine im Spiel weiterhin aktive Lua-Session. Die vorhandenen IPC-Logs werden nicht geleert oder rotiert.

## Reihenfolge für einen künftigen Live-Smoke-Test

Bei einem späteren isolierten Lauf muss die Lua-Probe zuerst mit fehlenden oder leeren Kanaldateien initialisieren. Danach `probe_bridge.py --cycles 1` mit einem unabhängig bestätigten Moddata-Pfad des entbehrlichen Testspielstands starten. Ein früherer Bridge-Start schreibt HELLO in den Kanal; die Lua-Initialisierung ist darauf ausgelegt, einen nicht leeren Eingang abzulehnen.

Der Live-Smoke-Test ist ein Plan für eine isolierte Wiederholung; dieser Offline-Harness selbst belegt weder Modladen noch Attach oder Live-Roundtrip. Separat sind 50 passive Bridge-Zyklen in einer aktiven Lua-Session dokumentiert. Der separate Lua-Injektor stoppte beim CRLF-HELLO_ACK vor PROBE; der Offline-Fix und seine Parserfälle belegen keine Avorion-Laufzeit. Technische Isolation und formale M1-Abnahme bleiben offen, bis Isolation, genaue Quellidentität und Wiederholbarkeit in einem frischen Testpfad bestätigt sind. Die Offline-Suite wurde mit `python -m unittest discover -s tests -v` in beiden Repositories ausgeführt: 32/32 Tests bestanden. Siehe [Injektorhinweise](lua-protocol-injector.md), [Projektstatus](../project/status.md) und [Isolationsplan](isolation-plan.md).
