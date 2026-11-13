"""Inhalt der eingebauten Anleitung: Trading-Grundlagen, Signale und alle Funktionen.

Jedes Kapitel ist (id, Titel, Gruppe, HTML). Das HTML nutzt nur, was Qt-Textfelder
darstellen können (Überschriften, Absätze, Listen, Tabellen). {T} wird durch das
Tastenkürzel-Zeichen ersetzt (⌘ auf dem Mac, Strg+ unter Windows).
"""

from __future__ import annotations


def _hinweis(text: str) -> str:
    return (f"<table width='100%' cellpadding='10' cellspacing='0' bgcolor='@kasten'>"
            f"<tr><td>{text}</td></tr></table><br>")


KAPITEL: list[tuple[str, str, str, str]] = [

    # ------------------------------------------------------------ Start
    ("start", "Willkommen", "Start", f"""
<h1>Willkommen bei Vyntro</h1>
<p>Vyntro beobachtet Aktien, ETFs und Kryptowährungen und zeigt dir nach <b>festen, offenen
Regeln</b>, ob ein Wert gerade eher nach <b>KAUFEN</b>, <b>HALTEN</b> oder <b>VERKAUFEN</b>
aussieht – mit Begründung, Chart, Prognose-Spanne und einem Rückblick, wie gut die Regel
früher funktioniert hat.</p>
<p>Dazu kommen dein eigenes <b>Depot</b> (Gewinn/Verlust, Dividenden, Steuer-Schätzung),
<b>Alarme</b>, eine <b>Markt-Heatmap</b> mit Filtern und eine <b>Schnellsuche</b>.</p>
{_hinweis("<b>Wichtig:</b> Vyntro handelt nicht und ist keine Anlageberatung. Die Signale "
          "sind einfache Regeln aus Kursdaten – sie liegen oft genug falsch. Kaufen und "
          "verkaufen tust du selbst bei deinem Broker (z. B. Trade Republic). Investiere nur "
          "Geld, dessen Verlust du verkraften kannst.")}
<h3>So nutzt du diese Anleitung</h3>
<ul>
<li>Links findest du alle Kapitel – oben die <b>Grundlagen</b> des Tradings, darunter die
<b>Signale und Charts</b> und zum Schluss jede <b>Funktion</b> der App.</li>
<li>Mit dem Suchfeld über dem Inhaltsverzeichnis findest du Begriffe wie „RSI“ oder
„Dividende“.</li>
<li>Die Anleitung öffnest du jederzeit über das Buch-Symbol oben oder mit {{T}}K →
„Anleitung“.</li>
</ul>
"""),

    ("erste-schritte", "Erste Schritte", "Start", """
<h1>Erste Schritte</h1>
<h3>1. Werte finden</h3>
<p>Tippe oben links in das Suchfeld, z. B. <i>Apple</i>, <i>SAP</i> oder <i>Bitcoin</i>, und
wähle einen Vorschlag. Der Wert öffnet sich in der <b>Detailansicht</b>. Alternativ:
{T}K drücken und tippen.</p>
<h3>2. Merken</h3>
<p>Gefällt dir ein Wert, klicke auf <b>Merken</b> (Stern). Er erscheint dann links unter
<b>Meine</b>. Gesuchte Werte werden <i>nicht</i> automatisch gemerkt.</p>
<h3>3. Signal lesen</h3>
<p>Oben rechts in der Detailansicht steht das Signal laut Regel. Darunter erklärt die Karte
<b>„Warum …?“</b>, welche Indikatoren dafür oder dagegen sprechen.</p>
<h3>4. Depot eintragen</h3>
<p>Wenn du einen Wert besitzt: in der Detailansicht <b>Kauf / Verkauf</b> eintragen – oder
im Depot den <b>Trade-Republic-Export importieren</b>. Dann siehst du Wert und
Gewinn/Verlust in Euro.</p>
<h3>5. Alarm setzen</h3>
<p>Mit <b>Alarm</b> wirst du benachrichtigt, wenn z. B. ein Kurs eine Marke erreicht oder
das Signal wechselt – auch wenn das Fenster geschlossen ist.</p>
"""),

    # ------------------------------------------------------------ Grundlagen
    ("grundlagen", "Wie Trading funktioniert", "Grundlagen", f"""
<h1>Wie Trading funktioniert</h1>
<p>An der Börse werden Anteile von Unternehmen (<b>Aktien</b>), Fonds (<b>ETFs</b>) und andere
Wertpapiere gehandelt. Der <b>Kurs</b> entsteht aus Angebot und Nachfrage: Wollen mehr Leute
kaufen als verkaufen, steigt er – und umgekehrt.</p>
<h3>Der Ablauf eines Kaufs</h3>
<ol>
<li>Du eröffnest ein <b>Depot</b> bei einem Broker (z. B. Trade Republic, Scalable,
Comdirect).</li>
<li>Du überweist Geld auf dein Verrechnungskonto.</li>
<li>Du gibst eine <b>Order</b> auf: welcher Wert, wie viel, zu welchem Preis.</li>
<li>Die Order wird an einem Handelsplatz ausgeführt; danach liegen die Anteile in deinem
Depot.</li>
<li>Beim Verkauf läuft es umgekehrt – der Erlös landet wieder auf dem Konto.</li>
</ol>
<h3>Gewinn entsteht auf zwei Wegen</h3>
<ul>
<li><b>Kursgewinn:</b> Du verkaufst teurer, als du gekauft hast.</li>
<li><b>Ausschüttungen:</b> Viele Unternehmen zahlen <b>Dividenden</b>, viele ETFs schütten
aus (oder legen die Erträge automatisch wieder an – „thesaurierend“).</li>
</ul>
<h3>Traden oder langfristig anlegen?</h3>
<p><b>Traden</b> heißt, häufig zu kaufen und zu verkaufen, um kurzfristige Bewegungen
mitzunehmen. Das ist schwierig: Kosten, Steuern und Fehlentscheidungen fressen schnell den
Gewinn. <b>Langfristiges Anlegen</b> (z. B. ein breiter ETF per Sparplan über viele Jahre)
war historisch für die meisten Privatanleger erfolgreicher. Vyntro zeigt dir beides – im
<b>Backtest</b> jeder Detailansicht siehst du, ob die Regel einfaches Halten geschlagen hätte.</p>
{_hinweis("Faustregel: Verstehe, was du kaufst, streue dein Geld über viele Werte, plane "
          "in Jahren statt Tagen und lege einen Notgroschen beiseite, bevor du investierst.")}
"""),

    ("anlageklassen", "Aktien, ETFs, Krypto", "Grundlagen", """
<h1>Aktien, ETFs und Krypto</h1>
<table width='100%' cellpadding='8' cellspacing='0' border='0'>
<tr><td width='22%'><b>Aktie</b></td><td>Anteil an einem einzelnen Unternehmen. Chance und
Risiko hängen an dieser einen Firma – Kursstürze von 50 % und mehr sind möglich.</td></tr>
<tr><td><b>ETF</b></td><td>Börsengehandelter Fonds, der einen Index nachbildet, z. B. den
MSCI World (rund 1.500 Unternehmen) oder den FTSE All-World. Breit gestreut, günstig,
beliebt für Sparpläne. <i>Thesaurierend</i> = Erträge werden wieder angelegt,
<i>ausschüttend</i> = Erträge werden ausgezahlt.</td></tr>
<tr><td><b>Kryptowährung</b></td><td>Digitale Währungen wie Bitcoin oder Ethereum. Rund um
die Uhr handelbar, sehr starke Schwankungen, keine Dividenden, kein Unternehmen
dahinter.</td></tr>
<tr><td><b>Index</b></td><td>Kennzahl für einen Markt, z. B. <b>DAX</b> (40 große deutsche
Firmen), <b>S&amp;P 500</b> (500 große US-Firmen), <b>Nasdaq</b> (vor allem Technologie).
Einen Index selbst kann man nicht kaufen – nur ETFs, die ihn abbilden.</td></tr>
</table>
<h3>Ticker</h3>
<p>Jeder Wert hat ein Kürzel. Vyntro nutzt die Schreibweise von Yahoo Finance:
<b>AAPL</b> (Apple, USA), <b>SAP.DE</b> (SAP an der Börse Xetra), <b>VWCE.DE</b>
(Vanguard FTSE All-World, Xetra), <b>BTC-USD</b> (Bitcoin in US-Dollar). Beim Broker
erkennst du Wertpapiere meist an der <b>ISIN</b> (z. B. US0378331005 für Apple).</p>
<h3>Währungen</h3>
<p>US-Aktien notieren in US-Dollar. Kaufst du sie in Euro, schwankt dein Ergebnis zusätzlich
mit dem Wechselkurs. Vyntro rechnet dein Depot deshalb immer in Euro um.</p>
"""),

    ("orders", "Orders und Kosten", "Grundlagen", f"""
<h1>Orders und Kosten</h1>
<h3>Ordertypen</h3>
<table width='100%' cellpadding='8' cellspacing='0'>
<tr><td width='24%'><b>Market-Order</b></td><td>Sofort zum aktuellen Kurs kaufen bzw.
verkaufen. Einfach, aber der genaue Preis steht vorher nicht fest.</td></tr>
<tr><td><b>Limit-Order</b></td><td>Nur kaufen, wenn der Kurs <i>höchstens</i> X beträgt
(bzw. nur verkaufen ab <i>mindestens</i> X). Schützt vor schlechten Preisen.</td></tr>
<tr><td><b>Stop-Loss</b></td><td>Automatisch verkaufen, wenn der Kurs unter X fällt –
begrenzt Verluste, kann bei schnellen Bewegungen aber deutlich darunter ausgeführt
werden.</td></tr>
<tr><td><b>Sparplan</b></td><td>Jeden Monat automatisch einen festen Betrag investieren.
Man kauft so mal teurer, mal günstiger (Durchschnittskosten-Effekt).</td></tr>
</table>
<h3>Kosten</h3>
<ul>
<li><b>Ordergebühr:</b> bei Neobrokern oft 1 € pro Order, bei Sparplänen häufig 0 €.</li>
<li><b>Spread:</b> Unterschied zwischen Kauf- und Verkaufskurs – versteckte Kosten, besonders
bei kleinen Werten und außerhalb der Handelszeiten.</li>
<li><b>Laufende Kosten</b> bei ETFs (TER), z. B. 0,2 % pro Jahr.</li>
</ul>
<h3>Handelszeiten</h3>
<p>Xetra handelt werktags von 9:00 bis 17:30 Uhr, die US-Börsen von 15:30 bis 22:00 Uhr
deutscher Zeit. Krypto wird rund um die Uhr gehandelt. Die Home-Seite zeigt, ob Xetra gerade
geöffnet ist.</p>
{_hinweis("Viele kleine Käufe kosten anteilig viel Gebühr: Bei 1 € Gebühr auf 10 € Kaufbetrag "
          "liegst du sofort 10 % im Minus.")}
"""),

    ("risiko", "Risiko und Streuung", "Grundlagen", f"""
<h1>Risiko und Streuung</h1>
<p>Jede Anlage kann an Wert verlieren – einzelne Aktien auch vollständig. Drei Grundsätze
helfen:</p>
<h3>Streuen (Diversifikation)</h3>
<p>Verteile dein Geld auf viele Unternehmen, Branchen und Länder. Ein breiter ETF erledigt
das automatisch. In Vyntro zeigt dir das Depot unter <b>Aufteilung</b>, wie konzentriert
du bist.</p>
<h3>Zeit</h3>
<p>Kurzfristig sind Kurse kaum vorhersehbar. Über viele Jahre gleichen sich Schwankungen eher
aus – Garantie gibt es aber keine.</p>
<h3>Nur entbehrliches Geld</h3>
<p>Investiere kein Geld, das du in den nächsten Jahren brauchst, und keine Kredite.
Gehebelte Produkte (CFDs, Optionsscheine, Knock-outs) können mehr als den Einsatz kosten
oder sehr schnell wertlos werden – Vyntro bildet sie bewusst nicht ab.</p>
<h3>Typische Fehler</h3>
<ul>
<li>Panisch verkaufen, wenn der Markt fällt – und den Wiederanstieg verpassen.</li>
<li>Gewinnern hinterherkaufen, nur weil sie stark gestiegen sind.</li>
<li>Zu viele Orders mit kleinen Beträgen (Gebühren!).</li>
<li>Einer einzelnen Quelle, einem Signal oder einem Social-Media-Tipp blind folgen.</li>
</ul>
{_hinweis("Auch die Signale in Vyntro sind nur ein Hinweis. In der Begründung steht jeweils "
          "die <b>bisherige Trefferquote</b> – sie liegt oft nur knapp über 50 %.")}
"""),

    ("steuern", "Steuern in Deutschland", "Grundlagen", """
<h1>Steuern in Deutschland (kurz)</h1>
<p>Auf Kursgewinne, Zinsen und Dividenden fällt die <b>Abgeltungssteuer</b> an:
25 % plus Solidaritätszuschlag (zusammen 26,375 %), ggf. plus Kirchensteuer.</p>
<ul>
<li><b>Sparerpauschbetrag:</b> 1.000 € pro Jahr bleiben steuerfrei (2.000 € bei
Zusammenveranlagung). Dafür beim Broker einen <b>Freistellungsauftrag</b> einrichten.</li>
<li>Deutsche Broker führen die Steuer automatisch ab – du musst meist nichts tun.</li>
<li><b>Verluste</b> werden mit Gewinnen verrechnet (Aktienverluste nur mit Aktiengewinnen).</li>
<li>Bei Fonds/ETFs gibt es eine <b>Teilfreistellung</b> (z. B. 30 % bei Aktien-ETFs) und
eine jährliche <b>Vorabpauschale</b> bei thesaurierenden Fonds.</li>
<li>Gewinne aus <b>Krypto</b> sind nach einem Jahr Haltedauer in der Regel steuerfrei,
davor gilt die persönliche Einkommensteuer (Freigrenze 1.000 € pro Jahr).</li>
</ul>
<p>Das Depot in Vyntro zeigt eine grobe <b>Steuer-Schätzung</b> für realisierte Gewinne.
Sie ersetzt keine Steuerberatung.</p>
"""),

    # ------------------------------------------------------------ Signale
    ("signale", "So entstehen die Signale", "Signale & Charts", f"""
<h1>So entstehen die Signale</h1>
<p>Vyntro bewertet jeden Wert jeden Tag mit drei Indikatoren. Jeder gibt <b>+1</b> (spricht
fürs Kaufen), <b>−1</b> (spricht fürs Verkaufen) oder <b>0</b> (neutral). Die Summe ist der
<b>Score</b> von −3 bis +3:</p>
<table width='100%' cellpadding='8' cellspacing='0'>
<tr><td width='30%'><b style='color:@gruen'>KAUFEN</b></td><td>Score +2 oder +3 – mindestens
zwei Indikatoren zeigen nach oben.</td></tr>
<tr><td><b style='color:@grau'>HALTEN</b></td><td>Score −1 bis +1 – kein klares Bild.</td></tr>
<tr><td><b style='color:@rot'>VERKAUFEN</b></td><td>Score −2 oder −3 – mindestens zwei
Indikatoren zeigen nach unten.</td></tr>
</table>
<h3>Die drei Indikatoren</h3>
<p><b>Trend</b> – Durchschnitt der letzten 50 Tage gegen den der letzten 200 Tage. Liegt der
50er darüber, gilt der Trend als aufwärts (+1), sonst abwärts (−1). Kreuzt der 50er den
200er nach oben, spricht man vom <i>Golden Cross</i>, nach unten vom <i>Death Cross</i>.</p>
<p><b>RSI</b> (Relative Stärke, 14 Tage) – misst, wie stark die Gewinne gegenüber den
Verlusten der letzten Tage waren, auf einer Skala von 0 bis 100. <b>Unter 30</b> gilt ein
Wert als <i>überverkauft</i> (+1, oft Gegenbewegung nach oben), <b>über 70</b> als
<i>überkauft</i> (−1).</p>
<p><b>MACD</b> – vergleicht einen schnellen mit einem langsamen gleitenden Durchschnitt
(12 und 26 Tage) und dessen Signallinie (9 Tage). Liegt der MACD über der Signallinie,
nimmt der Schwung zu (+1), sonst ab (−1).</p>
<h3>Begründung, Trefferquote, Gegenargumente</h3>
<p>Die Karte <b>„Warum …?“</b> nennt die Gründe für das Signal, was dagegen spricht, wie oft
das Signal bei diesem Wert früher richtig lag und was passieren müsste, damit es wechselt.</p>
{_hinweis("Signale werden aus <b>Tagesschlusskursen</b> berechnet und alle 15 Minuten für deine "
          "Werte neu bewertet. Sie sind bewusst einfach und für alle gleich – keine "
          "persönliche Empfehlung.")}
"""),

    ("charts", "Charts lesen", "Signale & Charts", f"""
<h1>Charts lesen</h1>
<h3>Kerzen</h3>
<p>Jede Kerze steht für einen Tag (bei langen Zeiträumen für eine Woche). Der dicke
<b>Körper</b> reicht vom Eröffnungs- bis zum Schlusskurs, die dünnen <b>Dochte</b> zeigen
Hoch und Tief. <span style='color:@gruen'>Grün</span> = Schlusskurs über Eröffnung,
<span style='color:@rot'>rot</span> = darunter.</p>
<h3>Linien und Markierungen</h3>
<ul>
<li><b>Helle Linie:</b> Durchschnitt der letzten 50 Tage, <b>dunkle Linie:</b> 200 Tage.</li>
<li><b>▲ / ▼</b>: Tage, an denen die Regel früher ein Kauf- bzw. Verkaufssignal gab.</li>
<li><b>Gepunktete Linie</b> quer: aktueller Kurs.</li>
<li><b>RSI</b> unten mit den Zonen unter 30 und über 70.</li>
</ul>
<h3>Zusatzlinien (unten rechts zuschaltbar)</h3>
<ul>
<li><b>Bollinger:</b> 20-Tage-Durchschnitt ± 2 Standardabweichungen – zeigt, wie stark der
Kurs gerade schwankt. Kurse am Rand des Bandes sind ungewöhnlich weit vom Durchschnitt
entfernt.</li>
<li><b>Volumen:</b> wie viele Anteile gehandelt wurden. Starke Bewegungen mit hohem Volumen
gelten als aussagekräftiger.</li>
<li><b>52W:</b> höchster und tiefster Kurs der letzten 12 Monate.</li>
</ul>
<h3>Bedienen</h3>
<ul>
<li>Zeiträume <b>1T</b> und <b>1W</b> zeigen den Verlauf eines bzw. fünf Handelstage.</li>
<li>Mit der Maus über den Chart fahren: Fadenkreuz mit Datum, Kurs und Veränderung.</li>
<li><b>Vergleichen:</b> bis zu drei andere Werte prozentual im selben Chart.</li>
</ul>
"""),

    ("prognose", "Prognose und Backtest", "Signale & Charts", """
<h1>Prognose und Backtest</h1>
<h3>Prognose-Linie</h3>
<p>Die mintfarbene Linie rechts im Chart schreibt den Trend der letzten 12 Monate fort –
aber nur zur <b>Hälfte</b> und höchstens etwa ±25 % pro Jahr, weil Trends meist nachlassen.
Die gestrichelten Linien zeigen die <b>Spannen</b>, in denen der Kurs bei gleicher
Schwankung wie bisher mit 50 % bzw. 80 % Wahrscheinlichkeit liegen würde.</p>
<p>Ist Analystenmeinung verfügbar, zeigt eine gestrichelte Linie zusätzlich das
<b>durchschnittliche Kursziel</b> der Analysten.</p>
<p><b>Wichtig:</b> Das ist eine statistische Fortschreibung, keine Vorhersage. Nachrichten,
Quartalszahlen oder Krisen können den Kurs jederzeit weit aus der Spanne bewegen.</p>
<h3>Backtest</h3>
<p>Der Backtest spielt die Regel über die letzten Jahre durch: investiert bei KAUFEN,
raus bei VERKAUFEN, gehandelt jeweils am Tag <i>nach</i> dem Signal, mit 0,1 % Gebühr pro
Order. Verglichen wird mit <b>einfachem Halten</b> über den ganzen Zeitraum. „Max. Verlust“
ist der größte zwischenzeitliche Rückgang vom Höchststand.</p>
<h3>Was wäre wenn</h3>
<p>Rechnet einen monatlichen Sparplan mit echten Kursen der letzten 1, 3 oder 5 Jahre nach –
ohne Gebühren und Steuern. Ein Rückblick, keine Garantie für die Zukunft.</p>
"""),

    # ------------------------------------------------------------ Funktionen
    ("home", "Home und Watchlist", "Funktionen", """
<h1>Home und Watchlist</h1>
<h3>Home</h3>
<p>Die Startseite zeigt die wichtigsten Märkte (DAX, S&amp;P 500, Nasdaq, Bitcoin, Gold,
EUR/USD), dein Depot, ausgelöste Alarme, die Gewinner und Verlierer unter deinen Werten,
aktuelle Kaufsignale und anstehende Termine. Alles ist anklickbar.</p>
<h3>Watchlist (links)</h3>
<ul>
<li><b>Aktien &amp; ETFs / Krypto:</b> umschalten zwischen den Bereichen.</li>
<li><b>Meine ▾:</b> zwischen eigenen Listen wechseln, neue anlegen, umbenennen, löschen.
Per Rechtsklick → „In Listen“ legst du Werte in mehrere Listen.</li>
<li><b>Sortieren:</b> eigene Reihenfolge (per Ziehen mit der Maus), Name, Tagesänderung,
Signal.</li>
<li><b>Unter 50 €:</b> Werte mit Kaufsignal, deren Stückpreis unter 50 € liegt (Grenze in den
Einstellungen änderbar). Ein niedriger Preis heißt nicht, dass ein Wert günstig ist.</li>
<li><b>Kaufsignale jetzt:</b> alle geprüften Werte, bei denen die Regel KAUFEN zeigt.</li>
<li>Die <b>Mini-Charts</b> zeigen den Verlauf von heute.</li>
</ul>
"""),

    ("depot", "Depot", "Funktionen", """
<h1>Depot</h1>
<p>Vyntro ist nicht mit deinem Broker verbunden – du trägst Käufe und Verkäufe selbst ein
oder importierst sie.</p>
<h3>Käufe und Verkäufe</h3>
<p>In der Detailansicht eines Werts: <b>Kauf / Verkauf</b>. Gib Betrag <i>oder</i> Stückzahl,
den Kurs in Euro, die Gebühr und das Datum ein – so, wie es dein Broker abgerechnet hat.</p>
<h3>Trade Republic importieren</h3>
<ol>
<li>In der Trade-Republic-App bzw. im Web: <b>Profil → Transaktionen exportieren</b>
(CSV).</li>
<li>In Vyntro unter <b>Depot → Trade Republic importieren</b> die Datei wählen.</li>
<li>Prüfen, ob die Ticker stimmen (änderbar), dann <b>übernehmen</b>.</li>
</ol>
<p>Bereits importierte Buchungen werden erkannt – du kannst jederzeit neu exportieren und
importieren.</p>
<h3>Was das Depot zeigt</h3>
<ul>
<li><b>Gewinn/Verlust</b> gesamt und heute – in Euro, inklusive Wechselkurs.</li>
<li><b>Einstand:</b> Durchschnittspreis inklusive Kaufgebühren. Bei Verkäufen wird der
Gewinn mit diesem Durchschnitt berechnet („aus Verkäufen realisiert“).</li>
<li><b>Verlauf</b> seit dem ersten Kauf, im Vergleich zum eingezahlten Geld und zum
MSCI World.</li>
<li><b>Aufteilung</b> nach Werten, Branche, Land, Art.</li>
<li><b>Dividenden</b> pro Jahr (nach der letzten bekannten Dividende).</li>
<li><b>Steuer-Schätzung</b> und <b>CSV-Export</b> für Excel/Numbers.</li>
</ul>
"""),

    ("alarme", "Alarme", "Funktionen", """
<h1>Alarme</h1>
<p>In jeder Detailansicht über <b>Alarm</b> anlegen. Mögliche Bedingungen:</p>
<ul>
<li>Kurs steigt über / fällt unter eine Marke</li>
<li>Steigt / fällt heute um mehr als X %</li>
<li>RSI fällt unter / steigt über einen Wert</li>
<li>Neues 52-Wochen-Hoch / -Tief</li>
<li>Das Signal der Regel ändert sich (z. B. HALTEN → VERKAUFEN)</li>
</ul>
<p>Ausgelöste Alarme melden sich mit einer Systemmitteilung und Ton. Die meisten Alarme
schalten sich danach ab (mit <b>Wieder an</b> reaktivierbar), der Signal-Alarm bleibt aktiv.
Außerdem meldet Vyntro einen Tag vorher, wenn bei deinen Werten <b>Quartalszahlen</b>
anstehen.</p>
<p>Alarme funktionieren, solange Vyntro läuft – auch im Hintergrund. Schalte dafür in den
Einstellungen <b>Autostart</b> und <b>im Hintergrund weiterlaufen</b> ein.</p>
"""),

    ("markt", "Markt: Heatmap und Filter", "Funktionen", """
<h1>Markt: Heatmap und Filter</h1>
<h3>Heatmap</h3>
<p>Jede Kachel ist ein Wert, die Farbe zeigt die Veränderung heute (kräftig grün = stark im
Plus, kräftig rot = stark im Minus). In der Ansicht <b>Depot</b> richtet sich die Größe nach
deinem Anteil. Klick auf eine Kachel öffnet den Wert.</p>
<h3>Filter</h3>
<p>Durchsucht alle geprüften Werte (deine Listen, Depot, DAX 40, große US-Werte, Krypto)
nach Art, Signal, RSI, Dividendenrendite, Kurs und Tagesbewegung. Klick auf eine
Spaltenüberschrift sortiert.</p>
<p>Ein Filter findet Werte, die bestimmte Zahlen erfüllen – er sagt nichts darüber, ob ein
Unternehmen gut ist. Lies dir zu jedem Treffer die Infos und Nachrichten durch.</p>
"""),

    ("bedienung", "Tastenkürzel und Einstellungen", "Funktionen", """
<h1>Tastenkürzel und Einstellungen</h1>
<table width='100%' cellpadding='7' cellspacing='0'>
<tr><td width='28%'><b>{T}K</b></td><td>Schnellsuche: Werte und Befehle</td></tr>
<tr><td><b>{T}1</b></td><td>Home</td></tr>
<tr><td><b>{T}J</b></td><td>Markt</td></tr>
<tr><td><b>{T}D</b></td><td>Depot</td></tr>
<tr><td><b>{T}L</b></td><td>Alarme</td></tr>
<tr><td><b>{T}R</b></td><td>Alle Kurse neu laden</td></tr>
<tr><td><b>{T}F</b></td><td>Suchfeld links</td></tr>
<tr><td><b>{T},</b></td><td>Einstellungen</td></tr>
</table>
<h3>Einstellungen</h3>
<ul>
<li><b>Autostart</b> beim Anmelden und <b>Weiterlaufen im Hintergrund</b> – damit Alarme
immer ankommen.</li>
<li>Was im Symbol in der Menü- bzw. Taskleiste steht (Depotwert oder ein Wert).</li>
<li>Termin-Mitteilungen, Sparerpauschbetrag, Preisgrenze für „Unter 50 €“.</li>
</ul>
"""),

    ("updates", "Updates und Daten", "Funktionen", """
<h1>Updates und Daten</h1>
<h3>Updates</h3>
<p>Vyntro prüft beim Start und alle sechs Stunden, ob es eine neue Version gibt. Dann
erscheint oben <b>„Neue Version …“</b>. Ein Klick zeigt, was neu ist, und <b>Jetzt
aktualisieren</b> lädt und installiert das Update mit Fortschrittsanzeige; danach startet
Vyntro neu. Die aktuelle Version steht unten auf der Home-Seite und in den Einstellungen.</p>
<h3>Woher die Daten kommen</h3>
<ul>
<li>Kurse, Kennzahlen und Termine: <b>Yahoo Finance</b>. Manche Börsen (z. B. Xetra) liefert
Yahoo bis zu 15 Minuten verzögert – das steht dann in der Detailansicht.</li>
<li>Nachrichten: Google News (deutsch) und Yahoo Finance (englisch).</li>
<li>Logos: öffentliche Bildquellen.</li>
</ul>
<h3>Deine Daten</h3>
<p>Listen, Depot, Alarme und Notizen bleiben ausschließlich auf deinem Rechner – unter
Windows in <b>%APPDATA%\\Vyntro</b>, auf dem Mac in
<b>~/Library/Application Support/Trading-Signale</b>. Vyntro hat kein Konto und schickt
nichts davon ins Internet.</p>
"""),
]


def kapitel_html(id_: str, taste: str, farben: dict) -> str:
    for kid, _titel, _gruppe, html in KAPITEL:
        if kid == id_:
            text = html.replace("{T}", taste)
            for k in ("gruen", "rot", "grau", "kasten"):
                text = text.replace(f"@{k}", farben.get(k, "#888"))
            return text
    return ""


def suchen(begriff: str) -> list[str]:
    """IDs der Kapitel, in deren Titel oder Text der Begriff vorkommt."""
    import re
    b = begriff.strip().lower()
    if not b:
        return [k[0] for k in KAPITEL]
    treffer = []
    for kid, titel, gruppe, html in KAPITEL:
        text = re.sub(r"<[^>]+>", " ", html).lower()
        muster = re.compile(r"(?<!\w)" + re.escape(b))  # ab Wortanfang
        if muster.search(titel.lower()) or muster.search(text) or muster.search(gruppe.lower()):
            treffer.append(kid)
    return treffer
