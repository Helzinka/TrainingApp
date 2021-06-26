import re
import operator
import json

# import pyplanet extension
from pyplanet.apps.config import AppConfig
from pyplanet.utils import times
from pyplanet.contrib.command import Command
from pyplanet.apps.core.trackmania import callbacks as tmcb
from pyplanet.apps.core.maniaplanet import callbacks as mpcb

# import app view
from .views import TrainingView, TrainRecordsWidget


class TraingApp(AppConfig):

    game_dependencies = ['trackmania_next', "maniaplanet"]

    app_dependencies = ['core.trackmania', 'core.maniaplanet']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # runtime app functions

    async def on_init(self):
        await super().on_init()

    async def on_start(self):
        await super().on_start()

        # Register dedicated callbacks server functions
        self.context.signals.listen(
            mpcb.flow.loading_map_start, self.loading_map_start)
        self.context.signals.listen(tmcb.finish, self.finish)
        self.context.signals.listen(mpcb.flow.round_end, self.round_end)
        self.context.signals.listen(mpcb.flow.round_start, self.round_start)
        self.context.signals.listen(
            tmcb.warmup_start_round, self.warmup_start_round)

        # Register all commands
        await self.instance.permission_manager.register('manage_train', 'Start/stop/rank of training mode', app=self, min_level=2)

        await self.instance.command_manager.register(
            Command('train', target=self.cmdStart, admin=True, perms='training:manage_train').add_param(
                'nb_rounds', required=False, type=int, default=5, help='Set numbers of Rounds.')
        )
        await self.instance.command_manager.register(
            Command('trainrank', target=self.cmdRank,
                    admin=True, perms='training:manage_train')
        )
        await self.instance.command_manager.register(
            Command('trainstop', target=self.cmdStop,
                    admin=True, perms='training:manage_train')
        )

    async def on_stop(self):
        await super().on_stop()

    async def on_destroy(self):
        await super().on_destroy()

    # Command functions

    async def cmdStart(self, player, data, raw, command):

        if player.level >= 2:
            self.is_app_active = True
            self.player_data = list()
            self.player_finished = []
            self.nb_players = 0
            self.nb_rounds = 0
            self.nb_finish = 1
            self.on_warm_up = False
            self.load_map_end = False
            self.default_setting = {}
            self.TrainRecordsWidget = None
            self.TrainingView = None

            await self.initPLayers()
            await self.apllySetting(player, data, raw, command)

    async def cmdRank(self, player, data, raw, command):

        self.TrainingView = TrainingView(self)
        await self.TrainingView.display(player=str(player))

    async def cmdStop(self, player, data, raw, command):

        if player.level >= 2:
            if self.TrainRecordsWidget:
                await self.TrainRecordsWidget.destroy()
            elif self.TrainingView:
                await self.TrainingView.destroy()
            self.is_app_active = False

        # Main functions

    async def initPLayers(self):

        schema = {
            "rank": 0,
            "nickname": "",
            "login": "",
            "times": [],
            "avg": 0,
            "avg_raw": 0,
            "best": 0,
            "dnf": 0
        }

        for ply in self.instance.player_manager.online:
            schema["nickname"] = ply.nickname
            schema["login"] = ply.login
            self.player_data.append(dict(schema))

        self.nb_players = len(self.instance.player_manager.online)

    async def apllySetting(self, player, data, raw, command):

        self.nb_rounds = data.nb_rounds
        self.default_setting = {
            "S_WarmUpNb": 1,
            "S_WarmUpDuration": -1,
            "S_WarmUpTimeout": 0
        }
        # if player is admin
        script_mode = re.search("Rounds", await self.instance.mode_manager.get_current_script())
        # if mode is not Rounds
        if script_mode != True:
            await self.instance.command_manager.execute(player, "//mode Rounds")
        await self.instance.command_manager.execute(player, "//res")
        await self.instance.mode_manager.update_settings(self.default_setting)

        for p in self.instance.player_manager.online:
            self.TrainRecordsWidget = TrainRecordsWidget(self)
            await self.TrainRecordsWidget.display(player=p)

    async def sortResults(self):
        newlist = sorted(self.player_data,
                         key=operator.itemgetter('dnf', 'avg'))

        for ply in range(len(newlist)):
            newlist[ply]["rank"] = ply + 1

        self.player_data = newlist

    # Callback functions

    async def loading_map_start(self, time, restarted):
        # wait mode rounds if not apply and set according setting
        if self.is_app_active:

            finish_timeout = await self.instance.gbx('GetCurrentMapInfo')
            self.default_setting["S_RoundsPerMap"] = self.nb_rounds
            self.default_setting["S_PointsLimit"] = self.nb_players ^ 100
            self.default_setting["S_FinishTimeout"] = round(
                finish_timeout["AuthorTime"] / 10000 + 5) if finish_timeout["AuthorTime"] >= 30000 else 3

            pts_repartion = ""
            for i in range(self.nb_players):
                comma = "," if i < self.nb_players - 1 else ""
                pts_repartion += str(2 *
                                     (self.nb_players - i)) + comma

            self.default_setting["S_PointsRepartition"] = pts_repartion

            await self.instance.mode_manager.update_settings(self.default_setting)

    async def finish(self, player, race_time, lap_time, cps, signal, lap_cps, race_cps, flow, is_end_race, is_end_lap, raw):

        if self.is_app_active and self.on_warm_up is False:

            avg = 0
            best = 0
            # set various data onto specific player
            self.player_finished.append(str(player))

            for ply in self.player_data:
                if ply["login"] == str(player):

                    # apprend times
                    time = list(ply["times"])
                    time.append(race_time)
                    ply["times"] = time
                    ply["round" +
                        str(self.nb_finish)] = times.format_time(race_time)

                    data = ply["times"]
                    for i in range(len(data)):
                        if (i == 0):
                            best = data[i]
                        elif (data[i] <= best):
                            best = data[i]
                        avg += data[i]
                    avg = round(avg / len(data))

                    ply["avg"] = times.format_time(avg)
                    ply["avg_raw"] = avg
                    ply["best"] = times.format_time(best)

    async def round_end(self, count, time):

        if self.is_app_active and self.on_warm_up is False:

            has_finished = False
            if self.player_finished:
                for ply in self.player_data:
                    for p in self.player_finished:
                        if ply["login"] == p:
                            has_finished = True
                    if has_finished is False:
                        ply["dnf"] += 1
                        ply["round" +
                            str(self.nb_finish)] = times.format_time(0)
                    else:
                        has_finished = False
                self.player_finished = []
            else:
                for ply in self.player_data:
                    ply["dnf"] += 1
                    ply["round" +
                        str(self.nb_finish)] = times.format_time(0)

            await self.sortResults()

            if self.TrainRecordsWidget:
                for p in self.instance.player_manager.online:
                    await self.TrainRecordsWidget.refresh(player=p)

            if self.nb_finish == self.nb_rounds:
                self.is_app_active = False
            else:
                self.nb_finish += 1

    async def round_start(self, count, time):

        if self.is_app_active:
            self.on_warm_up = False

    async def warmup_start_round(self, current, total):

        if self.is_app_active:
            self.on_warm_up = True
