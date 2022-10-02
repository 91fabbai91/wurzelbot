# (More pythonic) Wurzelbot

Automate your account in Wurzelimperium

## Description

This python tool is for automation of accounts in the browser game Wurzelimperium.
This repo is mainly inspired by MrFlamez WurzelimperiumBot on github

### Features
* Grow plants automatically
  * Grow plants according to different kinds of quests
* Water plante automatically
* Renew items in town park
* Empty cash point in town park
* and many more ...

## Getting Started

### Dependencies

* Python 3.8
* Poetry
* Docker/podman (if you want to run it inside a container)


### Executing program (without container)

* Clone repo into the folder of your choice
* Put a config yaml file into the config folder (default filename: config.yaml)
* Install the dependencies with poetry ```poetry install```
* Run main.py with ```poetry run python main.py```

### Executing program (with container)

* Clone repo into the folder of your choice
* Put a config yaml file into the config folder (default filename: config.yaml)
* Build the container with podman or docker  ```docker build . -t <name-of-your-choice>```
* Run the container with podman or docker ```docker run -v $(pwd)/config:/code/config <name-of-your-choice>```

## Authors

Contributors names and contact info

91fabbai91 - Fabian Baier

## License

This project is licensed under the MIT-License - see the LICENSE.md file for details

## Acknowledgments

Inspiration, code snippets, etc.
* [WurzelimperiumBot](https://github.com/MrFlamez/Wurzelimperium-Bot)

## Ideas for further steps

* Sell automatically fruits and vegetables
* Improve unit Tests
* Command line interface
* Tutorial to run this as a batch job in Cloud environments

