"""Inhalt der eingebauten Anleitung: Trading-Grundlagen, Chart-Kurs, Signale, Funktionen
und ein Glossar der Fachbegriffe.

Jedes Kapitel ist (id, Titel, Gruppe, HTML). Das HTML nutzt nur, was Qt-Textfelder
darstellen können (Überschriften, Absätze, Listen, Tabellen). Platzhalter:

- {T} wird durch das Tastenkürzel-Zeichen ersetzt (⌘ auf dem Mac, Strg+ unter Windows).
- @gruen, @rot, @grau, @kasten werden durch die Farben der App ersetzt.
- <img src='kurs:NAME'> zeigt ein Lehrbild aus kursbilder.py; Breite und Höhe setzt
  kapitel_html passend zur verfügbaren Breite.
- Links auf 'anleitung:ID' öffnen ein anderes Kapitel.
- Fett (<b>) erscheint in der Akzentfarbe (Mint) – für Fachbegriffe und Wichtiges.
"""

from __future__ import annotations

import re

KURS = "Chart-Kurs"  # Gruppe der Lektionen


# ------------------------------------------------------------------ Bausteine

def _kasten(text: str, farbe: str = "@gruen", titel: str = "") -> str:
    """Hinweiskasten mit farbigem Balken links."""
    kopf = (f"<p class='kastentitel' style='color:{farbe}'>{titel}</p>" if titel else "")
    return (f"<table width='100%' cellpadding='0' cellspacing='0' class='kasten'><tr>"
            f"<td width='3' bgcolor='{farbe}'></td>"
            f"<td bgcolor='@kasten' style='padding: 12px 16px'>{kopf}{text}</td>"
            f"</tr></table><br>")


def _hinweis(text: str) -> str:
    return _kasten(text)


def _merke(text: str) -> str:
    return _kasten(text, "@gruen", "MERKE")


def _vyntro(text: str) -> str:
    return _kasten(text, "@grau", "SO SIEHST DU ES IN VYNTRO")


def _falle(text: str) -> str:
    return _kasten(text, "@rot", "VORSICHT, FALLE")


def _bild(name: str, unterschrift: str = "") -> str:
    text = f"<p class='bild' align='center'>{unterschrift}</p>" if unterschrift else ""
    return f"<p class='bildzeile' align='center'><img src='kurs:{name}'></p>{text}"


def _lead(text: str) -> str:
    return f"<p class='lead'>{text}</p>"


def _link(kid: str, text: str) -> str:
    return f"<a href='anleitung:{kid}'>{text}</a>"


# ------------------------------------------------------------------ Kapitel

KAPITEL: list[tuple[str, str, str, str]] = [

    # ------------------------------------------------------------ Start
    ("start", "Willkommen", "Start", f"""
<h1>Willkommen bei Vyntro</h1>
<p>Vyntro beobachtet Aktien, ETFs und Kryptowährungen und zeigt dir nach <b>festen, offenen
Regeln</b>, ob ein Wert gerade eher nach <b style='color:@gruen'>KAUFEN</b>, <b style='color:@grau'>HALTEN</b>
oder <b style='color:@rot'>VERKAUFEN</b> aussieht – mit Begründung, Chart, Prognose-Spanne und einem Rückblick, wie gut die Regel
früher funktioniert hat.</p>
<p>Dazu kommen dein eigenes <b>Depot</b> (Gewinn/Verlust, Dividenden, Steuer-Schätzung),
<b>Alarme</b>, eine <b>Markt-Heatmap</b> mit Filtern und eine <b>Schnellsuche</b>.</p>
{_kasten("Vyntro handelt nicht und ist <b>keine Anlageberatung</b>. Die Signale sind einfache "
         "Regeln aus Kursdaten – sie liegen oft genug falsch. Kaufen und verkaufen tust du "
         "selbst bei deinem Broker (z. B. Trade Republic). <b>Investiere nur Geld, dessen "
         "Verlust du verkraften kannst.</b>", "@gruen", "WICHTIG")}
<h3>Neu: der Chart-Kurs</h3>
<p>In elf kurzen Lektionen lernst du, <b>Charts zu lesen</b>: Kerzen, Trends,
Unterstützungen und Widerstände, gleitende Durchschnitte, Volumen, RSI und MACD,
<b>Chartformationen</b> wie Doppelboden oder Schulter-Kopf-Schulter – mit Bildern,
Merksätzen und einer Übung zum Schluss. {_link("kurs", "Zum Kurs-Überblick →")}</p>
<h3>So nutzt du diese Anleitung</h3>
<ul>
<li>Links findest du alle Kapitel – oben die <b>Grundlagen</b> des Tradings, dann den
<b>Chart-Kurs</b>, die <b>Signale</b> von Vyntro, jede <b>Funktion</b> der App und zum
Schluss die {_link("glossar", "Fachbegriffe A–Z")}.</li>
<li><b>Fett und grün</b> markiert sind Fachbegriffe und das, was du dir merken solltest.</li>
<li>Mit dem Suchfeld über dem Inhaltsverzeichnis findest du Begriffe wie „RSI“ oder
„Dividende“. Unterstrichene Wörter sind Links zu anderen Kapiteln.</li>
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
<h3>4. Chart verstehen</h3>
<p>Was die Kerzen, Linien und Muster im Chart bedeuten, lernst du Schritt für Schritt im
<a href='anleitung:kurs'>Chart-Kurs</a>.</p>
<h3>5. Depot eintragen</h3>
<p>Wenn du einen Wert besitzt: in der Detailansicht <b>Kauf / Verkauf</b> eintragen – oder
im Depot den <b>Trade-Republic-Export importieren</b>. Dann siehst du Wert und
Gewinn/Verlust in Euro.</p>
<h3>6. Alarm setzen</h3>
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
{_merke("Verstehe, was du kaufst, <b>streue dein Geld</b> über viele Werte, plane in "
        "<b>Jahren statt Tagen</b> und lege einen Notgroschen beiseite, bevor du investierst.")}
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
{_falle("Viele kleine Käufe kosten anteilig viel Gebühr: Bei 1 € Gebühr auf 10 € Kaufbetrag "
        "liegst du <b>sofort 10 % im Minus</b>.")}
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
<b>Gehebelte Produkte</b> (CFDs, Optionsscheine, Knock-outs) können mehr als den Einsatz kosten
oder sehr schnell wertlos werden – Vyntro bildet sie bewusst nicht ab.</p>
<h3>Typische Fehler</h3>
<ul>
<li>Panisch verkaufen, wenn der Markt fällt – und den Wiederanstieg verpassen.</li>
<li>Gewinnern hinterherkaufen, nur weil sie stark gestiegen sind.</li>
<li>Zu viele Orders mit kleinen Beträgen (Gebühren!).</li>
<li>Einer einzelnen Quelle, einem Signal oder einem Social-Media-Tipp blind folgen.</li>
</ul>
{_merke("Auch die Signale in Vyntro sind nur ein Hinweis. In der Begründung steht jeweils "
        "die <b>bisherige Trefferquote</b> – sie liegt oft nur knapp über 50 %. Wie du "
        "Risiko pro Trade begrenzt, zeigt " + _link("kurs-fallen", "Lektion 10") + ".")}
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

    # ------------------------------------------------------------ Chart-Kurs
    ("kurs", "Kurs-Überblick", KURS, f"""
<h1>Charts lesen lernen</h1>
{_lead("Ein Mini-Kurs in elf Lektionen – vom einzelnen Kerzen-Docht bis zur fertigen "
       "Chartformation. Jede Lektion dauert etwa fünf Minuten.")}
<p>Ein <b>Chart</b> ist ein Bild der Vergangenheit: Er zeigt, wie Käufer und Verkäufer sich
bisher verhalten haben. Wer ihn lesen kann, erkennt <b>Trends</b>, wichtige
<b>Kursmarken</b> und typische <b>Muster</b> – und kann Signale wie die von Vyntro besser
einordnen. Diese Art der Analyse heißt <b>Charttechnik</b> oder <b>technische Analyse</b>.
Ihr Gegenstück ist die <b>Fundamentalanalyse</b>, die auf Umsatz, Gewinn und Bewertung
eines Unternehmens schaut.</p>
<h3>Die Lektionen</h3>
<table width='100%' cellpadding='6' cellspacing='0'>
<tr><td width='8%'><b>1</b></td><td>{_link("kurs-kerzen", "Kerzen lesen")} – woraus eine Kerze
besteht und was sie verrät</td></tr>
<tr><td><b>2</b></td><td>{_link("kurs-kerzenmuster", "Kerzenmuster")} – Doji, Hammer,
Shooting Star, Engulfing</td></tr>
<tr><td><b>3</b></td><td>{_link("kurs-trend", "Trends erkennen")} – höhere Hochs, tiefere
Tiefs, Trendlinien</td></tr>
<tr><td><b>4</b></td><td>{_link("kurs-unterstuetzung", "Unterstützung und Widerstand")} –
Böden, Decken, Ausbrüche</td></tr>
<tr><td><b>5</b></td><td>{_link("kurs-durchschnitte", "Gleitende Durchschnitte")} –
50 und 200 Tage, Golden Cross</td></tr>
<tr><td><b>6</b></td><td>{_link("kurs-volumen", "Volumen")} – wie viel Kraft hinter einer
Bewegung steckt</td></tr>
<tr><td><b>7</b></td><td>{_link("kurs-indikatoren", "RSI, MACD, Bollinger")} – Indikatoren
richtig deuten, Divergenzen</td></tr>
<tr><td><b>8</b></td><td>{_link("kurs-umkehr", "Umkehrformationen")} – Doppelboden,
Doppeltop, Schulter-Kopf-Schulter</td></tr>
<tr><td><b>9</b></td><td>{_link("kurs-fortsetzung", "Fortsetzungsformationen")} – Flaggen,
Dreiecke, Kurslücken</td></tr>
<tr><td><b>10</b></td><td>{_link("kurs-fallen", "Zeitebenen, Fallen, Risiko")} – Denkfehler
vermeiden, Chance-Risiko-Verhältnis</td></tr>
<tr><td><b>11</b></td><td>{_link("kurs-uebung", "Checkliste und Übung")} – einen Chart in
sechs Schritten lesen, Muster erkennen</td></tr>
</table>
<br>
{_merke("Charttechnik arbeitet mit <b>Wahrscheinlichkeiten, nicht mit Gewissheiten</b>. "
        "Kein Muster funktioniert immer – es verschiebt nur die Chancen ein wenig. Die Bilder "
        "im Kurs sind bewusst sauber gezeichnet; echte Charts sind unordentlicher.")}
<p>Bereit? {_link("kurs-kerzen", "Los geht's mit Lektion 1: Kerzen lesen →")}</p>
"""),

    ("kurs-kerzen", "1. Kerzen lesen", KURS, f"""
<h1>Kerzen lesen</h1>
{_lead("Du lernst, woraus eine Kerze besteht und was sie über Käufer und Verkäufer "
       "verrät.")}
<p>Ein Chart zeigt waagerecht die <b>Zeit</b> und senkrecht den <b>Preis</b>. Die
beliebteste Darstellung sind <b>Kerzen</b> <i>(Candlesticks)</i>: Jede Kerze fasst einen
Zeitabschnitt zusammen – im Tageschart einen Handelstag, im Wochenchart eine Woche.</p>
{_bild("kerze", "Aufbau einer Kerze: Der Körper zeigt Eröffnung und Schluss, die Dochte Hoch "
       "und Tief.")}
<h3>Vier Preise pro Kerze</h3>
<table width='100%' cellpadding='7' cellspacing='0'>
<tr><td width='30%'><b>Eröffnung</b> <i>(Open)</i></td><td>erster Kurs des Zeitabschnitts</td></tr>
<tr><td><b>Hoch</b> <i>(High)</i></td><td>höchster Kurs, oberes Ende des Dochts</td></tr>
<tr><td><b>Tief</b> <i>(Low)</i></td><td>tiefster Kurs, unteres Ende des Dochts</td></tr>
<tr><td><b>Schluss</b> <i>(Close)</i></td><td>letzter Kurs – der wichtigste, weil auf ihm die
meisten Berechnungen beruhen</td></tr>
</table>
<p>Zusammen heißen sie <b>OHLC</b>. Der dicke <b>Körper</b> reicht von Eröffnung bis Schluss,
die dünnen <b>Dochte</b> <i>(auch Schatten oder Lunten)</i> bis zum Hoch und Tief.</p>
<h3>Was eine Kerze verrät</h3>
<ul>
<li><b>Langer grüner Körper:</b> Die Käufer hatten fast den ganzen Tag die Oberhand.</li>
<li><b style='color:@rot'>Langer roter Körper:</b> Die Verkäufer haben dominiert.</li>
<li><b>Kleiner Körper:</b> Unentschlossenheit – keine Seite hat gewonnen.</li>
<li><b>Langer oberer Docht:</b> Der Kurs war oben, wurde aber wieder heruntergedrückt.
Man sagt: Der höhere Preis wurde <b>abgelehnt</b>.</li>
<li><b>Langer unterer Docht:</b> Der Kurs fiel, aber Käufer haben ihn zurückgeholt.</li>
</ul>
<p>Ein <b>Linienchart</b> verbindet nur die Schlusskurse. Er ist übersichtlicher, zeigt aber
nicht, wie umkämpft ein Tag war.</p>
{_merke("Die Farbe sagt nur, ob der Kurs <b>innerhalb dieser Kerze</b> gestiegen ist "
        "(Schluss über Eröffnung). Eine grüne Kerze kann trotzdem unter dem Schluss des Vortags "
        "liegen – etwa wenn der Kurs morgens tief eröffnet und sich dann etwas erholt hat.")}
{_vyntro("In der Detailansicht ist jede Kerze ein Tag. Bei <b>3J</b> und <b>Max</b> fasst "
         "Vyntro die Tage zu <b>Wochenkerzen</b> zusammen, damit sie lesbar bleiben. Fahr mit "
         "der Maus über den Chart: Das Fadenkreuz zeigt Datum, Kurs und Veränderung.")}
"""),

    ("kurs-kerzenmuster", "2. Kerzenmuster", KURS, f"""
<h1>Kerzenmuster</h1>
{_lead("Du lernst fünf bekannte Muster aus einer oder zwei Kerzen, die eine Wende "
       "ankündigen können.")}
<p>Zwei Wörter begegnen dir überall: <b>bullish</b> heißt „spricht für steigende Kurse“ (der
Bulle stößt mit den Hörnern nach oben), <b>bearish</b> heißt „spricht für fallende Kurse“
(der Bär schlägt mit der Tatze nach unten). Auf Deutsch auch <b>bullisch</b> und
<b>bärisch</b>.</p>
{_bild("kerzenmuster", "Das jeweilige Muster ist eingerahmt, davor steht die Bewegung, in der "
       "es auftaucht.")}
<table width='100%' cellpadding='8' cellspacing='0'>
<tr><td width='26%' valign='top'><b>Doji</b></td><td>Eröffnung und Schluss fast gleich, der
Körper ist nur ein Strich. Käufer und Verkäufer halten sich die Waage. Nach einem langen
Trend ein <b>Warnzeichen</b>: Der Schwung ist weg.</td></tr>
<tr><td valign='top'><b>Hammer</b></td><td>Kleiner Körper oben, langer unterer Docht
(mindestens doppelt so lang wie der Körper). Taucht er <b>nach einem Fall</b> auf, haben
Käufer einen Ausverkauf abgefangen – mögliche Wende nach oben.</td></tr>
<tr><td valign='top'><b>Shooting Star</b><br><i>(Sternschnuppe)</i></td><td>Das Gegenstück:
kleiner Körper unten, langer oberer Docht, <b>nach einem Anstieg</b>. Der Ausflug nach oben
wurde abverkauft – mögliche Wende nach unten.</td></tr>
<tr><td valign='top'><b>Bullish Engulfing</b><br><i>(bullische Umhüllende)</i></td><td>Nach
roten Kerzen folgt eine große grüne, deren Körper den Körper der Vortageskerze komplett
umschließt. Die Käufer haben übernommen.</td></tr>
<tr><td valign='top'><b>Bearish Engulfing</b><br><i>(bärische Umhüllende)</i></td><td>Nach
einem Anstieg umschließt eine große rote Kerze die grüne davor. Die Verkäufer haben
übernommen.</td></tr>
</table>
<br>
{_merke("Kerzenmuster zählen nur <b>an wichtigen Stellen</b>: nach einem langen Trend, an einer "
        "Unterstützung oder einem Widerstand (" + _link("kurs-unterstuetzung", "Lektion 4") +
        "). Und: <b>Warte auf die Bestätigung</b> – erst wenn die nächste Kerze in die neue "
        "Richtung läuft, ist das Muster etwas wert.")}
{_falle("Mitten in einer ruhigen Seitwärtsphase findest du ständig „Dojis“ und „Hämmer“. "
        "Dort bedeuten sie meist <b>gar nichts</b>.")}
"""),

    ("kurs-trend", "3. Trends erkennen", KURS, f"""
<h1>Trends erkennen</h1>
{_lead("Du lernst die wichtigste Frage bei jedem Chart zu beantworten: Wohin geht die Reise "
       "gerade?")}
<p>Kurse bewegen sich nie in gerader Linie, sondern in <b>Wellen</b>. Entscheidend ist, wie
die Hochs und Tiefs dieser Wellen zueinander liegen:</p>
{_bild("trends", "HH = höheres Hoch, HT = höheres Tief, TH = tieferes Hoch, TT = tieferes Tief.")}
<ul>
<li><b>Aufwärtstrend:</b> Jedes Hoch liegt höher als das vorige, und jedes Tief auch –
<b>höhere Hochs und höhere Tiefs</b>.</li>
<li><b>Abwärtstrend:</b> <b>tiefere Hochs und tiefere Tiefs</b>.</li>
<li><b>Seitwärtsphase</b> <i>(Range, Konsolidierung)</i>: Der Kurs pendelt zwischen einem
Boden und einer Decke, ohne klare Richtung.</li>
</ul>
<h3>Trendlinien zeichnen</h3>
<p>Eine <b>Trendlinie</b> verbindet im Aufwärtstrend mindestens zwei <b>Tiefs</b>, im
Abwärtstrend mindestens zwei <b>Hochs</b>. Je öfter der Kurs eine Linie berührt und wieder
abprallt, desto bedeutender ist sie. Fällt der Kurs deutlich durch die Linie, spricht man vom
<b>Trendbruch</b> – ein Warnzeichen, aber noch keine sichere Umkehr.</p>
<h3>Korrekturen gehören dazu</h3>
<p>Auch im besten Aufwärtstrend fällt der Kurs zwischendurch. Solche Gegenbewegungen heißen
<b>Korrektur</b> oder <b>Rücksetzer</b> <i>(Pullback)</i>. Sie sind normal, solange das neue
Tief über dem vorigen bleibt.</p>
{_merke("Ein Aufwärtstrend ist intakt, <b>solange höhere Tiefs entstehen</b>. Erst wenn ein Tief "
        "unter das vorige fällt, ist er angeschlagen. Die alte Börsenregel <b>„The trend is "
        "your friend“</b> heißt: Mit dem Trend zu handeln hat bessere Chancen als dagegen.")}
{_vyntro("Schalte unter dem Chart den Zeitraum um: Bei <b>1J</b> oder <b>3J</b> siehst du den "
         "großen Trend, bei <b>1M</b> oder <b>3M</b> die aktuellen Wellen. Beide können sich "
         "widersprechen – mehr dazu in " + _link("kurs-fallen", "Lektion 10") + ".")}
"""),

    ("kurs-unterstuetzung", "4. Unterstützung & Widerstand", KURS, f"""
<h1>Unterstützung und Widerstand</h1>
{_lead("Du lernst, wo Kurse gern abprallen, was ein Ausbruch ist und warum alte Decken zu "
       "neuen Böden werden.")}
{_bild("unterstuetzung", "Der Kurs pendelt zwischen Boden und Decke, bricht dann nach oben aus "
       "und testet die alte Decke von oben.")}
<p>Eine <b>Unterstützung</b> <i>(Support)</i> ist ein Kursbereich, an dem Käufer früher
eingestiegen sind und den Fall gestoppt haben – ein <b>Boden</b>. Ein <b>Widerstand</b>
<i>(Resistance)</i> ist das Gegenstück: eine <b>Decke</b>, an der Verkäufer den Anstieg
gebremst haben.</p>
<p>Warum funktioniert das? Weil sich Menschen an Preise erinnern. Wer bei 60 € gekauft hat
und dann ins Minus gerutscht ist, verkauft oft erleichtert, sobald der Kurs wieder bei 60 €
ist. Wer bei 40 € zu spät kam, kauft gern, wenn der Kurs dort wieder ankommt.</p>
<h3>Ausbruch, Rücktest, Rollentausch</h3>
<ul>
<li><b>Ausbruch</b> <i>(Breakout)</i>: Der Kurs schließt klar über einem Widerstand oder unter
einer Unterstützung. Oft beginnt damit eine neue Bewegung.</li>
<li><b>Rücktest</b> <i>(Retest)</i>: Nach dem Ausbruch kommt der Kurs häufig noch einmal zur
durchbrochenen Marke zurück.</li>
<li><b>Rollentausch:</b> Ein durchbrochener Widerstand wird zur neuen Unterstützung – und eine
durchbrochene Unterstützung zum neuen Widerstand.</li>
<li><b>Fehlausbruch</b> <i>(Fakeout)</i>: Der Kurs springt kurz über die Marke und fällt gleich
wieder zurück. Wer dort gekauft hat, sitzt in der <b>Bullenfalle</b> (nach unten: die
<b>Bärenfalle</b>).</li>
</ul>
<h3>Wo du solche Marken findest</h3>
<ul>
<li>frühere <b>Hochs und Tiefs</b>, an denen der Kurs mehrfach gedreht hat</li>
<li><b>runde Zahlen</b> wie 100 €, 50.000 $ bei Bitcoin oder 20.000 Punkte im DAX</li>
<li>das <b>52-Wochen-Hoch und -Tief</b></li>
<li><b>gleitende Durchschnitte</b> – sie wirken als „bewegliche“ Unterstützung
(<a href='anleitung:kurs-durchschnitte'>Lektion 5</a>)</li>
</ul>
{_merke("Unterstützung und Widerstand sind <b>Zonen, keine exakten Linien</b>. Je öfter eine "
        "Marke gehalten hat, desto wichtiger ist sie. Ein Ausbruch zählt erst mit einem "
        "<b>Schlusskurs jenseits der Marke</b> – nicht mit einem kurzen Docht.")}
{_vyntro("Schalte unter dem Chart <b>52W</b> ein, dann siehst du Jahreshoch und -tief als "
         "Linien. Mit <b>Alarm → Kurs steigt über / fällt unter</b> lässt du dich melden, "
         "sobald eine Marke erreicht ist.")}
"""),

    ("kurs-durchschnitte", "5. Gleitende Durchschnitte", KURS, f"""
<h1>Gleitende Durchschnitte</h1>
{_lead("Du lernst, wie Durchschnittslinien das Auf und Ab glätten und was Golden Cross und "
       "Death Cross bedeuten.")}
<p>Ein <b>gleitender Durchschnitt</b> <i>(Moving Average, kurz MA oder SMA)</i> ist der
Mittelwert der letzten X Schlusskurse. Jeden Tag fällt der älteste Kurs heraus und der neueste
kommt dazu – so „gleitet“ die Linie mit und <b>glättet</b> das tägliche Zickzack.</p>
<ul>
<li>Die <b>50-Tage-Linie</b> zeigt den mittelfristigen Trend (etwa ein Vierteljahr).</li>
<li>Die <b>200-Tage-Linie</b> zeigt den langfristigen Trend (etwa ein Börsenjahr). Viele
Anleger nutzen sie als Gesundheitscheck: <b>Kurs über der 200-Tage-Linie</b> gilt als stark,
darunter als schwach.</li>
</ul>
{_bild("durchschnitte", "Die schnelle 50-Tage-Linie kreuzt die langsame 200-Tage-Linie erst "
       "nach unten, später wieder nach oben.")}
<h3>Golden Cross und Death Cross</h3>
<p>Kreuzt die 50-Tage-Linie die 200-Tage-Linie <b>von unten nach oben</b>, heißt das
<b>Golden Cross</b> – der mittelfristige Trend hat den langfristigen überholt. Das
Gegenteil, ein Kreuzen <b>nach unten</b>, ist das <b>Death Cross</b>.</p>
<h3>Stärken und Schwächen</h3>
<ul>
<li>In Trends wirken Durchschnitte als <b>dynamische Unterstützung</b> bzw. Widerstand: Der Kurs
prallt oft an der 50-Tage-Linie ab.</li>
<li>Durchschnitte <b>hinken immer hinterher</b> <i>(nachlaufend, englisch „lagging“)</i>. Wenn
das Golden Cross kommt, ist ein Teil des Anstiegs schon vorbei.</li>
<li>In Seitwärtsphasen kreuzen sich die Linien ständig hin und her und liefern viele
<b>Fehlsignale</b>.</li>
</ul>
<p>Neben dem einfachen Durchschnitt gibt es den <b>exponentiellen Durchschnitt</b>
<i>(EMA)</i>, der jüngere Kurse stärker gewichtet und schneller reagiert. Auf ihm beruht der
MACD (<a href='anleitung:kurs-indikatoren'>Lektion 7</a>).</p>
{_merke("Durchschnitte zeigen, <b>was war</b>, nicht was kommt. Sie <b>bestätigen</b> Trends – "
        "vorhersagen können sie sie nicht.")}
{_vyntro("Im Chart ist die <b>helle Linie</b> der 50-Tage- und die <b>dunkle Linie</b> der "
         "200-Tage-Durchschnitt. Liegt die helle über der dunklen, gibt der Trend-Indikator "
         "+1 – siehe " + _link("signale", "So entstehen die Signale") + ".")}
"""),

    ("kurs-volumen", "6. Volumen", KURS, f"""
<h1>Volumen</h1>
{_lead("Du lernst, am Handelsvolumen zu erkennen, wie viel Überzeugung hinter einer "
       "Bewegung steckt.")}
<p>Das <b>Volumen</b> ist die Zahl der gehandelten Anteile in einem Zeitabschnitt. Steigt ein
Kurs, während nur wenige handeln, ist das wenig aussagekräftig. Steigt er, während sehr viele
kaufen, steckt <b>echtes Interesse</b> dahinter.</p>
{_bild("volumen", "Unten die Volumenbalken: ruhig in der Seitwärtsphase, ein Ausschlag beim "
       "Ausbruch.")}
<h3>Vier Faustregeln</h3>
<ul>
<li><b>Ausbruch mit hohem Volumen</b> ist glaubwürdiger als einer mit wenig Volumen.</li>
<li><b>Steigender Kurs bei sinkendem Volumen:</b> Der Anstieg verliert an Kraft.</li>
<li><b>Riesiges Volumen nach langem Fall</b> kann einen <b>Ausverkauf</b> <i>(Kapitulation)</i>
markieren – die letzten Verkäufer geben auf, oft nahe am Tief.</li>
<li>In <b>Seitwärtsphasen</b> ist das Volumen meist niedrig; der Markt wartet ab.</li>
</ul>
<p>Viel Volumen bedeutet auch hohe <b>Liquidität</b>: Du kannst leicht kaufen und verkaufen,
der <b>Spread</b> zwischen Kauf- und Verkaufskurs ist klein.</p>
{_merke("Volumen <b>bestätigt</b> Kursbewegungen. Frag bei jedem Ausbruch: Haben dabei "
        "<b>deutlich mehr</b> Leute gehandelt als an normalen Tagen?")}
{_falle("Das Volumen stammt von einer Datenquelle bzw. einem Handelsplatz – bei Krypto wird "
        "an vielen Börsen gleichzeitig gehandelt. Vergleiche das Volumen deshalb <b>nur mit sich "
        "selbst</b> (heute gegenüber den letzten Wochen), nicht zwischen verschiedenen Werten.")}
{_vyntro("Schalte unter dem Chart <b>Volumen</b> ein. Bei Wochenkerzen (3J, Max) zeigt jeder "
         "Balken das Volumen einer Woche.")}
"""),

    ("kurs-indikatoren", "7. RSI, MACD, Bollinger", KURS, f"""
<h1>RSI, MACD und Bollinger in der Praxis</h1>
{_lead("Du lernst, was Indikatoren können, wo sie täuschen und wie du eine Divergenz "
       "erkennst.")}
<p>Ein <b>Indikator</b> ist eine Hilfslinie, die aus den Kursen berechnet wird. Indikatoren,
die in einem festen Bereich hin- und herschwingen (wie der RSI zwischen 0 und 100), heißen
<b>Oszillatoren</b>. Sie messen vor allem das <b>Momentum</b> – den Schwung einer
Bewegung.</p>
<h3>RSI: überkauft heißt nicht „muss fallen“</h3>
<p>Der <b>RSI</b> <i>(Relative Strength Index)</i> vergleicht die Gewinne der letzten 14 Tage
mit den Verlusten. <b>Über 70</b> gilt ein Wert als <b>überkauft</b>, <b>unter 30</b> als
<b>überverkauft</b>. Wichtig: In einem starken Aufwärtstrend kann der RSI <b>wochenlang über
70</b> bleiben, während der Kurs weiter steigt. Überkauft heißt nur „ist schnell gestiegen“.</p>
<h3>Divergenz: wenn Kurs und Indikator sich widersprechen</h3>
{_bild("divergenz", "Bärische Divergenz: Der Kurs steigt auf ein neues Hoch, der RSI schafft "
       "das nicht mehr.")}
<p>Macht der Kurs ein <b>höheres Hoch</b>, der RSI aber ein <b>tieferes Hoch</b>, spricht man
von einer <b>bärischen Divergenz</b>: Der Kurs steigt noch, aber mit immer weniger Kraft. Das
Gegenstück, die <b>bullische Divergenz</b>, entsteht am Boden: Der Kurs macht ein tieferes
Tief, der RSI ein höheres. Divergenzen kündigen oft eine <b>Pause oder Wende</b> an – aber
nicht, wann sie kommt.</p>
<h3>MACD: Schwung im Vergleich</h3>
<p>Der <b>MACD</b> ist die Differenz zweier exponentieller Durchschnitte (12 und 26 Tage).
Seine eigene 9-Tage-Linie heißt <b>Signallinie</b>.</p>
<ul>
<li><b>MACD kreuzt die Signallinie nach oben:</b> Der Schwung nimmt zu.</li>
<li><b>MACD über der Nulllinie:</b> Der kurze Schnitt liegt über dem langen – der kurzfristige
Trend zeigt nach oben.</li>
</ul>
<h3>Bollinger-Bänder: Ruhe vor dem Sturm</h3>
{_bild("bollinger", "Erst zieht sich das Band zusammen (Squeeze), dann folgt eine starke "
       "Bewegung.")}
<p>Die <b>Bollinger-Bänder</b> liegen zwei <b>Standardabweichungen</b> über und unter dem
20-Tage-Durchschnitt. Die meiste Zeit bleibt der Kurs innerhalb. Sie zeigen die
<b>Volatilität</b> – wie stark der Kurs schwankt:</p>
<ul>
<li><b>Squeeze:</b> Das Band wird sehr eng. Nach solchen ruhigen Phasen folgt oft eine große
Bewegung – in welche Richtung, sagt das Band nicht.</li>
<li>In starken Trends <b>läuft der Kurs am Band entlang</b>. Ein Kurs am oberen Band ist dann
kein Verkaufsgrund, sondern ein Zeichen von Stärke.</li>
</ul>
{_merke("Indikatoren werden aus dem Kurs berechnet – sie enthalten <b>keine neue "
        "Information</b>, nur eine andere Sicht darauf. Am stärksten sind sie, wenn sie zu "
        "Trend, Marken und Volumen passen.")}
{_vyntro("Der <b>RSI</b> steht unter dem Chart, mit den Zonen unter 30 und über 70. Den "
         "<b>MACD</b> findest du als Karte unter dem Chart, <b>Bollinger</b> schaltest du unten "
         "rechts zu. RSI und MACD fließen in den Score ein – " +
         _link("signale", "So entstehen die Signale") + ".")}
"""),

    ("kurs-umkehr", "8. Umkehrformationen", KURS, f"""
<h1>Umkehrformationen</h1>
{_lead("Du lernst die bekanntesten Muster, an denen ein Trend kippt: Doppelboden, Doppeltop "
       "und Schulter-Kopf-Schulter.")}
<p>Eine <b>Chartformation</b> ist ein typisches Kursbild, das immer wieder auftaucht, weil
Menschen in ähnlichen Lagen ähnlich handeln. <b>Umkehrformationen</b> zeigen, dass ein Trend
die Richtung wechseln könnte. Allen gemeinsam ist eine <b>Nackenlinie</b> – die Marke, deren
Bruch die Formation erst bestätigt.</p>
<h3>Doppelboden (W) und Doppeltop (M)</h3>
{_bild("doppelboden", "Doppelboden: zwei Tiefs auf etwa gleicher Höhe, Ausbruch über die "
       "Nackenlinie, Kursziel per Faustregel.")}
<p>Beim <b>Doppelboden</b> fällt der Kurs zweimal auf etwa dasselbe Tief und prallt beide Male
ab – die Verkäufer schaffen es nicht tiefer. Das Hoch dazwischen ist die
<b>Nackenlinie</b>. Erst wenn der Kurs <b>über der Nackenlinie schließt</b>, ist der
Doppelboden fertig.</p>
<p>Der <b>Doppeltop</b> ist das Spiegelbild nach einem Anstieg: zwei Hochs auf gleicher Höhe,
dann der Bruch <b>unter</b> die Nackenlinie.</p>
<p><b>Kursziel-Faustregel:</b> Miss die Höhe der Formation (Tief bis Nackenlinie) und trage sie
vom Ausbruchspunkt in Ausbruchsrichtung ab.</p>
<h3>Schulter-Kopf-Schulter</h3>
{_bild("skf", "Drei Hochs, das mittlere am höchsten. Der Bruch der Nackenlinie bestätigt die "
       "Wende.")}
<p>Die <b>Schulter-Kopf-Schulter-Formation</b> <i>(SKS, englisch Head and Shoulders)</i>
besteht aus drei Hochs: Die <b>linke Schulter</b>, der höhere <b>Kopf</b> und die
<b>rechte Schulter</b>, die das Kopf-Hoch nicht mehr erreicht – den Käufern geht die Puste aus.
Die Nackenlinie verbindet die beiden Tiefs dazwischen. Bricht der Kurs darunter, gilt die
Formation als Signal für eine <b>Trendwende nach unten</b>.</p>
<p>Spiegelverkehrt am Boden heißt sie <b>inverse Schulter-Kopf-Schulter</b> – ein Signal für
eine Wende nach oben.</p>
{_merke("Eine Formation ist erst fertig, wenn die <b>Nackenlinie gebrochen</b> ist – am besten "
        "mit Schlusskurs und erhöhtem Volumen. Vorher ist sie nur eine Vermutung: Viele "
        "vermeintliche Doppelböden werden zu einem dritten, tieferen Tief.")}
{_falle("Kursziele aus Formationen sind <b>Faustregeln, keine Versprechen</b>. Oft wird das Ziel "
        "nicht erreicht, manchmal weit übertroffen.")}
"""),

    ("kurs-fortsetzung", "9. Fortsetzungsformationen", KURS, f"""
<h1>Fortsetzungsformationen und Kurslücken</h1>
{_lead("Du lernst Muster, bei denen ein Trend nur Luft holt – und was eine Kurslücke "
       "bedeutet.")}
<p><b>Fortsetzungsformationen</b> sind Verschnaufpausen in einem Trend. Danach geht es häufig
in die alte Richtung weiter.</p>
<h3>Flagge und Wimpel</h3>
{_bild("flagge", "Bullenflagge: steiler Anstieg (Fahnenstange), kurze Pause leicht gegen den "
       "Trend (Flagge), dann Ausbruch.")}
<p>Erst steigt der Kurs steil – das ist die <b>Fahnenstange</b>. Dann pendelt er einige Tage in
einem kleinen, leicht abwärts geneigten Kanal – die <b>Flagge</b>. Bricht er aus dem Kanal nach
oben aus, setzt sich der Trend oft fort. Ist die Pause statt eines Kanals ein kleines Dreieck,
heißt das Muster <b>Wimpel</b>. Im Abwärtstrend gibt es dasselbe spiegelverkehrt
(<b>Bärenflagge</b>).</p>
<h3>Dreiecke</h3>
{_bild("dreiecke", "Bei Dreiecken laufen die Schwankungen zusammen, bis der Kurs ausbricht.")}
<ul>
<li><b>Aufsteigendes Dreieck:</b> flache Decke, steigende Tiefs. Die Käufer werden immer
ungeduldiger – Ausbruch nach oben ist wahrscheinlicher.</li>
<li><b>Absteigendes Dreieck:</b> flacher Boden, fallende Hochs. Eher bärisch.</li>
<li><b>Symmetrisches Dreieck:</b> beide Linien laufen zusammen. Die Richtung ist offen; etwas
häufiger setzt sich der vorherige Trend fort – verlass dich nicht darauf.</li>
</ul>
<h3>Kurslücken (Gaps)</h3>
{_bild("gap", "Eine Kurslücke entsteht, wenn der Kurs deutlich über dem Hoch des Vortags "
       "eröffnet.")}
<p>Eine <b>Kurslücke</b> <i>(Gap)</i> entsteht, wenn der Kurs deutlich anders eröffnet, als
er am Vortag geschlossen hat – meist wegen Nachrichten über Nacht, etwa
<b>Quartalszahlen</b>. Eine Lücke mit hohem Volumen beim Ausbruch aus einer Formation kann der
Start eines neuen Trends sein. Viele Lücken werden später wieder <b>geschlossen</b> (der Kurs
läuft in den Bereich zurück) – längst aber nicht alle.</p>
{_merke("Fortsetzungsformationen sind <b>kurze Pausen</b> – meist ein paar Tage bis wenige "
        "Wochen. Dauert die „Pause“ viel länger, ist es eher eine neue Seitwärtsphase. Auch "
        "hier gilt: <b>erst der Ausbruch zählt</b>.")}
"""),

    ("kurs-fallen", "10. Zeitebenen, Fallen, Risiko", KURS, f"""
<h1>Zeitebenen, Denkfallen und Risiko</h1>
{_lead("Du lernst, warum derselbe Chart je nach Zeitraum anders aussieht, welche Denkfehler "
       "fast jeder macht und wie du dein Risiko begrenzt.")}
<h3>Zeitebenen</h3>
<p>Die <b>Zeitebene</b> <i>(Timeframe)</i> ist der Zeitraum, den du betrachtest. Ein
„Abwärtstrend“ im 1-Monats-Chart kann im 3-Jahres-Chart nur eine kleine Korrektur in einem
großen Aufwärtstrend sein. Deshalb: <b>von groß nach klein</b> lesen.</p>
<ol>
<li><b>Lang</b> (1J, 3J): Wie ist der große Trend? Wo liegen die wichtigen Marken?</li>
<li><b>Mittel</b> (3M, 6M): Was passiert gerade? Bildet sich eine Formation?</li>
<li><b>Kurz</b> (1W, 1M): Wie sieht die aktuelle Lage im Detail aus?</li>
</ol>
<p>Widersprechen sich die Zeitebenen, hat die <b>größere Vorrang</b>.</p>
<h3>Typische Denkfallen</h3>
<ul>
<li><b>Bestätigungsfehler</b> <i>(Confirmation Bias)</i>: Wer schon gekauft hat, sieht überall
bullische Muster.</li>
<li><b>Muster im Zufall:</b> Kurse sind zu einem großen Teil zufällig. Wer lange sucht, findet
in jedem Chart ein „Dreieck“.</li>
<li><b>Rückschaufehler:</b> Im Nachhinein ist jedes Muster offensichtlich. Rechts im Chart, wo
die Zukunft beginnt, ist es das nie.</li>
<li><b>Zu viele Indikatoren:</b> Zehn Linien widersprechen sich immer irgendwo – am Ende
entscheidet das Bauchgefühl.</li>
<li><b>Nachrichten schlagen Charts:</b> Quartalszahlen, Zinsentscheide oder Krisen können jede
Formation über Nacht erledigen.</li>
</ul>
<h3>Risiko vorher festlegen</h3>
<p>Bevor du kaufst, beantworte drei Fragen: <b>Wo steige ich ein? Wo liege ich falsch?
Wo will ich hin?</b> „Falsch“ ist der Punkt, an dem dein Grund für den Kauf nicht mehr gilt –
z. B. wenn der Kurs unter die Unterstützung fällt, an der du gekauft hast. Dort liegt dein
<b>Stop-Loss</b>.</p>
<p>Daraus ergibt sich das <b>Chance-Risiko-Verhältnis</b> <i>(CRV)</i>: möglicher Gewinn
geteilt durch möglichen Verlust. Ein Beispiel:</p>
<table width='100%' cellpadding='7' cellspacing='0'>
<tr><td width='40%'>Einstieg</td><td>50 €</td></tr>
<tr><td>Stop-Loss (unter der Unterstützung)</td><td>46 € → Risiko 4 €</td></tr>
<tr><td>Ziel (nächster Widerstand)</td><td>58 € → Chance 8 €</td></tr>
<tr><td><b>CRV</b></td><td><b>8 : 4 = 2</b></td></tr>
</table>
<p>Bei einem CRV von 2 reicht es – vor Kosten –, wenn mehr als jeder dritte Versuch aufgeht.
Bei einem CRV unter 1 musst du dagegen meistens richtig liegen. Viele Trader riskieren
außerdem pro Idee nur einen <b>kleinen Teil ihres Depots</b>, damit eine Serie von
Fehlschlägen sie nicht aus dem Spiel wirft.</p>
{_merke("Charttechnik liefert <b>Wahrscheinlichkeiten</b>, keine Gewissheiten. Wer <b>vor dem "
        "Kauf weiß, wo er aussteigt</b>, wenn er falsch liegt, übersteht auch die "
        "Fehlsignale.")}
{_falle("Ein Stop-Loss ist kein Garantiepreis: Bei einer Kurslücke über Nacht wird er zum "
        "<b>nächsten verfügbaren Kurs</b> ausgeführt – das kann deutlich darunter sein.")}
"""),

    ("kurs-uebung", "11. Checkliste und Übung", KURS, f"""
<h1>Checkliste und Übung</h1>
{_lead("Zum Abschluss: ein fester Ablauf für jeden Chart – und vier Muster zum Selbst-"
       "Erkennen.")}
<h3>Einen Chart in sechs Schritten lesen</h3>
<table width='100%' cellpadding='8' cellspacing='0'>
<tr><td width='8%' valign='top'><b>1</b></td><td><b>Großer Trend</b> – Zeitraum 1J oder 3J:
Höhere Hochs und Tiefs oder tiefere? Kurs über oder unter der 200-Tage-Linie?</td></tr>
<tr><td valign='top'><b>2</b></td><td><b>Wichtige Marken</b> – Wo sind Unterstützungen und
Widerstände? 52W einschalten. Wo steht der Kurs dazwischen?</td></tr>
<tr><td valign='top'><b>3</b></td><td><b>Aktuelle Lage</b> – Zeitraum 3M oder 6M: Trend,
Seitwärtsphase oder Formation im Entstehen?</td></tr>
<tr><td valign='top'><b>4</b></td><td><b>Schwung</b> – RSI über 70 oder unter 30? Gibt es eine
Divergenz? Was sagt der MACD?</td></tr>
<tr><td valign='top'><b>5</b></td><td><b>Bestätigung</b> – Gab es bei Ausbrüchen viel Volumen?
Liegt der Schlusskurs klar jenseits der Marke?</td></tr>
<tr><td valign='top'><b>6</b></td><td><b>Plan und Risiko</b> – Wo läge ich falsch? Wie groß ist
das CRV? Stehen Termine wie Quartalszahlen an?</td></tr>
</table>
<br>
<h3>Übung: Welches Muster ist das?</h3>
<p>Schau dir die vier Charts an und überlege, welche Formation du siehst – und in welche
Richtung sie eher deutet.</p>
<table width='100%' cellpadding='6' cellspacing='0'>
<tr><td align='center'><p class='bildzeile'><img src='kurs:uebung_a'></p></td><td align='center'><p class='bildzeile'><img src='kurs:uebung_b'></p></td></tr>
<tr><td align='center'><p class='bildzeile'><img src='kurs:uebung_c'></p></td><td align='center'><p class='bildzeile'><img src='kurs:uebung_d'></p></td></tr>
</table>
<!--loesung-->
<h3>Auflösung</h3>
<table width='100%' cellpadding='8' cellspacing='0'>
<tr><td width='8%' valign='top'><b>A</b></td><td><b>Doppeltop (M)</b> – zwei Hochs auf gleicher
Höhe, danach fällt der Kurs unter die Nackenlinie. Bärisch. ({_link("kurs-umkehr", "Lektion 8")})</td></tr>
<tr><td valign='top'><b>B</b></td><td><b>Bullenflagge</b> – steiler Anstieg, kurze Pause leicht
nach unten, Ausbruch in Trendrichtung. Bullisch. ({_link("kurs-fortsetzung", "Lektion 9")})</td></tr>
<tr><td valign='top'><b>C</b></td><td><b>Inverse Schulter-Kopf-Schulter</b> – drei Tiefs, das
mittlere am tiefsten, dann Ausbruch über die Nackenlinie. Bullisch.
({_link("kurs-umkehr", "Lektion 8")})</td></tr>
<tr><td valign='top'><b>D</b></td><td><b>Aufsteigendes Dreieck</b> – flache Decke, steigende
Tiefs, Ausbruch nach oben. Bullisch. ({_link("kurs-fortsetzung", "Lektion 9")})</td></tr>
</table>
<!--/loesung-->
<br>
{_merke("Übung macht den Unterschied: Öffne einen Wert aus deiner Watchlist und geh die "
        "Checkliste durch, <b>bevor</b> du auf das Signal schaust. Vergleiche danach mit der "
        "Karte <b>„Warum …?“</b> – siehst du dasselbe wie die Regel?")}
<p>Geschafft – du hast den Chart-Kurs abgeschlossen. Alle Fachbegriffe findest du jederzeit
unter {_link("glossar", "Fachbegriffe A–Z")}.</p>
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
200er nach oben, spricht man vom <i>Golden Cross</i>, nach unten vom <i>Death Cross</i>.
Mehr dazu in {_link("kurs-durchschnitte", "Lektion 5")}.</p>
<p><b>RSI</b> (Relative Stärke, 14 Tage) – misst, wie stark die Gewinne gegenüber den
Verlusten der letzten Tage waren, auf einer Skala von 0 bis 100. <b>Unter 30</b> gilt ein
Wert als <i>überverkauft</i> (+1, oft Gegenbewegung nach oben), <b>über 70</b> als
<i>überkauft</i> (−1).</p>
<p><b>MACD</b> – vergleicht einen schnellen mit einem langsamen gleitenden Durchschnitt
(12 und 26 Tage) und dessen Signallinie (9 Tage). Liegt der MACD über der Signallinie,
nimmt der Schwung zu (+1), sonst ab (−1). Wie du RSI und MACD deutest, zeigt
{_link("kurs-indikatoren", "Lektion 7")}.</p>
<h3>Begründung, Trefferquote, Gegenargumente</h3>
<p>Die Karte <b>„Warum …?“</b> nennt die Gründe für das Signal, was dagegen spricht, wie oft
das Signal bei diesem Wert früher richtig lag und was passieren müsste, damit es wechselt.</p>
{_hinweis("Signale werden aus <b>Tagesschlusskursen</b> berechnet und alle 15 Minuten für deine "
          "Werte neu bewertet. Sie sind bewusst einfach und für alle gleich – <b>keine "
          "persönliche Empfehlung</b>.")}
"""),

    ("charts", "Der Chart in Vyntro", "Signale & Charts", f"""
<h1>Der Chart in Vyntro</h1>
{_lead("Was die Linien und Zeichen im Chart der Detailansicht bedeuten. Wie man Charts "
       "allgemein liest, lernst du im " + _link("kurs", "Chart-Kurs") + ".")}
<h3>Kerzen</h3>
<p>Jede Kerze steht für einen Tag (bei 3J und Max für eine Woche). Der dicke
<b>Körper</b> reicht vom Eröffnungs- bis zum Schlusskurs, die dünnen <b>Dochte</b> zeigen
Hoch und Tief. <span style='color:@gruen'>Grün</span> = Schlusskurs über Eröffnung,
<span style='color:@rot'>rot</span> = darunter. Ausführlich: {_link("kurs-kerzen", "Lektion 1")}.</p>
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
<li>Zeiträume <b>1T</b> und <b>1W</b> zeigen einen bzw. fünf Handelstage als <b>Live-Kerzen</b>:
Die letzte Kerze bewegt sich mit jedem neuen Kurs, und nach Ablauf ihrer Zeit beginnt die
nächste. Daneben wählst du die Kerzengröße (bei 1T 1, 5 oder 15 Minuten, bei 1W 15 Minuten,
30 Minuten oder 1 Stunde) oder schaltest auf <b>Linie</b> um. Oben rechts steht
<b>● LIVE</b>, solange Echtzeit-Kurse ankommen – sonst „Börse geschlossen“ oder ein Hinweis
auf verzögerte Kurse.</li>
<li>Mit der Maus über den Chart fahren: Fadenkreuz mit Datum, Kurs und Veränderung.</li>
<li><b>Vergleichen:</b> bis zu drei andere Werte prozentual im selben Chart.</li>
</ul>
"""),

    ("prognose", "Prognose und Backtest", "Signale & Charts", f"""
<h1>Prognose und Backtest</h1>
<h3>Prognose-Linie</h3>
<p>Die mintfarbene Linie rechts im Chart schreibt den Trend der letzten 12 Monate fort –
aber nur zur <b>Hälfte</b> und höchstens etwa ±25 % pro Jahr, weil Trends meist nachlassen.
Die gestrichelten Linien zeigen die <b>Spannen</b>, in denen der Kurs bei gleicher
Schwankung wie bisher mit 50 % bzw. 80 % Wahrscheinlichkeit liegen würde.</p>
<p>Ist Analystenmeinung verfügbar, zeigt eine gestrichelte Linie zusätzlich das
<b>durchschnittliche Kursziel</b> der Analysten.</p>
{_kasten("Das ist eine <b>statistische Fortschreibung, keine Vorhersage</b>. Nachrichten, "
         "Quartalszahlen oder Krisen können den Kurs jederzeit weit aus der Spanne bewegen.",
         "@gruen", "WICHTIG")}
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
<p>Tipp: Setz Kurs-Alarme auf wichtige <a href='anleitung:kurs-unterstuetzung'>Unterstützungen
und Widerstände</a> – dann musst du nicht ständig auf den Chart schauen.</p>
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


# ------------------------------------------------------------------ Glossar

# (Begriff, englisch/auch, Erklärung, Kapitel-ID für „mehr“ oder "")
GLOSSAR: list[tuple[str, str, str, str]] = [
    ("52-Wochen-Hoch/-Tief", "52-week high/low", "Höchster bzw. tiefster Kurs der letzten zwölf "
     "Monate. Wichtige Marke, an der Kurse oft reagieren.", "kurs-unterstuetzung"),
    ("Abwärtstrend", "downtrend", "Tiefere Hochs und tiefere Tiefs.", "kurs-trend"),
    ("Aufwärtstrend", "uptrend", "Höhere Hochs und höhere Tiefs.", "kurs-trend"),
    ("Ausbruch", "Breakout", "Der Kurs schließt klar über einem Widerstand oder unter einer "
     "Unterstützung.", "kurs-unterstuetzung"),
    ("Ausverkauf", "Kapitulation, sell-off", "Sehr starker Fall mit riesigem Volumen; die "
     "letzten Verkäufer geben auf. Oft nahe am Tief.", "kurs-volumen"),
    ("Bärenfalle / Bullenfalle", "bear trap / bull trap", "Fehlausbruch nach unten bzw. oben: Der "
     "Kurs kehrt gleich wieder um und erwischt die, die dem Ausbruch gefolgt sind.",
     "kurs-unterstuetzung"),
    ("bearish / bärisch", "", "Spricht für fallende Kurse.", "kurs-kerzenmuster"),
    ("Bestätigung", "confirmation", "Ein Signal gilt erst, wenn der Kurs es bestätigt – z. B. "
     "Schlusskurs jenseits der Nackenlinie oder eine Folgekerze in die neue Richtung.",
     "kurs-umkehr"),
    ("Bollinger-Bänder", "Bollinger Bands", "20-Tage-Durchschnitt ± 2 Standardabweichungen. "
     "Zeigen die Schwankungsbreite.", "kurs-indikatoren"),
    ("bullish / bullisch", "", "Spricht für steigende Kurse.", "kurs-kerzenmuster"),
    ("Chance-Risiko-Verhältnis", "CRV, risk/reward", "Möglicher Gewinn geteilt durch möglichen "
     "Verlust eines Trades.", "kurs-fallen"),
    ("Chartformation", "chart pattern", "Typisches, wiederkehrendes Kursbild wie Doppelboden "
     "oder Dreieck.", "kurs-umkehr"),
    ("Charttechnik", "technische Analyse", "Analyse von Kursverlauf und Volumen, um "
     "Wahrscheinlichkeiten für die weitere Entwicklung abzuschätzen.", "kurs"),
    ("Death Cross", "", "Die 50-Tage-Linie kreuzt die 200-Tage-Linie von oben nach unten.",
     "kurs-durchschnitte"),
    ("Divergenz", "divergence", "Kurs und Indikator laufen auseinander, z. B. Kurs mit höherem "
     "Hoch, RSI mit tieferem Hoch. Zeigt nachlassenden Schwung.", "kurs-indikatoren"),
    ("Docht", "Schatten, Lunte, wick", "Dünner Strich einer Kerze bis zum Hoch bzw. Tief.",
     "kurs-kerzen"),
    ("Doji", "", "Kerze mit fast gleicher Eröffnung und Schluss – Unentschlossenheit.",
     "kurs-kerzenmuster"),
    ("Doppelboden / Doppeltop", "W- / M-Formation", "Zwei Tiefs bzw. Hochs auf etwa gleicher "
     "Höhe; Umkehrformation, bestätigt mit Bruch der Nackenlinie.", "kurs-umkehr"),
    ("Dreieck", "triangle", "Formation, in der die Schwankungen zusammenlaufen – aufsteigend, "
     "absteigend oder symmetrisch.", "kurs-fortsetzung"),
    ("EMA", "exponential moving average", "Exponentieller Durchschnitt; gewichtet jüngere Kurse "
     "stärker als der einfache Durchschnitt.", "kurs-durchschnitte"),
    ("Engulfing", "Umhüllende", "Große Kerze, deren Körper den Körper der Vortageskerze "
     "komplett umschließt.", "kurs-kerzenmuster"),
    ("Fehlausbruch", "Fakeout", "Kurzer Ausbruch, der gleich wieder zurückfällt.",
     "kurs-unterstuetzung"),
    ("Flagge / Wimpel", "flag / pennant", "Kurze Pause nach einem steilen Anstieg oder Fall "
     "(Fahnenstange); Fortsetzungsformation.", "kurs-fortsetzung"),
    ("Fundamentalanalyse", "", "Bewertung eines Unternehmens anhand von Umsatz, Gewinn, "
     "Schulden und Aussichten – das Gegenstück zur Charttechnik.", "kurs"),
    ("Gap", "Kurslücke", "Bereich, in dem kein Handel stattfand, weil der Kurs deutlich anders "
     "eröffnet hat, als er am Vortag geschlossen hat.", "kurs-fortsetzung"),
    ("Gleitender Durchschnitt", "Moving Average, MA, SMA", "Mittelwert der letzten X "
     "Schlusskurse, der jeden Tag mitwandert.", "kurs-durchschnitte"),
    ("Golden Cross", "", "Die 50-Tage-Linie kreuzt die 200-Tage-Linie von unten nach oben.",
     "kurs-durchschnitte"),
    ("Hammer", "", "Kerze mit kleinem Körper oben und langem unterem Docht nach einem Fall.",
     "kurs-kerzenmuster"),
    ("Indikator", "indicator", "Aus Kursen (und Volumen) berechnete Hilfslinie, z. B. RSI oder "
     "MACD.", "kurs-indikatoren"),
    ("Kerze", "Candlestick", "Darstellung von Eröffnung, Hoch, Tief und Schluss eines "
     "Zeitabschnitts.", "kurs-kerzen"),
    ("Konsolidierung", "Seitwärtsphase, Range", "Phase ohne klaren Trend, in der der Kurs "
     "zwischen Boden und Decke pendelt.", "kurs-trend"),
    ("Korrektur", "Rücksetzer, Pullback", "Gegenbewegung innerhalb eines Trends.",
     "kurs-trend"),
    ("Körper", "body", "Dicker Teil einer Kerze zwischen Eröffnung und Schluss.",
     "kurs-kerzen"),
    ("Liquidität", "liquidity", "Wie leicht ein Wert ohne großen Preisabschlag gehandelt "
     "werden kann. Viel Volumen = hohe Liquidität.", "kurs-volumen"),
    ("MACD", "Moving Average Convergence Divergence", "Differenz der 12- und 26-Tage-EMA, "
     "verglichen mit ihrer 9-Tage-Signallinie. Misst den Schwung.", "kurs-indikatoren"),
    ("Momentum", "Schwung", "Wie schnell und kräftig sich ein Kurs bewegt.",
     "kurs-indikatoren"),
    ("Nackenlinie", "neckline", "Linie, deren Bruch eine Umkehrformation bestätigt.",
     "kurs-umkehr"),
    ("OHLC", "Open, High, Low, Close", "Die vier Preise einer Kerze: Eröffnung, Hoch, Tief, "
     "Schluss.", "kurs-kerzen"),
    ("Oszillator", "oscillator", "Indikator, der in einem festen Bereich schwankt, z. B. der RSI "
     "zwischen 0 und 100.", "kurs-indikatoren"),
    ("Rollentausch", "role reversal", "Ein durchbrochener Widerstand wird zur Unterstützung "
     "und umgekehrt.", "kurs-unterstuetzung"),
    ("RSI", "Relative Strength Index", "Oszillator von 0 bis 100; über 70 überkauft, unter 30 "
     "überverkauft.", "kurs-indikatoren"),
    ("Rücktest", "Retest", "Der Kurs kehrt nach einem Ausbruch zur durchbrochenen Marke "
     "zurück.", "kurs-unterstuetzung"),
    ("Schulter-Kopf-Schulter", "SKS, Head and Shoulders", "Drei Hochs, das mittlere am "
     "höchsten; Umkehrformation nach unten. Invers am Boden nach oben.", "kurs-umkehr"),
    ("Shooting Star", "Sternschnuppe", "Kerze mit kleinem Körper unten und langem oberem "
     "Docht nach einem Anstieg.", "kurs-kerzenmuster"),
    ("Signallinie", "signal line", "9-Tage-Durchschnitt des MACD.", "kurs-indikatoren"),
    ("Spread", "", "Unterschied zwischen Kauf- und Verkaufskurs.", "orders"),
    ("Squeeze", "", "Die Bollinger-Bänder werden sehr eng – oft folgt eine starke Bewegung.",
     "kurs-indikatoren"),
    ("Standardabweichung", "standard deviation", "Statistisches Maß dafür, wie weit Werte im "
     "Schnitt vom Mittelwert abweichen.", "kurs-indikatoren"),
    ("Stop-Loss", "", "Order, die automatisch verkauft, wenn der Kurs unter eine Marke fällt.",
     "kurs-fallen"),
    ("Trendbruch", "trend break", "Der Kurs fällt deutlich durch eine Trendlinie – ein "
     "Warnzeichen.", "kurs-trend"),
    ("Trendlinie", "trendline", "Linie durch mindestens zwei Tiefs (Aufwärtstrend) bzw. Hochs "
     "(Abwärtstrend).", "kurs-trend"),
    ("überkauft / überverkauft", "overbought / oversold", "RSI über 70 bzw. unter 30: Der Kurs "
     "ist sehr schnell gestiegen bzw. gefallen.", "kurs-indikatoren"),
    ("Umkehrformation", "reversal pattern", "Formation, die einen Richtungswechsel des Trends "
     "anzeigt.", "kurs-umkehr"),
    ("Fortsetzungsformation", "continuation pattern", "Formation, nach der der bisherige Trend "
     "meist weiterläuft.", "kurs-fortsetzung"),
    ("Unterstützung", "Support", "Kursbereich, an dem Käufer früher einen Fall gestoppt "
     "haben – ein Boden.", "kurs-unterstuetzung"),
    ("Volatilität", "volatility", "Stärke der Kursschwankungen.", "kurs-indikatoren"),
    ("Volumen", "volume", "Anzahl der gehandelten Anteile in einem Zeitabschnitt.",
     "kurs-volumen"),
    ("Widerstand", "Resistance", "Kursbereich, an dem Verkäufer früher einen Anstieg gebremst "
     "haben – eine Decke.", "kurs-unterstuetzung"),
    ("Zeitebene", "Timeframe", "Der betrachtete Zeitraum bzw. die Dauer einer Kerze (Tag, "
     "Woche …).", "kurs-fallen"),
]


def _sortierschluessel(begriff: str) -> str:
    b = begriff.lower()
    for a, e in (("ä", "a"), ("ö", "o"), ("ü", "u"), ("ß", "ss")):
        b = b.replace(a, e)
    return re.sub(r"^[^a-z]+", "", b) or b


def _glossar_html() -> str:
    titel = {k[0]: k[1] for k in KAPITEL}
    teile = ["<h1>Fachbegriffe A–Z</h1>",
             _lead("Die wichtigsten Begriffe aus Chart-Kurs und App in einem Satz – mit Link "
                   "zur passenden Lektion. Englische Begriffe stehen grau darunter.")]
    buchstabe = None
    for begriff, auch, text, ziel in sorted(GLOSSAR, key=lambda g: _sortierschluessel(g[0])):
        b = _sortierschluessel(begriff)[0].upper()
        if b.isdigit():
            b = "0–9"
        if b != buchstabe:
            if buchstabe is not None:
                teile.append("</table>")
            buchstabe = b
            teile.append(f"<h3>{b}</h3><table width='100%' cellpadding='6' cellspacing='0'>")
        ziel_titel = titel.get(ziel, "mehr").replace("&", "&amp;")
        mehr = f" {_link(ziel, ziel_titel + ' →')}" if ziel else ""
        auch_html = f"<br><i>{auch}</i>" if auch else ""
        teile.append(f"<tr><td width='32%' valign='top'><b>{begriff}</b>{auch_html}</td>"
                     f"<td valign='top'>{text}{mehr}</td></tr>")
    teile.append("</table>")
    return "\n".join(teile)


KAPITEL.append(("glossar", "Fachbegriffe A–Z", "Nachschlagen", _glossar_html()))


# ------------------------------------------------------------------ Darstellung

_BILD = re.compile(r"<img src='kurs:(\w+)'>")
_LOESUNG = re.compile(r"<!--loesung-->.*?<!--/loesung-->", re.S)


def _lektionen() -> list[str]:
    return [k[0] for k in KAPITEL if k[2] == KURS and k[0] != "kurs"]


def hat_bilder(id_: str) -> bool:
    return any(kid == id_ and "kurs:" in html for kid, _t, _g, html in KAPITEL)


def kapitel_html(id_: str, taste: str, farben: dict, breite: int = 640,
                 loesung: bool = False) -> str:
    """HTML eines Kapitels mit eingesetzten Farben, Tastenkürzeln und Bildgrößen.

    breite: verfügbare Textbreite in Pixeln (für die Lehrbilder).
    loesung: in der Übung die Auflösung zeigen statt des Knopfs „Auflösung anzeigen“.
    """
    ids = [k[0] for k in KAPITEL]
    if id_ not in ids:
        return ""
    kid, _titel, gruppe, html = KAPITEL[ids.index(id_)]
    text = html.replace("{T}", taste)

    if not loesung:
        text = _LOESUNG.sub("<p><a href='loesung:zeigen'>Auflösung anzeigen ↓</a></p>", text)

    def bild(m: re.Match) -> str:
        import kursbilder
        name = m.group(1)
        verhaeltnis, anteil = kursbilder.FORMAT.get(name, (0.4, 1.0))
        b = max(160, min(680, breite) if anteil >= 1 else int(min(680, breite) * anteil) - 16)
        return f"<img src='kurs:{name}?b={b}' width='{b}' height='{round(b * verhaeltnis)}'>"
    text = _BILD.sub(bild, text)

    # Lektionen: Kopfzeile „Lektion x von y“ und Verweis auf die nächste Lektion
    if gruppe == KURS:
        lektionen = _lektionen()
        if kid in lektionen:
            nr = lektionen.index(kid) + 1
            kopf = f"<p class='kicker'>CHART-KURS · LEKTION {nr} VON {len(lektionen)}</p>"
        else:
            kopf = "<p class='kicker'>CHART-KURS</p>"
        text = kopf + text
        if kid in lektionen and ids.index(kid) + 1 < len(ids):
            nk, nt, ng, _ = KAPITEL[ids.index(kid) + 1]
            wort = "Nächste Lektion" if ng == KURS else "Weiter"
            name = re.sub(r"^\d+\.\s*", "", nt).replace("&", "&amp;")
            text += (f"<br><p class='weiter'>{wort}: <a href='anleitung:{nk}'>{name} →</a>"
                     f"</p>")

    for k in ("gruen", "rot", "grau", "kasten"):
        text = text.replace(f"@{k}", farben.get(k, "#888"))
    return text


def suchen(begriff: str) -> list[str]:
    """IDs der Kapitel, in deren Titel oder Text der Begriff vorkommt."""
    b = begriff.strip().lower()
    if not b:
        return [k[0] for k in KAPITEL]
    treffer = []
    muster = re.compile(r"(?<!\w)" + re.escape(b))  # ab Wortanfang
    for kid, titel, gruppe, html in KAPITEL:
        text = re.sub(r"<[^>]+>", " ", html).lower()
        if muster.search(titel.lower()) or muster.search(text) or muster.search(gruppe.lower()):
            treffer.append(kid)
    return treffer
