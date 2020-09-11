# 18749
Building Reliable Distributed Systems

## Installation

Firstly you'll need git of course to checkout the repository.

```bash
sudo apt install git
```

You should then install pip, followed by virtualenv.

```bash
sudo apt install python3-pip
pip install virtualenv
```

The repo should have a virtualenv already created in the directory env.
To enter the virtual environment you should cd into the 18642 repo and 
run the following:

```bash
. env/bin/activate
```

You can leave the virtual environment by running:

```bash
deactivate
```

To confirm that this is working as expected you can run the following
commands to see different paths for python3:

```bash
which python3
. env/bin/activate
which python3
```
