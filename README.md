# Scolendar API
[![Build Status](https://travis-ci.com/tag166tt/l3_s6_projet_bdd_api.svg?token=hfWoGD6NjtKs6Vbqwnfs&branch=master)](https://travis-ci.com/tag166tt/l3_s6_projet_bdd_api)
![Django CI Ubuntu](https://github.com/tag166tt/l3_s6_projet_bdd_api/workflows/Django%20CI%20Ubuntu/badge.svg?branch=master)
![Django CI Windows](https://github.com/tag166tt/l3_s6_projet_bdd_api/workflows/Django%20CI%20Windows/badge.svg?branch=master)
![Django CI MacOS](https://github.com/tag166tt/l3_s6_projet_bdd_api/workflows/Django%20CI%20MacOS/badge.svg?branch=master)
[![Dependabot](https://badgen.net/badge/Dependabot/enabled/green?icon=dependabot)](https://dependabot.com/)

## Table of contents
  * [Supported platforms](#supported-platforms)
  * [How to start the server](#how-to-start-the-server)
  * [Use the API](#use-the-api)

## Supported platforms
Code is automatically tested on latest versions Windows, Ubuntu and MacOS available in Github Actions.

The project also contains necessary files to run as a container. The container build is also tested in Github Actions.

Project is tested with the following Python versions:
- 3.6
- 3.7
- 3.8

## How to start the server
The project can be run in a container.

>From the information I gathered, to run Docker on Windows, you either need Windows 10 Pro, or Windows 10 Home 2004 with the WSL2 backend enabled.

Just type the following command to build and run the container
```shell script
docker-compose up --force-recreate --build api
```

## Use the API
All test users have the same password : `passwdtest`.
Their usernames are:
- Super user: `super`
- Admin: `admin`
- Student: same as in test server `{first_name}.{last_name}`
- Teacher: same as in test server `{first_name}.{last_name}`

**All default usernames do not contain special characters or spaces.**

A default class is also created: `L3 Informatique`.
