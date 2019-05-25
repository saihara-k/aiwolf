# -*- coding: utf-8 -*-
#!/usr/bin/env python
from __future__ import print_function, division

import aiwolfpy
import aiwolfpy.contentbuilder as cb

import numpy as np
import pandas as pd

import random
import re

class WinCount:
    def __init__(self):
        self.win_count = {'BODYGUARD':0, 'MEDIUM':0, 'POSSESSED':0,
        'SEER':0, 'VILLAGER':0, 'WEREWOLF':0}
        self.asign_count = {'BODYGUARD':0, 'MEDIUM':0, 'POSSESSED':0,
        'SEER':0, 'VILLAGER':0, 'WEREWOLF':0}
        self.game_count = 0
        self.others_win_count = {i:0 for i in range(1,16)}

    def initialize(self):
        self.is_finish = False
        # 強いエージェント探す
        strong_agents=[]
        if self.game_count>=50:
            for k,v in self.others_win_count.items():
                if v/self.game_count>0.7:
                    strong_agents.append(k)
        return strong_agents


    def finish(self, base_info, diff_data):
        self.game_count += 1
        #agent_data = []

        diff_data['role']=[row.split(' ')[-1] for row in diff_data['text']]
        diff_data['idx'] = diff_data['idx'].astype('str')
        df_role = diff_data[['idx', 'role']]
        df_base=pd.DataFrame(base_info)
        df_base=pd.merge(df_base, df_role, left_index=True, right_on='idx')

        is_werewolf_win = 'ALIVE' in df_base[df_base['role']=='WEREWOLF']['statusMap'].values
        myRole=base_info['myRole']
        self.win_count[myRole]+=is_win(myRole, is_werewolf_win)
        self.asign_count[myRole]+=1
        if is_werewolf_win:
            for idx,data  in df_base.iterrows():
                if data['role']=='WEREWOLF' or data['role']=='POSSESSED':
                    self.others_win_count[int(data['idx'])]+=1
        else:
            for idx,data  in df_base.iterrows():
                if data['role']!='WEREWOLF' or data['role']!='POSSESSED':
                    self.others_win_count[int(data['idx'])]+=1


    def get(self):
        return self.win_count

    def finish_term(self, game_num):
        try:
            if self.game_count == game_num:
                print({k:v/self.asign_count[k] for k,v in self.win_count.items() if self.asign_count[k]!=0})
                print('total:{}'.format(sum(self.win_count.values())/game_num))
        except:
             return None

def is_win(myRole, is_werewolf_win):
    if myRole in ['WEREWOLF', 'POSSESSED']:
        if is_werewolf_win:
            return 1
    else:
        if not is_werewolf_win:
            return 1
    return 0
