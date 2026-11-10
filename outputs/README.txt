NHIS 2025 – Projekt 2: Schluckbeschwerden und Einsamkeit
Stand: 6. November 2026

Zuerst 00_Machbarkeit_und_Ergebnisse.html im Browser öffnen.
Der Bericht enthält Stichprobenfluss, fehlende Werte, gewichtete Häufigkeiten,
Haupt- und Sensitivitätsanalysen, Variablenmapping und Grenzen.

01_Analyseplan.txt: vor eigenen Kreuztabellen und Modellen festgelegte Entscheidungen.
02_Analyse.R: vollständige Datenaufbereitung, Prüfungen und Survey-Analyse.
03_R_SessionInfo.txt: tatsächlich verwendete R- und Paketversionen.
04_Download_und_Start.ps1: offizielle Dateien abrufen, SHA-256 prüfen und Analyse starten.
05_Bericht.R: Bericht aus den Ergebnistabellen erzeugen.
tables/: maschinenlesbare Tabellen, tabulatorgetrennt. NA bedeutet fehlend.

Reproduktion unter Windows
Die Dateien müssen in einem Unterordner outputs/ eines Projektordners liegen.
In PowerShell: & ./outputs/04_Download_und_Start.ps1
Bei anderem Installationsort: -Rscript 'Pfad/zur/Rscript.exe' ergänzen.
Netzwerkzugriff ist für erstmalige CDC-Downloads und Paketinstallation erforderlich.
Downloads und R-Pakete landen ausschließlich unter work/ im Projektordner.
Das Startskript bricht bei geänderter CDC-Dateiversion ab, statt still eine neue
Version auszuwerten. Die CRAN-Paketinstallation ist nicht versionsfixiert;
für langfristige Reproduktion die Sitzungsdatei und lokale Bibliothek aufbewahren.

Die zwei ursprünglichen Rohdatenarchive und drei offiziellen PDF-Dokumente
liegen lokal unter work/raw bzw. work/docs. Sie sind weder im Ergebnis-ZIP noch im aktuellen Komplettarchiv
enthalten; der Startcode lädt sie aus offiziellen CDC-Quellen erneut herunter.
work/prepared.rds enthält aufbereitete Individualdaten; work/models.rds enthält
kompakte Modellparameter und Kovarianzen für alle zehn Imputationen.
Individualdaten werden nicht im Bericht oder Ergebnis-ZIP ausgegeben.

Qualitätsprüfung
- Dateidimensionen und drei Referenzhäufigkeiten gegen offizielles Codebook geprüft.
- HHX und Einkommensimputationsschlüssel eindeutig; Verknüpfung vollständig.
- Positive Gewichte, gültige Designvariablen, Skip-Logik geprüft.
- Survey-Design vor der Bildung der Analysedomänen definiert.
- Keine ungewichtete Regression, keine Behandlung der zehn Imputationen als
  zehnfach unabhängige Personen.
- Vollständiger erfolgreicher Lauf und Reproduktionsvergleich der Modellergebnisse.

Ergebnisse sind Assoziationen aus einer Querschnittserhebung, keine klinisch
bestätigten Dysphagiebefunde und kein Kausalnachweis. Literaturprüfung und
Publikationsplanung sind nicht Gegenstand dieses Analysepakets.

Gesamtprojekt: RunAll.ps1 im entpackten Komplettarchiv startet auch die
Erweiterungsanalysen und englischen Abbildungen. Es ist keine lokale
Originaldatenkopie aus outputs/source_data erforderlich. Fruehere Git-Versionen
enthalten noch die damaligen Datenarchive; die Historie bleibt unveraendert.
