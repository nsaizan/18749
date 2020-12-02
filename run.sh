#!/bin/sh

export PYTHONPATH="${PYTHONPATH}:$PWD"

#gnome-terminal -e "bash -c \"python3 $PWD/replication-manager/replication-manager.py;exec bash\"" --title="RM"
#gnome-terminal -e "bash -c \"python3 $PWD/global-detector/global-detector.py 1;exec bash\"" --title="GFD"
#gnome-terminal -e "bash -c \"python3 $PWD/detector/detector.py 1 1;exec bash\"" --title="LFD 1"
#gnome-terminal -e "bash -c \"python3 $PWD/detector/detector.py 2 1;exec bash\"" --title="LFD 2"
#gnome-terminal -e "bash -c \"python3 $PWD/detector/detector.py 3 1;exec bash\"" --title="LFD 3"
#gnome-terminal -e "bash -c \"python3 $PWD/server/server.py 1;exec bash\"" --title="SERVER 1"
#gnome-terminal -e "bash -c \"python3 $PWD/server/server.py 2;exec bash\"" --title="SERVER 2"
#gnome-terminal -e "bash -c \"python3 $PWD/server/server.py 3;exec bash\"" --title="SERVER 3"
#gnome-terminal -e "bash -c \"python3 $PWD/client/client.py 1;exec bash\"" --title="CLIENT 1"
#gnome-terminal -e "bash -c \"python3 $PWD/client/client.py 2;exec bash\"" --title="CLIENT 2"
#gnome-terminal -e "bash -c \"python3 $PWD/client/client.py 3;exec bash\"" --title="CLIENT 3"

gnome-terminal -e "bash -c \"python3 $PWD/replication-manager/replication-manager.py;exec bash\"" --title="RM"
gnome-terminal -e "bash -c \"python3 $PWD/global-detector/global-detector.py 1;exec bash\"" --title="GFD"
gnome-terminal --tab -e "bash -c \"python3 $PWD/detector/detector.py 1 1;exec bash\"" --title="LFD 1" --tab -e "bash -c \"python3 $PWD/detector/detector.py 2 1;exec bash\"" --title="LFD 2" --tab -e "bash -c \"python3 $PWD/detector/detector.py 3 1;exec bash\"" --title="LFD 3"
gnome-terminal --tab -e "bash -c \"python3 $PWD/server/server.py 1;exec bash\"" --title="SERVER 1" --tab -e "bash -c \"python3 $PWD/server/server.py 2;exec bash\"" --title="SERVER 2" --tab -e "bash -c \"python3 $PWD/server/server.py 3;exec bash\"" --title="SERVER 3"
gnome-terminal --tab -e "bash -c \"python3 $PWD/client/client.py 1;exec bash\"" --title="CLIENT 1" --tab -e "bash -c \"python3 $PWD/client/client.py 2;exec bash\"" --title="CLIENT 2" --tab -e "bash -c \"python3 $PWD/client/client.py 3;exec bash\"" --title="CLIENT 3"
