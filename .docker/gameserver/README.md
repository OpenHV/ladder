# OpenHV Ladder Game Server Dockerfile
This uses the [official OpenHV Dockerfile](https://github.com/OpenHV/Server).

## Configuration
To setup a game server that records replays and stores them outside the container on the host use the following shell script:

```sh
RELEASE=20250628
PORT=1235

docker run -dit \
    -p $PORT:$PORT \
    -e TZ=UTC \
    -v $HOME/.config/openra/Replays/hv/$RELEASE/:/root/.config/openra/Replays/hv/$RELEASE/ \
    --restart always \
    --name ladder_gameserver \
    docker.io/openhv/server:$RELEASE \
    "Server.Name=Competitive 1v1 Ladder" \
    "Server.RequireAuthentication=True" \
    "Server.EnableSingleplayer=False" \
    "Server.RecordReplays=True" \
    "Server.ListenPort=$PORT"
```
