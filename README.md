# Projet L3 S6
[![Build Status](https://travis-ci.com/tag166tt/l3_s6_projet.svg?token=hfWoGD6NjtKs6Vbqwnfs&branch=master)](https://travis-ci.com/tag166tt/l3_s6_projet)
[![Dependabot](https://badgen.net/badge/Dependabot/enabled/green?icon=dependabot)](https://dependabot.com/)

## Team Members
- Yashovardhan THEVALIL SANJAY
- Nicolas BOURRAS
- Florian GUIZELIN
- Damien MARROU
- Thomas MOUTIER
- Pauline TEOULLE
- Roméo CHATEL-DESHAYES

## How to start the project?
Build scripts are included in the project to run DB migrations and setup a basic super user.

The test user is identified by :
- Username: test
- Password: test

The scripts should be run before starting the app. Thee following guide will show you how to add the proper script to run before build.

### Windows
Go to the Run/Debug Configuration page

![Run Debug Config](/readme_images/run_debug_edit.png)*

Then we need to add an action to be executed before launch

![Run Debug Plus](/readme_images/run_conf.png)

![Run Debug External Tool](/readme_images/run_conf_plus.png)

We now need to add the proper information

![Tool Config](/readme_images/tool_config.png)
