#!/usr/bin/env python
#
# Copyright (C) 2020
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import argparse
import datetime
import hashlib
import logging
import os.path as op
import shutil
import sqlite3
from collections import UserDict
from math import ceil

from filelock import FileLock, Timeout

from .ranking import ranking_systems
from .replay import GamePlayerInfo
from .utils import get_results, get_profile_ids


class PlayerLookup(UserDict):
    """Connects a `GamePlayerInfo` (or its fingerprint) to a `_Player`.

    Several way to access a player:
        1) From a `GamePlayerInfo`: `lookup[result.player0]`
        2) From the unique id: `lookup[6003]`
        3) From the player name (since it's also unique): `lookup['morkel']`.
           Notice this only works for __getitem__ and not __setitem__. The name
           is also case-sensitive.
    """

    def __init__(self, accounts_db, ranking):
        super().__init__()
        self.accounts_db = accounts_db
        self.ranking = ranking
        self._names = {}

    def _insert_from_fingerprint(self, fingerprint):
        profile_id, name, avatar_url = self.accounts_db.get(fingerprint)
        self.data.setdefault(profile_id, _Player(self.ranking, profile_id, name, avatar_url))
        self._names.setdefault(self.data[profile_id].name, self.data[profile_id])
        return self.data[profile_id]

    def __getitem__(self, obj):
        if isinstance(obj, GamePlayerInfo):
            return self._insert_from_fingerprint(obj.fingerprint)
        if isinstance(obj, str):  # we assume it's the name of the player, then.
            if obj not in self._names:
                raise KeyError(obj)
            return self._names[obj]
        return super().__getitem__(obj)

    def __setitem__(self, key, obj):
        assert isinstance(obj, _Player)
        super().__setitem__(key, obj)
        self._names[obj.name] = obj

    def __repr__(self):
        return f"<PlayerLookup dictionary with {len(self.data)} items>"


class _Player:
    def __init__(self, ranking, profile_id, name, avatar_url, banned=False):
        self.profile_id = profile_id
        self.name = name
        self.wins = 0
        self.losses = 0
        self.prv_rating = ranking.get_default_rating()
        self.rating = ranking.get_default_rating()
        self.avatar_url = avatar_url
        self.banned = banned

    def update_rating(self, new_rating):
        self.prv_rating = self.rating
        self.rating = new_rating

    def __repr__(self):
        return f"<Player {self.name}, id={self.profile_id}>"

    @property
    def sql_row(self):
        return (
            self.profile_id,
            self.name,
            self.avatar_url,
            self.banned,
            self.wins,
            self.losses,
            self.prv_rating.display_value,
            self.rating.display_value,
        )


class _OutCome:
    def __init__(self, result, p0, p1):
        self._hash = hashlib.sha256(result.filename.encode()).hexdigest()
        self._filename = result.filename
        self._start_time = result.start_time
        self._end_time = result.end_time
        self._p0_profile_id = p0.profile_id
        self._p1_profile_id = p1.profile_id
        self._p0_rating0 = p0.prv_rating
        self._p1_rating0 = p1.prv_rating
        self._p0_rating1 = p0.rating
        self._p1_rating1 = p1.rating
        self._p0_faction = result.player0.faction
        self._p1_faction = result.player1.faction
        self._p0_selected_faction = result.player0.selected_faction
        self._p1_selected_faction = result.player1.selected_faction
        self._map_uid = result.map_uid
        self._map_title = result.map_title

    @staticmethod
    def _sql_date_fmt(dt):
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def sql_row(self):
        return (
            self._hash,
            self._sql_date_fmt(self._start_time),
            self._sql_date_fmt(self._end_time),
            self._filename,
            self._p0_profile_id,
            self._p1_profile_id,
            self._p0_rating0.display_value,
            self._p1_rating0.display_value,
            self._p0_rating1.display_value,
            self._p1_rating1.display_value,
            self._p0_faction,
            self._p1_faction,
            self._p0_selected_faction,
            self._p1_selected_faction,
            self._map_uid,
            self._map_title,
        )


def _get_players_outcomes(accounts_db, results, ranking_system):

    ranking = ranking_systems[ranking_system]()

    player_lookup = PlayerLookup(accounts_db, ranking)
    outcomes = []

    ratings = ranking.compute_ratings_from_series_of_games(results, player_lookup)

    for result, (r0, r1) in zip(results, ratings):
        p0 = player_lookup[result.player0]
        p1 = player_lookup[result.player1]
        p0.update_rating(r0)
        p1.update_rating(r1)
        p0.wins += 1
        p1.losses += 1
        outcomes.append(_OutCome(result, p0, p1))
    players = player_lookup.values()
    return players, outcomes


def _preprocess_period(args):
    """Forms CLI arguments "period", "start", and "end" into a dictionary

    Possible combinations:
        - period in {1m, 2m}, start and end missing: returns the 1 or 2 month period
        - period is any string, start an ISO format date string, end missing:
          returns the period from start date to "now" (actually, "tomorrow")
        - period is any string, start and end are ISO format date strings:
          returns the period from start to end date

    Returns a dict with elements, "name" (str), "start", "end" (datetime.date)
    """
    today = datetime.date.today()
    if args.start:
        start = datetime.date.fromisoformat(args.start)
        if args.end:
            end = datetime.date.fromisoformat(args.end)
        else:
            end = today + datetime.timedelta(days=1)
    else:
        if args.period == "1m":
            start = datetime.date(today.year, today.month, 1)
        elif args.period == "2m":
            start_month = ((today.month - 1) & ~1) + 1
            start = datetime.date(today.year, start_month, 1)
        else:
            start = datetime.date(year=1990, month=1, day=1)
        end = today + datetime.timedelta(days=1)
    return {"name": args.period, "start": start, "end": end}


def _main(args):
    conn = sqlite3.connect(args.database)

    c = conn.cursor()

    # We don't know if the new submitted replays will be properly ordered, so
    # all the information needs to be reconstructed
    c.execute("DROP TABLE IF EXISTS players")
    c.execute("DROP TABLE IF EXISTS outcomes")

    with open(args.schema) as f:
        c.executescript(f.read())

    # Re-use the cached OpenRA account information to prevent stressing too
    # much the service
    request_accounts = c.execute("SELECT * FROM accounts")
    accounts_db = {fp: (pid, pname, avatar_url) for fp, pid, pname, avatar_url in request_accounts.fetchall()}

    period_dict = _preprocess_period(args)
    results = get_results(accounts_db, args.replays, period_dict)

    players, outcomes = _get_players_outcomes(accounts_db, results, args.ranking)

    if args.bans_file:
        banned_profiles = get_profile_ids(args.bans_file)
        for player in players:
            player.banned = player.profile_id in banned_profiles

    outcomes_sql = [o.sql_row for o in outcomes]
    players_sql = [p.sql_row for p in players]
    accounts_sql = [(fp, acc[0], acc[1], acc[2]) for fp, acc in accounts_db.items() if acc is not None]

    c.executemany("INSERT OR IGNORE INTO accounts VALUES (?,?,?,?)", accounts_sql)
    c.executemany("INSERT OR IGNORE INTO players VALUES (?,?,?,?,?,?,?,?)", players_sql)
    c.executemany("INSERT OR IGNORE INTO outcomes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", outcomes_sql)

    conn.commit()
    conn.close()


def run():
    logging.basicConfig(level="INFO")
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--database", default="db.sqlite3")
    parser.add_argument("-s", "--schema", default=op.join(op.dirname(__file__), "ladder.sql"))
    parser.add_argument("-r", "--ranking", choices=ranking_systems.keys(), default="elo")
    parser.add_argument("-p", "--period")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--bans-file")
    parser.add_argument("-l", "--log-level", default="WARNING")
    parser.add_argument("replays", nargs="*")
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level)

    lockfile = args.database + ".lock"
    lock = FileLock(lockfile, timeout=1)
    try:
        with lock:
            _main(args)
    except Timeout:
        logging.error("Another instance of this application currently holds the %s lock file.", lockfile)


def initialize_periodic_databases():
    """A CLI tool to create multiple database files in batch

    In the current implementation, this is customized to support 2-months-periods as used by the ladder.openhv.net website.
    For a given timespan based on "year" and "start-month" parameters, SQLite database files get created. Each DB file
    contains data for a 2-month period starting with every 2nd month of a year (i.e. January, March, May, ...) which
    will be named following the pattern db-{year}-{nr}.sqlite3 where {nr} is an integer counter starting with 1 for the
    Jan-Feb period going up to 6 for the Nov-Dec period of the given year.

    If invoked with a start month that does not mark the beginning of one of these periods, it will get corrected by
    subtracting one month so that the resulting DB files will be true to the defined format/content.

    For less customized database file creation, refer to the `openhv-ladder` CLI tool utilizing "start" and "end"
    parameters.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--schema", default=op.join(op.dirname(__file__), "ladder.sql"))
    parser.add_argument("-r", "--ranking", choices=ranking_systems.keys(), default="openskill")
    parser.add_argument("--bans-file")
    parser.add_argument("-m", "--mod", default="hv")
    parser.add_argument("-y", "--year", type=int, default=datetime.date.today().year)
    parser.add_argument("--start-month", type=int, default="1", help="Number between 1 and 12")
    parser.add_argument("-l", "--log-level", default="WARNING")
    parser.add_argument("replays", nargs="*")
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level)

    # Correct to previous month for even-numbered months (February, April, ...)
    start_month = args.start_month - (args.start_month & 1 == 0)

    start_date = datetime.date(year=args.year, month=start_month, day=1)
    season_counter = ceil(start_month / 2)
    prev_db_name = None

    while True:
        # calculate the seasons end date (start + 2 months - 1 day)
        end_date = datetime.date(start_date.year, (start_date.month + 2) % 12, start_date.day)
        # in case we have reached January again, update year
        if end_date.month == 1:
            end_date = end_date.replace(year=end_date.year + 1)
        end_date -= datetime.timedelta(days=1)

        # prepare arguments for creating the actual database files
        db_name = f"db-{args.mod}-{start_date.year}-{season_counter}.sqlite3"

        # If the first database from the batch has already been created, copy that to use it as a base for the
        # next iteration; this reduces API calls to the OpenRA user account service
        if prev_db_name is not None:
            shutil.copyfile(prev_db_name, db_name)
            logging.info(f"Copied {prev_db_name} to {db_name}")

        # Track database filename for next iteration
        prev_db_name = db_name

        lockfile = db_name + ".lock"
        args.start = str(start_date)
        args.end = str(end_date)
        args.database = db_name
        args.period = ""

        # create the actual database files using _main() method
        try:
            with FileLock(lockfile, timeout=1):
                _main(args)
                logging.info(
                    f"Created database file {db_name} using "
                    f"start date {start_date}, end date {end_date}, source "
                    f"folder {args.replays}."
                )
        except Timeout:
            logging.error("Another instance of this application currently holds the %s lock file.", lockfile)

        #
        start_date = start_date.replace(month=(start_date.month + 2) % 12)
        season_counter += 1

        # stop the loop if we completed a year or if the start date is in the future
        if start_date.month == 1 or start_date > datetime.date.today():
            break
