#!/usr/bin/env python
from __future__ import print_function, division

# this is main script
import numpy as np
import aiwolfpy
import aiwolfpy.contentbuilder as cb
import pandas as pd
from numpy.random import *
# sample
import aiwolfpy.puppy

myname = 'puppy'

class PythonPlayer(object):

    def __init__(self, agent_name):
        # myname
        self.myname = agent_name

        # predictor from sample
        # DataFrame -> P
        self.predicter_15 = aiwolfpy.puppy.Predictor_15()
        self.predicter_5 = aiwolfpy.puppy.Predictor_5()



    def getName(self):
        return self.myname

    def initialize(self, base_info, diff_data, game_setting):
        #print(base_info)
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
        self.executed_agent = 0
        self.not_reported = False
        self.vote_declare = 0
        self.file_num =0
        self.day_depend_fake=[0.7,0.5,0.3,0.1,0,0,0,0,0,0]
        print("agent ID is "+str(self.base_info['agentIdx']))

    def update(self, base_info, diff_data, request):
        # print(base_info)
        # print(diff_data)

        # update base_info
        self.base_info = base_info

        # result
        if request == 'DAILY_INITIALIZE':

            for i in range(diff_data.shape[0]):
                # IDENTIFY
                if diff_data['type'][i] == 'identify':
                    self.not_reported = True
                    self.myresult = diff_data['text'][i]

                # DIVINE
                if diff_data['type'][i] == 'divine':
                    self.not_reported = True
                    self.myresult = diff_data['text'][i]

                # GUARD
                if diff_data['type'][i] == 'guard':
                    self.myresult = diff_data['text'][i]
                # GUARD
                if diff_data['type'][i] == 'execute':
                    self.executed_agent = int(diff_data['agent'][i])
            # POSSESSED
            if (self.base_info['myRole'] == 'POSSESSED') or (self.base_info['myRole'] == 'WEREWOLF') and self.comingout != '':
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

            else:
                # update pred
                self.predicter_15.update(diff_data)

        else:
            self.predicter_5.update(diff_data)



    def dayStart(self):
        self.vote_declare = 0
        self.talk_turn = 0
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
                self.comingout = 'SEER'
                return cb.comingout(self.base_info['agentIdx'], self.comingout)

            elif self.base_info['myRole'] == 'WEREWOLF' and self.comingout == '' and self.base_info["day"] > 1:
                if self.predicter_15.num_seer() < 2 and rand() < 0.3: 
                    self.comingout = 'SEER'
                    return cb.comingout(self.base_info['agentIdx'], self.comingout)
                elif self.predicter_15.num_seer() > 1 and self.predicter_15.num_medium() < 2 and rand() < 0.3: 
                    self.comingout = 'MEDIUM'
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
                # FAKE
                if  self.comingout == 'SEER':
                    return self.fake_seer_result()
                elif  self.comingout == 'MEDIUM':
                    return self.fake_medium_result()

            elif self.base_info['myRole'] == 'WEREWOLF' and self.not_reported:
                self.not_reported = False
                # FAKE
                if  self.comingout == 'SEER':
                    return self.fake_seer_result()
                elif  self.comingout == 'MEDIUM':
                    return self.fake_medium_result()
            # 3.declare vote if not yet
            if self.vote_declare != self.vote():
                self.vote_declare = self.vote()
                return cb.vote(self.vote_declare)

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
            elif self.base_info['myRole'] == 'MEDIUM' and self.comingout == '':
                self.comingout = 'MEDIUM'
                return cb.comingout(self.base_info['agentIdx'], self.comingout)
            elif self.base_info['myRole'] == 'POSSESSED' and self.comingout == '':
                self.comingout = 'SEER'
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

                return self.fake_seer()

            # 3.declare vote if not yet
            if self.vote_declare != self.vote():
                self.vote_declare = self.vote()
                return cb.vote(self.vote_declare)

            # 4. skip
            if self.talk_turn <= 10:
                return cb.skip()

            return cb.over()

    def whisper(self):
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
                        p0 *= self.day_depend_fake[self.base_info["day"]]
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
            elif self.base_info['myRole'] == "POSSESSED":
                p = 1
                idx = 1
                for i in range(1, 16):
                    p0 = p0_mat[i-1, 1]
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 < p:
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
            p0_mat = self.predicter_15.ret_pred_wn()
            for i in range(1, 16):
                p0 = p0_mat[i-1, 1]
                if self.base_info['statusMap'][str(i)] == 'ALIVE' and i not in self.divined_list and p0 > p:
                    p = p0
                    idx = i
            self.divined_list.append(idx)
            return idx
        else:
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
        pass

    def fake_seer(self):
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
    def fake_seer_result(self):
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
    def fake_medium_result(self):
        self.myresult = 'IDENTIFIED Agent[' + "{0:02d}".format(self.executed_agent) + '] ' + 'HUMAN'
        return self.myresult   
agent = PythonPlayer(myname)

# run
if __name__ == '__main__':
    aiwolfpy.connect_parse(agent)