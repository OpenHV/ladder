## Docker

The entire architecture can be set up in containerized environment using Docker images.

The following instructions only cover the Ladder and tournament website services. If you want to run an OpenHV game server with additional convenience features, check out the [game server docs](./ladder_server/README.md).

These instructions expect you to know the basics of Docker and the Docker CLI.

### Build

First, you have to build the Docker images. To streamline this process, a shell script
is packaged with this repository. Run the shell script from the repository root
directory:

```sh
.docker/build.sh
```

### Run

Export the path to your replay directory into the environment variable
`REPLAY_DIRECTORY`. Then run the RAGL or Ladder web service with the following
commands:

```sh
export REPLAY_DIRECTORY=$HOME/.config/openra/Replays/
docker run --rm --name ladder -dit -p 8001:8000 -v $REPLAY_DIRECTORY:/replays/:ro openhv/ladder:latest
```

Starts at http://127.0.0.1:8001

NB: These containers will be removed entirely when stopped due to the `--rm` flag.

### Update database

To update the database files, you can use `docker exec` as follows for the
`ladder` container:

```sh
docker exec -it ladder venv/bin/openhv-ladder -d instance/db-hv-all.sqlite3 /replays
```
