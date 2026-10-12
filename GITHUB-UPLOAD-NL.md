# Naar GitHub uploaden — eenvoudige uitleg

Deze uitleg gaat ervan uit dat je nog weinig met Git/GitHub hebt gedaan.

## Makkelijkste methode: via de GitHub-website

1. Pak `sublime-markdown-outline-v1.0.0.zip` uit op je pc.
2. Ga naar GitHub en log in.
3. Klik rechtsboven op **+** en kies **New repository**.
4. Geef de repository bijvoorbeeld deze naam:

   `sublime-markdown-outline`

5. Kies **Public** als iedereen hem mag zien, of **Private** als alleen jij hem wilt gebruiken.
6. Vink **Add a README**, **.gitignore** en **license** op deze GitHub-pagina NIET aan. Die bestanden zitten al in deze map.
7. Klik **Create repository**.
8. Op de lege repositorypagina kies je **uploading an existing file** of **Add file → Upload files**.
9. Open lokaal de uitgepakte map `sublime-markdown-outline`.
10. Selecteer de inhoud van die map en sleep die naar de GitHub-uploadpagina.
11. Controleer dat GitHub onder andere deze bestanden laat zien:

```text
MarkdownOutline.py
Default.sublime-commands
Main.sublime-menu
README.md
INSTALL-NL.md
CHANGELOG.md
LICENSE
docs/
examples/
```

12. Onderaan bij **Commit changes** zet je bijvoorbeeld:

```text
Initial release v1.0.0
```

13. Klik **Commit changes**.

Dat is in gewone taal wat "inchecken" betekent: je slaat een versie van de bestanden met een beschrijving op in Git.

## Daarna een Release maken

Als de repository online staat:

1. Open de repository.
2. Klik rechts op **Releases**.
3. Kies **Draft a new release**.
4. Klik **Choose a tag** en maak:

```text
v1.0.0
```

5. Release title:

```text
Markdown Outline v1.0.0
```

6. Korte tekst:

```text
First stable GitHub release with global fold levels,
progressive drill-down and synchronized Markdown editor folding.
```

7. Sleep `MarkdownOutline-v1.0.0.sublime-package` als downloadbestand naar de release-assets.
8. Klik **Publish release**.

Nu heb je twee dingen:

- de broncode in je GitHub repository;
- een versie `v1.0.0` die mensen als release kunnen downloaden.

## Later wijzigingen inchecken

Als je later bijvoorbeeld `MarkdownOutline.py` aanpast, kun je op GitHub opnieuw **Add file → Upload files** gebruiken en het bestaande bestand vervangen.

Gebruik dan een korte committekst die uitlegt wat veranderde, bijvoorbeeld:

```text
Fix outline refresh after heading edits
```

Voor regelmatige ontwikkeling is GitHub Desktop of Git via PowerShell makkelijker. Maar voor de eerste publicatie is de webmethode het eenvoudigst.
