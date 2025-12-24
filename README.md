# cs2_elo
A system to track elo and to balance team for a group of players

## Usage
- edit `data/initial_elos.json` to give a starting elo for the players. Player name should agree with how they appear in the match history data file (copied from steam scrimmage match history)
- edit `data/player_aliases.json` to map common nicknames to actual in-game player names
- curate `data/cs_nz_history.txt` by copy match history from scrimmage page on steam
- double click `run.bat` (on windows OS) to launch app
- set input file to `cs_nz_history.txt` or equivalent match history data file and `Parse`
- move to the `Balance Teams` Tab, and select or type out the names of players participating. Click `Balance Teams` once ready.
