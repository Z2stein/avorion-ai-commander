# Projektanweisungen

## Architektur und Evidenz

- Das Projekt entwickelt einen Avorion-AI-Commander: Eine serverseitige Mod beobachtet ein Schiff, ein separater Prozess trifft begrenzte Entscheidungen, und der Server validiert vorgeschlagene Aktionen.
- Avorion-APIs, Callback-Signaturen und Spielverhalten nicht erfinden. Kennzeichne Aussagen als **BESTÄTIGT** (direkter Beleg), **DOKUMENTIERT** (passende Dokumentation), **PLAUSIBEL** (noch nicht nachgewiesen) oder **GETESTET** (reproduzierbarer Laufzeitnachweis).
- Dokumentation belegt kein Laufzeitverhalten. Empfangene Befehle belegen keine ausgeführte Spielaktion.

## Daten- und Testsicherheit

- Installationsdateien, Workshop-Inhalte und bestehende Spielstände nicht verändern.
- Laufzeittests nur mit einem entbehrlichen Testspielstand in einer nachweislich isolierten Umgebung ausführen.
- Ein laufendes Spiel oder einen Server nicht ohne ausdrückliche Freigabe starten, stoppen oder beeinflussen.
- Betriebssystem- oder Firewall-Einstellungen nicht ohne ausdrückliche Freigabe ändern.
- Projektdateien außerhalb der Spielinstallation halten.

## Qualität und Dokumentation

- Vor Implementierung oder Test die API, Sandbox und Zielspielversion prüfen.
- Für jeden Meilenstein Abnahmekriterien festlegen und offene Fragen sowie nicht ausgeführte Tests dokumentieren.
- Umfangreiche Änderungen nach Möglichkeit unabhängig prüfen lassen.
- Vor einem Commit diese Anweisungen, die Root-README und relevante Unterordner-READMEs lesen; betroffene Dokumentation aktualisieren und Review einholen.
- Eine kurze Commit-Überschrift mit einer Beschreibung der Änderungen verwenden.
