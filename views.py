from pyplanet.views.generics.list import ManualListView
from pyplanet.views.generics.widget import TimesWidgetView


class TrainingView(ManualListView):

    def __init__(self, app):
        super().__init__(self)
        self.app = app
        self.manager = app.context.ui

    async def get_fields(self):
        self.index = [{
            'name': 'Rank',
            'index': "rank",
            'sorting': True,
            'width': 10,
            'type': 'label'

        },
            {
            'name': 'Player',
            'index': 'nickname',
            'sorting': True,
            'searching': True,
            'width': 30,
        },
            {
            'name': 'Dnf',
            'index': 'dnf',
            'sorting': True,
            'width': 10,
        },
            {
            'name': 'Best',
            'index': 'best',
            'sorting': True,
            'width': 20,
        },
            {
            'name': 'Average',
            'index': 'avg',
            'sorting': True,
            'width': 20,
        }]

        await self.get_custom_index()

        return self.index

    async def get_data(self):

        data = self.app.player_data

        return data

    async def get_title(self):
        return 'Training on {}'.format(self.app.instance.map_manager.current_map.name)

    ## utils func ##

    async def get_custom_index(self):

        self.width = 20 if self.app.nb_finish <= 5 else 10
        self.pos = 2

        if self.app.nb_finish == self.app.nb_rounds:
            for f in range(self.app.nb_finish):
                round = {
                    'name': "Rounds " + str(f+1),
                    'index': "round" + str(f+1),
                    'sorting': True,
                    'width': self.width,
                }
                self.index.insert(self.pos, round)
                self.pos += 1


class TrainRecordsWidget(TimesWidgetView):
    widget_x = 125
    widget_y = 56.5
    z_index = 30
    top_entries = 5
    title = 'Training Average'

    def __init__(self, app):
        super().__init__(self)
        self.app = app
        self.manager = app.context.ui
        self.id = 'pyplanet__widgets_localrecords'

    async def get_context_data(self):

        context = await super().get_context_data()

        current_rank = []

        for ply in self.app.player_data:
            data = {
                "index": ply["rank"],
                "nickname": ply["nickname"],
                "score": ply["avg"]
            }
            current_rank.append(dict(data))

        context.update({
            'times': current_rank
        })

        return context
