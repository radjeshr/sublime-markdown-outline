# Installatie en gebruik — Nederlands

## Wat installeer je?

`MarkdownOutline` is een kleine Sublime Text-plugin die rechts naast je Markdown-document een klikbare heading-tree toont.

De plugin gebruikt de Markdown-headings:

```markdown
# Level 1
## Level 2
### Level 3
```

## Eenmalige installatie

1. Open Sublime Text.
2. Kies **Preferences → Browse Packages…**.
3. Er opent een Windows Verkenner-map. Dit is jouw Sublime `Packages`-map.
4. Sluit Sublime Text volledig.
5. Gebruik je nog de oude ontwikkelversie? Verwijder of hernoem dan:
   - `Packages\User\MarkdownOutline.py`
   - `Packages\User\MarkdownOutline.sublime-commands`
6. Maak in `Packages` een map met exact deze naam:
   `MarkdownOutline`
7. Kopieer de inhoud van deze Git-repository naar die map.
8. Start Sublime Text opnieuw.
9. Open een `.md`-bestand.
10. Druk `Ctrl+Shift+P`.
11. Kies **Markdown Outline: Show Right**.

Op jouw Windows-machine ziet het pad er normaal ongeveer zo uit:

```text
C:\Users\<jouw-gebruikersnaam>\AppData\Roaming\Sublime Text\Packages\MarkdownOutline\
```

## Hoe gebruik je hem?

Bovenaan rechts staat ongeveer:

```text
MARKDOWN OUTLINE    Fold: Level 1 ▾    ↻   +   −   ×
```

`Fold: Level 1` betekent: gebruik Level 1 (`#`) als globale basis.

Klik je daarna op `▸ October 2026`, dan wordt alleen October één niveau verder geopend.

Klik je vervolgens op `▸ Sunday, October 11, 2026`, dan wordt alleen die Sunday-branch verder geopend. Andere maanden/dagen blijven zoals ze stonden.

Dit heet progressive drill-down.

## Betekenis van de knoppen

- `Fold: Level N ▾` — kies het globale fold-niveau.
- `↻` — tree opnieuw inlezen.
- `+` — alles volledig open.
- `−` — terug naar Fold Level 1.
- `×` — outline sluiten.
- `▸/▾` — alleen deze specifieke branch openen/sluiten.
- Klik op de headingtekst — spring naar die heading in het Markdown-document.

## Belangrijk tijdens editen

Normaal typen of een heading aanpassen mag het document niet automatisch opnieuw dichtklappen.

De plugin ververst de tree na een wijziging, maar verandert editor-folds alleen na een expliciete fold/outline-actie.

## Problemen oplossen

### Command verschijnt niet

Controleer of deze bestanden bestaan:

```text
Packages\MarkdownOutline\MarkdownOutline.py
Packages\MarkdownOutline\Default.sublime-commands
```

Sluit Sublime daarna volledig af en start opnieuw.

### Dubbele of vreemde commands

Controleer of de oude ontwikkelbestanden nog in `Packages\User\` staan:

```text
MarkdownOutline.py
MarkdownOutline.sublime-commands
```

Die moeten weg of hernoemd zijn als je de echte package-map gebruikt.

### Outline zegt dat je eerst Single Layout moet gebruiken

Kies:

```text
View → Layout → Single
```

en start daarna **Markdown Outline: Show Right** opnieuw.

### Een heading verschijnt niet

De plugin leest momenteel alleen `#`-stijl headings. Bijvoorbeeld:

```markdown
## Dit werkt
```

Setext-stijl wordt niet gebruikt:

```markdown
Dit is een heading
-------------------
```
