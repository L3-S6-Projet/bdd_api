# Projet L3 S6
[![Build Status](https://travis-ci.com/tag166tt/l3_s6_projet_bdd_api.svg?token=hfWoGD6NjtKs6Vbqwnfs&branch=master)](https://travis-ci.com/tag166tt/l3_s6_projet_bdd_api)
![Django CI Ubuntu](https://github.com/tag166tt/l3_s6_projet_bdd_api/workflows/Django%20CI%20Ubuntu/badge.svg?branch=master)
![Django CI Windows](https://github.com/tag166tt/l3_s6_projet_bdd_api/workflows/Django%20CI%20Windows/badge.svg?branch=master)
![Django CI MacOS](https://github.com/tag166tt/l3_s6_projet_bdd_api/workflows/Django%20CI%20MacOS/badge.svg?branch=master)
[![Dependabot](https://badgen.net/badge/Dependabot/enabled/green?icon=dependabot)](https://dependabot.com/)

## Supported platforms
Code is automatically tested on latest versions Windows, Ubuntu and MacOS available in Github Actions.

The project also contains necessary files to run as a container. The container build is also tested in Github Actions.

## How to start the project?
Build scripts are included in the project to run DB migrations and setup a basic super user. You first need to create a python virtual environment for the scripts to work.
The folder containing the virtual environment should be named:
- venv on Windows
- .venv on Linux

Let PyCharm create it on Windows, and if you're on Linux, you should know how to do this anyway 😊

The test user is identified by :
- Username: test
- Password: passwdtest

The scripts should be run before starting the app. Thee following guide will show you how to add the proper script to run before build.
