# Club Logo Assets

Place local club badge/logo files in this folder. The Streamlit app loads logos only from local files and does not hotlink external image URLs.

Official club logos are not included by default because club badges may be protected by trademark and licensing restrictions. Add official files only if you have the right to use them.

This folder may contain neutral generated placeholder badges with initials and approximate team colors. These are not official club logos.

Supported formats:

- PNG
- SVG

Recommended filenames must match the team names used by the model or the `team_logo_map` in `app.py`:

- `Arsenal.png`
- `Aston Villa.png`
- `Bournemouth.png`
- `Brentford.png`
- `Brighton.png`
- `Chelsea.png`
- `Crystal Palace.png`
- `Everton.png`
- `Fulham.png`
- `Leeds.png`
- `Liverpool.png`
- `Man City.png`
- `Man United.png`
- `Newcastle.png`
- `Nott'm Forest.png`
- `Sunderland.png`
- `Tottenham.png`

SVG alternatives also work, for example `Arsenal.svg`.

If a logo is missing, the dashboard shows a clean circular initials placeholder such as `ARS`, `BRI`, or `BOU`.

Do not represent generated placeholders as official club logos.
