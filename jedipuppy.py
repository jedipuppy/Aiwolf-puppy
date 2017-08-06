#!/usr/bin/env python
from __future__ import print_function, division

# this is main script
import numpy as np
import aiwolfpy
import aiwolfpy.contentbuilder as cb
import pandas as pd
from numpy.random import *
import math
# sample
import aiwolfpy.puppy

myname = 'jedipuppy'

class PythonPlayer(object):

    def __init__(self, agent_name):
        # myname
        self.myname = agent_name

        # predictor from sample
        # DataFrame -> P
        self.predicter_15 = aiwolfpy.puppy.Predictor_15()
        self.predicter_5 = aiwolfpy.puppy.Predictor_5()
        self.guard_factor = [[15,15],[15,15],[15,15]]
        self.attack_result = np.zeros([15,3])
        self.threat_factor = np.ones([15,15])

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
        self.estimate_werewolf = 0 
        self.estimate_villager = 0       
        self.file_num =0
        self.day_depend_fake=[0.9,0.7,0.5,0.3,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2]
        self.attacked_agent = [-1,-1,-1]


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
                # EXECUTE
                if diff_data['type'][i] == 'execute':
                    self.executed_agent = int(diff_data['agent'][i])

            #
            voteList = self.base_info['voteList']
            if len(voteList) != 0:
                for l in voteList:
                    if l['target'] == self.base_info['agentIdx']:
                        self.threat_factor[int(self.base_info['day']-1)][int(l['agent'])-1] *= 1.01

            #Attacked 
            if self.base_info['day'] < 5: 
                self.attacked_agent[int(self.base_info['day'])-2] = self.seek_attacked()

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
            elif self.base_info['myRole'] == 'MEDIUM' and self.comingout == '' and self.base_info["day"] > 1:
                self.comingout = 'MEDIUM'
                return cb.comingout(self.base_info['agentIdx'], self.comingout)

            elif self.base_info['myRole'] == 'POSSESSED' and self.comingout == '':
                if self.predicter_15.num_seer() < 2 and rand() < 0.5: 
                    self.comingout = 'SEER'
                    return cb.comingout(self.base_info['agentIdx'], self.comingout)


            elif self.base_info['myRole'] == 'WEREWOLF' and self.comingout == '' and self.base_info["day"] == 2:
                if self.predicter_15.num_seer() > 1 and self.predicter_15.num_medium() < 2 and rand() <0.1: 
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
                    return self.possessed_seer_result()
                elif  self.comingout == 'MEDIUM':
                    return self.fake_medium_result()

            elif self.base_info['myRole'] == 'WEREWOLF' and self.not_reported:
                self.not_reported = False
                # FAKE
                if  self.comingout == 'SEER':
                    return self.werewolf_seer_result()
                elif  self.comingout == 'MEDIUM':
                    return self.fake_medium_result()
            # 3.declare vote if not yet
            if self.vote_declare != self.vote_declare_func():
                if self.vote_prob() > 0.6:
                    self.vote_declare = self.vote_declare_func()
                    return cb.vote(self.vote_declare)

            # 3.estimate werewolf if not yet
            if self.estimate_werewolf != self.vote():
                if self.vote_prob() > 0.8:
                    self.estimate_werewolf = self.vote_declare_func()
                    return cb.estimate(self.estimate_werewolf,'WEREWOLF')
            # 3.estimate villager if not yet
            if self.estimate_villager != self.estimate_villager_func():
                if self.villager_prob() > 0.2:
                    self.estimate_villager = self.estimate_villager_func()
                    return cb.estimate(self.estimate_villager,'VILLAGER')


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
            elif self.base_info['myRole'] == 'POSSESSED' and self.comingout == ''  and self.base_info["day"] == 2:
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

                #return self.fake_seer()

            # 3.declare vote if not yet
            if self.vote_declare != self.vote():
                self.vote_declare = self.vote()
                return cb.vote(self.vote_declare)
            # 3.estimate werewolf if not yet
            if self.base_info['myRole'] == "POSSESSED":
                if self.estimate_werewolf != self.vote():
                    if self.vote_prob() > 0.8:
                        self.estimate_werewolf = self.vote_declare_func()
                        return cb.estimate(self.estimate_werewolf,'HUMAN')
            # 3.estimate villager if not yet
                if self.estimate_villager != self.estimate_villager_func():
                    if self.villager_prob() > 0.2:
                        self.estimate_villager = self.estimate_villager_func()
                        return cb.estimate(self.estimate_villager,'WEREWOLF')
            else:
                if self.estimate_werewolf != self.vote():
                    if self.vote_prob() > 0.8:
                        self.estimate_werewolf = self.vote_declare_func()
                        return cb.estimate(self.estimate_werewolf,'WEREWOLF')
            # 3.estimate villager if not yet
                if self.estimate_villager != self.estimate_villager_func():
                    if self.villager_prob() > 0.2:
                        self.estimate_villager = self.estimate_villager_func()
                        return cb.estimate(self.estimate_villager,'VILLAGER')

            # 4. skip
            if self.talk_turn <= 10:
                return cb.skip()

            return cb.over()

    def whisper(self):
        return cb.skip()

    def vote_declare_func(self):
        if self.game_setting['playerNum'] == 15:
            p0_mat = self.predicter_15.ret_pred_wn()
                # highest prob ww in alive agents provided watashi ningen
            p = -1
            idx = 1
            for i in range(1, 16):
                p0 = p0_mat[i-1, 1]
                if self.base_info['agentIdx'] != idx and self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                    p = p0
                    idx = i
            return idx
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

    def villager_prob(self):
        if self.game_setting['playerNum'] == 15:
            list_seer= list(self.predicter_15.list_seer())
            list_medium= list(self.predicter_15.list_medium())
            p0_mat = self.predicter_15.ret_pred_wn()
            # highest prob ww in alive agents provided watashi ningen
            p = -1
            idx = 1
            for i in range(1, 16):
                p0 = p0_mat[i-1, 0]
                p0 *= self.threat_factor[int(self.base_info['day'])-1][i-1]
                if list_seer[i-1] != 1 and list_medium[i-1] != 1 and self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                    p = p0
                    idx = i
            return p
        else:
            p0_mat = self.predicter_5.ret_pred_wx(0)
            p = -1
            idx = 1
            for i in range(1, 6):
                p0 = p0_mat[i-1, 0]
                p0 *= self.threat_factor[int(self.base_info['day'])-1][i-1]
                if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                    p = p0
                    idx = i
            return p

    def estimate_villager_func(self):
        if self.game_setting['playerNum'] == 15:
            list_seer= list(self.predicter_15.list_seer())
            list_medium= list(self.predicter_15.list_medium())
            p0_mat = self.predicter_15.ret_pred_wn()
            # highest prob ww in alive agents provided watashi ningen
            p = -1
            idx = 1
            for i in range(1, 16):
                p0 = p0_mat[i-1, 0]
                p0 *= self.threat_factor[int(self.base_info['day'])-1][i-1]
                if list_seer[i-1] != 1 and list_medium[i-1] != 1 and self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                    p = p0
                    idx = i
            return idx
        else:
            p0_mat = self.predicter_5.ret_pred_wx(0)
            p = -1
            idx = 1
            for i in range(1, 6):
                p0 = p0_mat[i-1, 0]
                p0 *= self.threat_factor[int(self.base_info['day'])-1][i-1]
                if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                    p = p0
                    idx = i
        return idx

    def vote_prob(self):
        if self.game_setting['playerNum'] == 15:
            p0_mat = self.predicter_15.ret_pred_wn()
            # highest prob ww in alive agents provided watashi ningen
            p = -1
            idx = 1
            for i in range(1, 16):
                p0 = p0_mat[i-1, 1]
                p0 *= self.threat_factor[int(self.base_info['day'])-1][i-1]
                if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                    p = p0
                    idx = i
            return p
        else:
            p0_mat = self.predicter_5.ret_pred_wx(0)
            p = -1
            idx = 1
            for i in range(1, 6):
                p0 = p0_mat[i-1, 1]
                p0 *= self.threat_factor[int(self.base_info['day'])-1][i-1]
                if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                    p = p0
                    idx = i
            return p

    def vote(self):
        if self.game_setting['playerNum'] == 15:

            p0_mat = self.predicter_15.ret_pred_wn()

            if self.base_info['myRole'] == "WEREWOLF":
                p = -1
                idx = 1
                for i in range(1, 16):
                    p0 = p0_mat[i-1, 1]
                    p0 *= self.threat_factor[int(self.base_info['day'])-1][i-1]
                    if str(i) in self.base_info['roleMap'].keys():
                        p0 *= self.day_depend_fake[self.base_info["day"]]
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
            elif self.base_info['myRole'] == "POSSESSED":
                p = -1
                idx = 1
                for i in range(1, 16):
                    p0 = p0_mat[i-1, 1]
                    p0 *= self.threat_factor[int(self.base_info['day'])-1][i-1]
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
            else:
                # highest prob ww in alive agents provided watashi ningen
                p = -1
                idx = 1
                for i in range(1, 16):
                    p0 = p0_mat[i-1, 1]
                    p0 *= self.threat_factor[int(self.base_info['day'])-1][i-1]
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
                    p0 = p0_mat[i-1, 1]
                    p0 *= self.threat_factor[int(self.base_info['day'])-1][i-1]
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
            elif self.base_info['myRole'] == "POSSESSED":
                p0_mat = self.predicter_5.ret_pred_wx(2)
                p = -1
                idx = 1
                for i in range(1, 6):
                    p0 = p0_mat[i-1, 3]
                    p0 *= self.threat_factor[int(self.base_info['day'])-1][i-1]
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
            elif self.base_info['myRole'] == "SEER":
                p0_mat = self.predicter_5.ret_pred_wx(3)
                p = -1

                idx = 1
                for i in range(1, 6):
                    p0 = p0_mat[i-1, 1]
                    p0 *= self.threat_factor[int(self.base_info['day'])-1][i-1]
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
            else:
                p0_mat = self.predicter_5.ret_pred_wx(0)
                p = -1
                idx = 1
                for i in range(1, 6):
                    p0 = p0_mat[i-1, 1]
                    p0 *= self.threat_factor[int(self.base_info['day'])-1][i-1]
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
            return idx

    def attack(self):
        if self.game_setting['playerNum'] == 15:
            # highest prob hm in alive agents
            attack_candidates =[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14]
            list_seer= list(self.predicter_15.list_seer())
            attack_seer =[]
            beguri = False
            seer_is_alive = False
            p = -1
            idx = 1

            if self.base_info['day'] < 3 and len(self.base_info['statusMap']) % 2 != 0:
                for i in range(0, 15):
                    if list_seer[i] == 1 and str(i+1) not in self.base_info['roleMap'].keys() and i+1 != self.seek_attacked():
                        if self.base_info['statusMap'][str(i+1)] == 'DEAD':
                            beguri = True
                        elif self.base_info['statusMap'][str(i+1)] == 'ALIVE':
                            idx = i+1
                if attack_seer is not None and beguri == False:
                    return idx



            p0_mat = self.predicter_15.ret_pred()
            p0_sort = p0_mat[:,1].argsort()
            p0_sort_alive = []

            for i in range(0,15):


                if self.base_info['statusMap'][str(p0_sort[i]+1)] == 'ALIVE' and list_seer[i] == 0 and i+1 != self.seek_attacked():
                    p0_sort_alive.append(p0_sort[i])

            if len(self.base_info['statusMap']) % 2 == 0:
                attack_index = len(p0_sort_alive)-1


            elif self.base_info['day'] <3:
                attack_index = 1


            else:
                attack_index = 0

            idx = int(p0_sort_alive[attack_index])+1
            return idx
        else:

            # lowest prob ps in alive agents
            p = 1
            idx = 1
            p0_mat = self.predicter_5.ret_pred_wx(1)
            for i in range(1, 6):
                p0 = p0_mat[i-1, 2]
                p0 *= self.threat_factor[int(self.base_info['day'])-1][i-1]
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
            num_seer = self.predicter_15.num_seer()
            num_medium = self.predicter_15.num_medium()
            seer_killed = self.predicter_15.seer_killed()
            medium_killed = self.predicter_15.medium_killed()
            list_seer= list(self.predicter_15.list_seer())
            list_medium= list(self.predicter_15.list_medium())
            day = int(self.base_info['day'])
            # highest prob hm in alive agents

            p0_mat = self.predicter_15.ret_pred_wn()              
            p = -1
            idx = 1
            for i in range(1, 16):
                p0 = p0_mat[i-1, 0]
                if list_seer[i-1] == 1 and day < 4:
                    if self.attack_result[day-1][2] > 9 :
                        x = (float(self.attack_result[day-1][0])/float(self.attack_result[day-1][2]))
                    else:
                        x = 0.3
                    p0 *= self.guard_factor[day-1][0]*x
                elif list_medium[i-1] == 1 and day < 4:
                    if self.attack_result[day-1][2]  > 9 :
                        x = (float(self.attack_result[day-1][1])/float(self.attack_result[day-1][2]))
                    else:
                        x = 0.2
                    p0 *= self.guard_factor[day-1][0]*x
                if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                    p = p0
                    idx = i
            return idx
        else:
            # no need
            return 1

    def finish(self):
        if self.game_setting['playerNum'] == 15:        
            list_seer = list(self.predicter_15.list_seer())
            list_medium = list(self.predicter_15.list_medium())
            for i in range (0,3):
                if self.attacked_agent[i] == -1:
                    pass
                elif list_seer[self.attacked_agent[i]-1]:   
                    self.attack_result[i][0] += 1      
                elif list_medium[self.attacked_agent[i]-1]:
                    self.attack_result[i][1] += 1    
                else:
                    self.attack_result[i][2] += 1 



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

    def possessed_seer_result(self):

        suicide_run_prob = 0.5
        idx = 1
        if rand() < suicide_run_prob:          
            p = -1
            p0_mat = self.predicter_15.ret_pred()
            for i in range(1, 16):
                p0 = p0_mat[i-1, 0]
                if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                    p = p0
                    idx = i
            seer_result ="WEREWOLF"
        else:
            p = -1
            p0_mat = self.predicter_15.ret_pred()
            for i in range(1, 16):
                p0 = p0_mat[i-1, 1]
                if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                    p = p0
                    idx = i
            seer_result ="HUMAN"


        self.myresult = 'DIVINED Agent[' + "{0:02d}".format(idx) + '] ' + seer_result
        return self.myresult  


    def werewolf_seer_result(self):

        suicide_run_prob = 0.5
        idx = 1
        p = -1
        p0_mat = self.predicter_15.ret_pred()
        for i in range(1, 16):
            p0 = p0_mat[i-1, 1]
            if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                p = p0
                idx = i
        seer_result ="HUMAN"
        self.myresult = 'DIVINED Agent[' + "{0:02d}".format(idx) + '] ' + seer_result
        return self.myresult  

    def fake_medium_result(self):
        p0_mat = self.predicter_15.ret_pred()
        if p0_mat[self.executed_agent-1, 1] > 0.1 and p0_mat[self.executed_agent-1, 1] > 0.1:
            medium_result ="HUMAN"
        else:
            medium_result ="WEREWOLF"
        self.myresult = 'IDENTIFIED Agent[' + "{0:02d}".format(self.executed_agent) + '] ' + medium_result
        return self.myresult   

    def seek_attacked(self):
        attacked_agent = self.base_info['lastDeadAgentList']
        if  len(attacked_agent) == 1 :
            return int(attacked_agent[0])   
        return -1

agent = PythonPlayer(myname)

# run
if __name__ == '__main__':
    aiwolfpy.connect_parse(agent)
