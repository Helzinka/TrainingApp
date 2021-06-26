# Training App

This plugin offer some data about your regularity in rounds mode. 
One side it show average and your rank and in an other side your best rounds, cp time, average and more !

## Installation

- On your **Pyplanet** folder, create if not exist a folder name **apps** and put this plugin.

- Secondly on **settings** folder, edit your **apps.py** with :

```python
APPS = {
	'default': [
		'pyplanet.apps.contrib.admin',
		#'pyplanet.apps.contrib.jukebox',
		#'pyplanet.apps.contrib.karma',
		'apps.TrainingApp.training'
    ]}
```

> apps here means training parent's folder

## Commands in Game

- //train 8 = Will start plugin with the round mode for 8 rounds (5 rounds default).

- //trainrank = Only available at the end of the Match. It'll show you more data about previous rounds ended.

- //trainstop = Destroy and hide view of plugins


> To restart plugins simply retype **//train** command.

### Have fun ! 

