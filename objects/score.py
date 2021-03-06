from objects import glob, db
from enum import IntEnum, unique

from utils.pp import PPCalculator, modsBitsFromDroidStr

@unique
class SubmissionStatus(IntEnum):
    # totally not copied from gulag
    FAILED = 0
    SUBMITTED = 1
    BEST = 2

    def __repr__(self) -> str:
        return {
            self.FAILED: 'Failed',
            self.SUBMITTED: 'Submitted',
            self.BEST: 'Best'
        }[self.value]

class Score:
    ''' 
    i cant wrap my head around score submission so this one is based from gulag

    <3 cmyui
    '''

    def __init__(self):
        self.id = None

        self.map_hash = None
        self.player = None

        self.pp = None
        self.map = None
        self.score = None
        self.max_combo = None
        self.mods = None

        self.acc = None

        self.h300 = None
        self.h100 = None
        self.h50 = None
        self.hmiss = None
        self.hgeki = None
        self.hkatsu = None
        self.grade = None

        self.rank = None
        self.fc = None
        self.status = SubmissionStatus.SUBMITTED
        #self.passed = None # droid doesnt have this
        #self.perfect = None
        self.device_id = None # unused

        self.prev_best = None

    @classmethod
    async def from_sql(cls, score_id: int):
        res = await glob.db.getPlay(score_id)

        if not res:
            return

        s = cls()

        s.id = res['id']
        s.player = await glob.players.get(id=int(res['playerID']))
        s.status = SubmissionStatus(res['status'])
        s.mapHash = res['mapHash']

        
        s.score = res['score']
        s.max_combo = res['combo']
        s.mods = res['mods']
        s.acc = res['acc']
        s.grade = res['rank']
        

        s.h300 = res['hit300']
        s.h100 = res['hit100']
        s.h50 = res['hit50']
        s.hmiss = res['hitmiss']
        s.hgeki = res['hitgeki']
        s.hkatsu = res['hitkatsu']

        s.pp = await PPCalculator.from_md5(s.mapHash, mods=s.mods, combo=s.max_combo, nmiss=s.hmiss, acc=s.acc)
        if s.pp:
            s.pp = await s.pp.calc()
        
        if s.mapHash:
            s.rank = await s.calc_lb_placement()
            
        return s

    @classmethod
    async def from_submission(cls, data: dict):
        data = data.split('+')

        s = cls()

        pname = data[13]
        s.player = await glob.players.get(name=pname)
        

        if not s.player:
            # refer to gulag score.py
            return s
        
        s.mapHash = s.player.stats.playing
        s.pp = await PPCalculator.from_md5(s.mapHash)

        (s.score, s.max_combo) = map(int, data[1:3])
        (s.hgeki, s.h300, s.hkatsu, s.h100, s.h50,
            s.hmiss) = map(int, data[4:10])

        s.mods = data[0]
        s.grade = data[3]
        s.acc = float(data[10])/1000
        s.fc = data[12] == 'true'
        s.device_id = data[11]

        s.pp = await PPCalculator.from_md5(s.mapHash, mods=s.mods, combo=s.max_combo, nmiss=s.hmiss, acc=s.acc)

        if s.pp:
            s.pp = await s.pp.calc()

        if s.mapHash:
            await s.calc_status()
            s.rank = await s.calc_lb_placement()
            

        return s


    async def calc_lb_placement(self):
        res = await glob.db.fetch("select count(*) as c from scores where mapHash = ? and score > ?", [self.mapHash, self.score])
        return int(res[0]['c']) + 1 if res else 1

    

    async def calc_status(self):
        res = await glob.db.userScore(id=self.player.id, mapHash=self.mapHash)

        if res:
            self.prev_best = await Score.from_sql(res['id'])

            if self.score > res['score']:
                self.status = SubmissionStatus.BEST
                self.prev_best.status = SubmissionStatus.SUBMITTED
            
        else:
            self.status = SubmissionStatus.BEST

            