# OpenHV ladder

This repository contains all the sources used by the OpenHV community
competitive 1v1 ladder hosted on [ladder.openhv.net](http://ladder.openhv.net).

It contains:
- the web frontend written in Flask (Python)
- the backend tools (`openhv-ladder`, `openhv-replay`)
- the game server configuration
- detailed explanations on the setup

For some context and history on the project, you can also read the following
blog post: [Building a competitive ladder for OpenRA][blog-post].

[blog-post]: http://blog.pkh.me/p/28-building-a-competitive-ladder-for-openra.html


## Developers

### Bootstrap

The only dependency is `Python`. To run the ladder locally, just type `make`.
This will create a local Python virtualenv, bootstrap all the dependencies into
it, and start a local development server.

The site should be accessible through http://127.0.0.1:5000 and any change in
the sources will be reflected there immediately.

Initially the database is empty so what's being displayed has little to no
interest. We can fill it using the `openhv-ladder` backend command:

```sh
# Enter the virtualenv
. venv/bin/activate

# Create the 2 databases (all times and periodic) with your local HV replays
openhv-ladder -d db-hv-all.sqlite3 ~/.config/openra/Replays/hv
openhv-ladder -d db-hv-2m.sqlite3 -p 2m ~/.config/openra/Replays/hv

# If everything went well, update the DB of the website atomically
cp db-hv-all.sqlite3 db-hv-2m.sqlite3 instance/
```

### Docker

The web services can be run in Docker containers. Please refer to the
[Docker instructions](.docker/README.md) for more information.

## Production infrastructure

In production, the setup requires a bit more work than in development mode.
Following is a suggestion of setup.

Let's assume we have 2 users: `ora` and `web`. `ora` is running the game
server, and `web` runs the backend script and the web frontend (this could be
split further but let's keep it simple for now):

```sh
useradd -m ora
useradd -m web

# allow the web to read the replays
usermod -a -G ora web
chmod g+rx /home/openhv
```

### Game server instances

`ora` needs a virtualenv with the ladder installed in it. For that, we need to
build a Python `wheel` of `oraladder`. This can be done with `make wheel`.  It
will create an `oraladder-*-py3-none-any.whl` file. After uploading it into
`ora` home directory, we can setup the game server instances:

```sh
# Setup virtualenv
python -m venv venv

# Enter the virtualenv
. venv/bin/activate

# Install the ladder wheel
pip install oraladder-*-py3-none-any.whl
```


### Backend

Just like `ora`, `web` needs a virtualenv with the ladder installed in it. Upload
`oraladder-*-py3-none-any.whl` again, this time in `web` home directory. Then
we can setup the ladder:

```sh
# Setup virtualenv
python -m venv venv

# Enter the virtualenv
. venv/bin/activate

# Install the ladder wheel
pip install oraladder-*-py3-none-any.whl

# Create initial empty databases
mkdir -p venv/var/web-instance
openhv-ladder -d venv/var/web-instance/db-hv-all.sqlite3  # all-time DB
openhv-ladder -d venv/var/web-instance/db-hv-2m.sqlite3 -p 2m  # periodic DB

# Create a useful DB update script
cat <<EOF > ~/update-ladderdb.sh
#!/bin/sh
set -xeu
~/venv/bin/openhv-ladder -d db-hv-all.sqlite3      /home/openhv/srv-ladder/instance-*/support_dir/Replays/
~/venv/bin/openhv-ladder -d db-hv-2m.sqlite3 -p 2m /home/openhv/srv-ladder/instance-*/support_dir/Replays/
cp db-hv-all.sqlite3 db-hv-2m.sqlite3 /home/web/venv/var/web-instance
EOF
chmod +x ~/update-ladderdb.sh
```

The last step is to setup a crontab to update the database regularly; in
`crontab -e` we can for example do:
```
*/5 * * * * ~/update-ladderdb.sh
0   0 * * * rm -f ~/db-*.sqlite3
```

This will update the database every 5 minutes. And every day, we remove the
cached `db-hv-all.sqlite3` (and `db-hv-2m.sqlite3`) so that the next update
causes a full reconstruction of the databases. This is an arbitrary trade-off
to avoid spamming OpenRA user account service, and still get relatively
up-to-date information displayed.


### Frontend

The front-end is the last step. So as `web` user:

```sh
# Re-enter the virtualenv (if not already in)
. venv/bin/activate

# Install Green Unicorn (Python WSGI HTTP Server)
pip install gunicorn

# Generate a secret key
# Following https://flask.palletsprojects.com/en/1.1.x/tutorial/deploy/#configure-the-secret-key
python -c 'import os;print(f"SECRET_KEY = {repr(os.urandom(16))}")' > ~/venv/var/web-instance/config.py

# Start the service (listening on 127.0.0.1:8000)
gunicorn web:app
```

Now that the server is listening in local, we can use `nginx` to expose it to
the outside. A `nginx.conf` configuration example file is available in the
`misc` directory.

Since the outcomes are stored in UTC time in the replays, you will likely want
to align the system clock as well so that the website behaves in coordination
(typically with regards to period resets) using for example `timedatectl
set-timezone Etc/UTC`.
