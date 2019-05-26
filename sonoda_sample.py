#!/usr/bin/env python -u
from __future__ import print_function, division

# this is main script

import aiwolfpy
import aiwolfpy.contentbuilder as cb
import numpy as np
# sample
import aiwolfpy.cash
# import time
# myname = 'cantar{}'.format(str(time.time())[-2:])
myname = 'cantar'
import win_count


class PythonPlayer(object):

    def __init__(self, agent_name):
        # myname
        self.myname = agent_name

        # predictor from sample
        # DataFrame -> P
        self.predicter_15 = aiwolfpy.cash.Predictor_15()
        self.predicter_5 = aiwolfpy.cash.Predictor_5()
        self.win_count = win_count.WinCount()
        self.strong_agents = []


    def getName(self):
        return self.myname

    def initialize(self, base_info, diff_data, game_setting):
        # print(base_info)
        # print(diff_data)
        # base_info
        self.base_info = base_info
        # game_setting
        self.game_setting = game_setting

        # initialize
        if self.game_setting['playerNum'] == 15:
            self.predicter_15.initialize(base_info, game_setting)
        elif self.game_setting['playerNum'] == 5:
            self.predicter_5.initialize(base_info, game_setting)

        ### EDIT FROM HERE ###
        self.divined_list = []
        self.comingout = ''
        self.myresult = ''
        self.not_reported = False
        self.vote_declare = 0
        self.strong_agents = self.win_count.initialize()
        self.try_pp_block = False
        self.co_dict = {}
        self.pretend_seer = False
        self.pretend_medium = False
        


    def update(self, base_info, diff_data, request):
        # print(base_info)
        # print(diff_data)
        # print(request)
        # update base_info
        self.base_info = base_info
        print(self.co_dict)

        # result
        if request == 'DAILY_INITIALIZE':
            for i in range(diff_data.shape[0]):
                # IDENTIFY
                if diff_data['type'][i] == 'identify':
                    print(diff_data)
                    self.not_reported = True
                    self.myresult = diff_data['text'][i]

                # DIVINE
                if diff_data['type'][i] == 'divine':
                    self.not_reported = True
                    self.myresult = diff_data['text'][i]

                # GUARD
                if diff_data['type'][i] == 'guard':
                    self.myresult = diff_data['text'][i]

            # POSSESSED
            if self.base_info['myRole'] == 'POSSESSED':
                self.not_reported = True

        # UPDATE
        if self.game_setting['playerNum'] == 15:
            if self.base_info["day"] == 0 and request == 'DAILY_INITIALIZE' and self.game_setting['talkOnFirstDay'] == False:
                # update pred
                self.predicter_15.update_features(diff_data)
                self.predicter_15.update_df()

            elif self.base_info["day"] == 0 and request == 'DAILY_FINISH' and self.game_setting['talkOnFirstDay'] == False:
                # no talk at day:0
                self.predicter_15.update_pred()

            elif self.base_info['day'] == 0 and request == 'WHISPER':
                contents = []
                for i in range(diff_data.shape[0]):
                    content = diff_data.text[i].split()
                    if content[0] == 'COMINGOUT' and diff_data['agent'][i] != self.base_info['agentIdx']:
                        contents.append(content[2])
                if contents.count('SEER')>0:
                    self.pretend_seer = False
                    if contents.count('MEDIUM') >0:
                        self.comingout = 'VILLAGER'
                    else:
                        self.pretend_medium = True
                        self.comingout = 'MEDIUM'
                else:
                    self.pretend_seer = True
                    self.comingout = 'SEER'
            elif request == 'TALK':
                for i in range(diff_data.shape[0]):
                    content = diff_data.text[i].split()
                    if content[0] == 'COMINGOUT' and diff_data['agent'][i] != self.base_info['agentIdx']:
                        self.co_dict[diff_data['agent'][i]] = content[2]
            else:
                # update pred
                self.predicter_15.update(diff_data)
        else:
            if self.base_info['day'] == 2 and request == 'TALK':
                contents = []
                for i in range(diff_data.shape[0]):
                    content = diff_data.text[i].split()
                    if content[0] == 'COMINGOUT':
                        contents.append(content[2])
                if 'POSSESSED' in contents and 'WEREWOLF' in contents:
                    self.try_pp_block = 1
            self.predicter_5.update(diff_data)

        if request == 'FINISH':
            if self.win_count.is_finish == True:
                return None
            self.win_count.is_finish = True
            self.win_count.finish(base_info, diff_data)



    def dayStart(self):
        self.vote_declare = 0
        self.talk_turn = 0
        self.estimated = False
        return None

    def talk(self):
        
        if self.game_setting['playerNum'] == 15:

            self.talk_turn += 1

            # 1.comingout anyway
            if self.base_info['myRole'] == 'SEER' and self.comingout == '':
                self.comingout = 'SEER'
                return cb.comingout(self.base_info['agentIdx'], self.comingout)
            elif self.base_info['myRole'] == 'MEDIUM' and self.comingout == '':
                self.comingout = 'MEDIUM'
                return cb.comingout(self.base_info['agentIdx'], self.comingout)
            elif self.base_info['myRole'] == 'POSSESSED' and self.comingout == '':
                if np.random.rand() < 0.5:
                    self.comingout = 'SEER'
                    self.pretend_seer = True
                else:
                    self.comingout = 'MEDIUM'
                    self.pretend_medium = True
                return cb.comingout(self.base_info['agentIdx'], self.comingout)

            # 1.2 ww pretend seer
            elif self.base_info['myRole'] == 'WEREWOLF':
                if self.pretend_seer and self.base_info['day'] == 1 and self.talk_turn <= 1:
                    self.comingout = 'SEER'
                # 毎日、毎ターン霊媒師だと訴え続ける
                elif self.pretend_medium:
                    self.comingout = 'MEDIUM'
                return cb.comingout(self.base_info['agentIdx'], self.comingout)

            # 1.3 pp
            # if self.base_info['statusMap'].values().count('ALIVE') == 4:
            #     if self.base_info['myRole']

            # 2.report
            if self.base_info['myRole'] == 'SEER' and self.not_reported:
                self.not_reported = False
                return self.myresult
            elif self.base_info['myRole'] == 'MEDIUM' and self.not_reported:
                self.not_reported = False
                return self.myresult
            elif self.pretend_seer and self.not_reported:       
                self.not_reported = False
                # FAKE DIVINE
                # highest prob ww in alive agents
                p = -1
                idx = 1
                p0_mat = self.predicter_15.ret_pred()
                for i in range(1, 16):
                    p0 = p0_mat[i-1, 1]
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
                self.myresult = 'DIVINED Agent[' + "{0:02d}".format(idx) + '] ' + 'HUMAN'
                return self.myresult

            # 3.declare vote if not yet
            if self.vote < 0.3:
                return cb.skip()
            if self.vote_declare != self.vote():
                if self.estimated:
                    self.vote_declare = self.vote()
                    return cb.vote(self.vote_declare)
                else:
                    self.estimated = True
                    if self.base_info['myRole'] not in ['WEREWOLF', 'POSSESSED']:
                        return cb.estimate(self.vote(), 'WEREWOLF')
                    else:
                        tmp_myRole, self.base_info['myRole'] = self.base_info['myRole'], 'VILLAGER'
                        fake_vote = self.vote()
                        self.base_info['myRole'] = tmp_myRole
                        return cb.estimate(fake_vote, 'WEREWOLF')

            # 4. skip
            if self.talk_turn <= 10:
                return cb.skip()

            return cb.over()
        else:
            self.talk_turn += 1

            # 1.comingout anyway
            if self.base_info['myRole'] == 'SEER' and self.comingout == '':
                self.comingout = 'SEER'
                return cb.comingout(self.base_info['agentIdx'], self.comingout)
            # elif self.base_info['myRole'] == 'MEDIUM' and self.comingout == '':
            #     self.comingout = 'MEDIUM'
                # return cb.comingout(self.base_info['agentIdx'], self.comingout)
            elif self.base_info['myRole'] == 'POSSESSED' and self.comingout == '':
                self.comingout = 'SEER'
                return cb.comingout(self.base_info['agentIdx'], self.comingout)

            # 1.2 PP sonoda added
            if self.base_info["day"] == 2 and self.base_info['myRole'] == 'POSSESSED':
                self.comingout = 'POSSESSED'
                return cb.comingout(self.base_info['agentIdx'], self.comingout)

            # 1.3 PP-Block
            if self.base_info['day'] == 2 and self.base_info['myRole'] == 'VILLAGER' and self.try_pp_block:
                self.comingout = 'WEREWOLF'
                return cb.comingout(self.base_info['agentIdx'], self.comingout)

            # 2.report
            if self.base_info['myRole'] == 'SEER' and self.not_reported:
                self.not_reported = False
                return self.myresult
            elif self.base_info['myRole'] == 'MEDIUM' and self.not_reported:
                self.not_reported = False
                return self.myresult
            elif self.base_info['myRole'] == 'POSSESSED' and self.not_reported:
                self.not_reported = False
                # FAKE DIVINE
                # highest prob ww in alive agents
                p = -1
                idx = 1
                p0_mat = self.predicter_5.ret_pred_wx(2)
                for i in range(1, 6):
                    p0 = p0_mat[i-1, 1]
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
                self.myresult = 'DIVINED Agent[' + "{0:02d}".format(idx) + '] ' + 'HUMAN'
                return self.myresult

            # 3.declare vote if not yet
            if self.vote_declare != self.vote():
                self.vote_declare = self.vote()
                return cb.vote(self.vote_declare)

            # 4. skip
            if self.talk_turn <= 10:
                return cb.skip()

            return cb.over()

    def whisper(self):
        if self.base_info['day'] == 0:
            return cb.comingout(self.base_info['agentIdx'], self.comingout)
        return cb.skip()

    def vote(self):
        if self.game_setting['playerNum'] == 15:
            p0_mat = self.predicter_15.ret_pred_wn()
            if self.base_info['myRole'] == "WEREWOLF":
                p = -1
                idx = 1
                for i in range(1, 16):
                    p0 = p0_mat[i-1, 1]
                    if str(i) in self.base_info['roleMap'].keys():
                        p0 *= np.random.rand()
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
            elif self.base_info['myRole'] == "POSSESSED":
                p = -1
                idx = 1
                for i in range(1, 16):
                    p0 = p0_mat[i-1, 1]
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
            else:
                # highest prob ww in alive agents provided watashi ningen
                p = -1
                idx = 1
                for i in range(1, 16):
                    p0 = p0_mat[i-1, 1]
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
            return idx
        else:
            if self.base_info['myRole'] == "WEREWOLF":
                p0_mat = self.predicter_5.ret_pred_wx(1)
                p = -1
                idx = 1
                for i in range(1, 6):
                    p0 = p0_mat[i-1, 3]
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
            elif self.base_info['myRole'] == "POSSESSED":
                p0_mat = self.predicter_5.ret_pred_wx(2)
                p = -1
                idx = 1
                for i in range(1, 6):
                    p0 = p0_mat[i-1, 3]
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
            elif self.base_info['myRole'] == "SEER":
                p0_mat = self.predicter_5.ret_pred_wx(3)
                p = -1
                idx = 1
                for i in range(1, 6):
                    p0 = p0_mat[i-1, 1]
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
            else:

                # if 
                p0_mat = self.predicter_5.ret_pred_wx(0)
                p = -1
                idx = 1
                for i in range(1, 6):
                    p0 = p0_mat[i-1, 1]
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
            return idx

    def attack(self):
        if self.game_setting['playerNum'] == 15:
            # 対抗を殺す
            ids = self.co_dict.keys()
            for idx in ids:
                if self.base_info['statusMap'][str(idx)] == 'DEAD':
                    del self.co_dict[idx]
            
            for idx in self.co_dict.keys():
                if not str(idx) in self.base_info['roleMap'].keys():
                    return idx
            # highest prob hm in alive agents
            p = -1
            idx = 1
            p_list = []
            idx_list = []
            p0_mat = self.predicter_15.ret_pred()
            for i in range(1, 16):
                p0 = p0_mat[i-1, 0]
                if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                    p_list.append(p)
                    idx_list.append(idx)
                    p = p0
                    idx = i
            # if 1st-higest prob - Nnd-higest prob < 5%
            # then 脅威噛み 
            for np, nidx in zip(p_list,idx_list):
                if p - np < 0.05 and len(self.strong_agents)>0:
                    for i in self.strong_agents:
                        if self.base_info['statusMap'][str(i)] == 'ALIVE' and int(i) != self.base_info['agentIdx']:
                            if nidx == i:
                                return nidx
            return idx
        else:
            # 脅威噛み
            if len(self.strong_agents)>0:
                for i in self.strong_agents:
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and int(i) != self.base_info['agentIdx']:
                        return int(i)
            # lowest prob ps in alive agents
            p = 1
            idx = 1
            p0_mat = self.predicter_5.ret_pred_wx(1)
            for i in range(1, 6):
                p0 = p0_mat[i-1, 2]
                if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 < p and i != self.base_info['agentIdx']:
                    p = p0
                    idx = i

            return idx

    def divine(self):
        if self.game_setting['playerNum'] == 15:
            # highest prob ww in alive and not divined agents provided watashi ningen
            p = -1
            idx = 1
            p_list = []
            idx_list = []
            p0_mat = self.predicter_15.ret_pred_wn()
            for i in range(1, 16):
                p0 = p0_mat[i-1, 1]
                if self.base_info['statusMap'][str(i)] == 'ALIVE' and i not in self.divined_list and p0 > p:
                    p_list.append(p)
                    idx_list.append(idx)
                    p = p0
                    idx = i
            # 脅威占い
            for np, nidx in zip(p_list, idx_list):
                if p - np < 0.1 and len(self.strong_agents)>0:
                    for i in self.strong_agents:
                        if self.base_info['statusMap'][str(i)] == 'ALIVE' and int(i) != self.base_info['agentIdx']:
                            if nidx == i:
                                self.divined_list.append(nidx)
                                return nidx
   
            self.divined_list.append(idx)
            return idx
        else:
            # 脅威噛み
            if len(self.strong_agents)>0:
                for i in self.strong_agents:
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and int(i) != self.base_info['agentIdx']:
                        return int(i)
            # highest prob ww in alive and not divined agents provided watashi ningen
            p = -1
            idx = 1
            p0_mat = self.predicter_5.ret_pred_wx(3)
            for i in range(1, 6):
                p0 = p0_mat[i-1, 1]
                if self.base_info['statusMap'][str(i)] == 'ALIVE' and i not in self.divined_list and p0 > p:
                    p = p0
                    idx = i
            self.divined_list.append(idx)
            return idx

    def guard(self):
        if self.game_setting['playerNum'] == 15:
            # highest prob hm in alive agents
            p = -1
            idx = 1
            p0_mat = self.predicter_15.ret_pred()
            for i in range(1, 16):
                p0 = p0_mat[i-1, 0]
                if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                    p = p0
                    idx = i
            return idx
        else:
            # no need
            return 1

    def finish(self):
        game_num=100
        self.win_count.finish_term(game_num)
        pass



agent = PythonPlayer(myname)

# run
if __name__ == '__main__':
    aiwolfpy.connect(agent)
