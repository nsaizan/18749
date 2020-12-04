#!/bin/sh

export PYTHONPATH="${PYTHONPATH}:$PWD"

gnome-terminal -e "bash -c \"python3 $PWD/server/server.py $1 2;exec bash\"" --title="SERVER $1"
