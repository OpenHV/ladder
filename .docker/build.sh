#!/bin/sh
#
# Build OpenHV Ladder Docker images
#
# Run from project root directory (not within ".docker" directory)

cp .docker/Dockerfile .

docker build -t openhv/ladder:latest -f Dockerfile .

rm Dockerfile