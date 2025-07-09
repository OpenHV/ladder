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

## Production

The web services can be run in Docker containers. Please refer to the
[Wiki](https://github.com/OpenHV/ladder/wiki) for more information.

```sh
docker build -t openhv/ladder:latest -f Dockerfile .
```

```sh
docker run --name ladder -dit -p 8001:8000 openhv/ladder:latest
```

Runs at http://127.0.0.1:8001
