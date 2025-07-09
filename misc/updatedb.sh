#!/bin/sh

set -xeu

~/venv/bin/openhv-ladder --bans-file /home/openhv/bans.list -d db-hv-all.sqlite3      /home/openhv/srv-ladder/instance-*/support_dir/Replays/
~/venv/bin/openhv-ladder --bans-file /home/openhv/bans.list -d db-hv-2m.sqlite3 -p 2m /home/openhv/srv-ladder/instance-*/support_dir/Replays/

cp -v db-*-*.sqlite3  /home/web/venv/var/web-instance/
