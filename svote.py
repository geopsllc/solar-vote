#!/usr/bin/env python3

# Imports
from config import *
import os
import json
import requests
from shutil import copy2

# Functions
def api_get(url):
    resp = requests.get(url, timeout=10)
    if (resp.status_code == 200):
        return resp.json()
    else:
        print('Could not retrieve: ' + url)
        quit()

def rank_get(name, votes):
    delegate_votes_temp = delegate_votes_dict.copy()
    delegate_votes_temp[name] = votes
    if name != voted_name and voted_name != '':
        delegate_votes_temp[voted_name] = str(int(delegate_votes_temp[voted_name]) - int(address_balance))
    sorted_votes = sorted(delegate_votes_temp.values(), key = int, reverse=True)
    return sorted_votes.index(votes)+1

def cur_reward_get():
    delegate_votes = voted_delegate['data']['votes']
    delegate_rank = rank_get(voted_name, delegate_votes)
    if delegate_rank in range(1, int(active_delegates) + 1):
        reward = int(address_balance) / int(delegate_votes) * 10800 / int(active_delegates) * dynamic_rewards[str(delegate_rank)] * delegate_share_dict[voted_name] / 100 * (100 - devfund) / 100
    else:
        reward = 0
    return [voted_name, delegate_rank, reward]

def best_reward_get():
    temp_reward = cur_reward[2]
    temp_name = cur_reward[0]
    temp_rank = cur_reward[1]
    for delegate in delegate_share_dict:
        if delegate != cur_reward[0] and delegate != 'N/A':
            total_votes = str(int(address_balance) + int(delegate_votes_dict[delegate]))
            new_rank = rank_get(delegate, total_votes)
            if new_rank in range(1, int(active_delegates) + 1):
                new_reward = int(address_balance) / int(total_votes) * 10800 / int(active_delegates) * dynamic_rewards[str(new_rank)] * delegate_share_dict[delegate] / 100 * (100 - devfund) / 100
            else:
                new_reward = 0
            if new_reward > temp_reward:
                temp_reward = new_reward
                temp_name = delegate
                temp_rank = new_rank
    return [temp_name, temp_rank, temp_reward]

info = open('info.txt','w+')
csv = open('state.csv','w+')
csv.write('Wallet,Balance,Current,Daily,Best,Daily,Gain\n')
total = [0, 0, 0, 0]

delegate_share_dict = {}
delegate_votes_dict = {}
atomic = 100000000
devfund = 0

share_data = api_get(sapi)
network_data = api_get(api + '/node/configuration')
active_delegates = network_data['data']['constants']['activeDelegates']
delegate_data = api_get(api + '/delegates?limit=' + str(active_delegates+2))
if share_data['total'] > share_data['perPage']:
    share_count = share_data['perPage']
else:
    share_count = share_data['total']
delegate_count = delegate_data['meta']['count']
dynamic_rewards = network_data['data']['constants']['dynamicReward']['ranks']

if network_data['data']['constants'].get('devFund'):
    for address in network_data['data']['constants']['devFund']:
        devfund = devfund + network_data['data']['constants']['devFund'][address]

for i in range(0, share_count):
    del_name = share_data['data'][i]['username']
    del_rank = share_data['data'][i]['rank']
    del_share = share_data['data'][i]['payout']
    del_interval = share_data['data'][i]['payout_interval']
    if del_rank in range(1, int(active_delegates) + 3) and del_share in range(min_share, max_share +1) and del_interval in range(min_time, max_time +1) and del_name not in disallowed:
        delegate_share_dict[del_name] = del_share

delegate_share_dict['N/A'] = 0

for i in range(0, delegate_count):
    del_name = delegate_data['data'][i]['username']
    delegate_votes_dict[del_name] = delegate_data['data'][i]['votes']

for name, address in addresses.items():
    address_data = api_get(api + '/wallets/' + address)
    address_balance = address_data['data']['balance']
    if address_data['data']['attributes'].get('vote'):
        voted_delegate = api_get(api + '/delegates/' + address_data['data']['attributes']['vote'])
        voted_name = voted_delegate['data']['username']
    else:
        voted_name = ''

    if voted_name not in delegate_share_dict:
        cur_reward = ['N/A', 0, 0]
    else:
        cur_reward = cur_reward_get()

    best_reward = best_reward_get()

    voting = cur_reward[0] + '[' + str(cur_reward[1]) + ']' + '[' + str(delegate_share_dict[cur_reward[0]]) + '%]'
    best = best_reward[0] + '[' + str(best_reward[1]) + ']' + '[' + str(delegate_share_dict[best_reward[0]]) + '%]'
    delta = round((best_reward[2] - cur_reward[2]) / atomic, 3)

    if delta == 0.0:
        delta = 0

    if delta > gain:
        if 'final' not in globals():
            final = [name, cur_reward[0], best_reward[0], delta]
        elif delta > final[3]:
            final = [name, cur_reward[0], best_reward[0], delta]

    total[0] = total[0] + int(address_balance)
    total[1] = total[1] + cur_reward[2]
    total[2] = total[2] + best_reward[2]
    total[3] = total[3] + delta

    print('Wallet:', name, '-> Balance:', f'{int(address_balance)/atomic:,.2f}', '-> Voting:', voting, '-> Daily:', round(cur_reward[2]/atomic, 2), '-> Best:', best, '-> Daily:', round(best_reward[2]/atomic, 2), '-> Gain:', str(delta))
    csv.write(name + ',' + str(round(int(address_balance)/atomic, 2)) + ',' + voting + ',' + str(round(cur_reward[2]/atomic, 2)) + ',' + best + ',' + str(round(best_reward[2]/atomic, 2)) + ',' + str(delta) + '\n')

print('Wallet: Total', '-> Balance:', f'{total[0]/atomic:,.2f}', '-> Voting: All', '-> Daily:', round(total[1]/atomic, 2), '-> Best: All', '-> Daily:', round(total[2]/atomic, 2), '-> Gain:', round(total[3], 3))
csv.write('Total,' + str(round(total[0]/atomic, 2)) + ',All,' + str(round(total[1]/atomic, 2)) + ',All,' + str(round(total[2]/atomic, 2)) + ',' + str(round(total[3], 3)) + '\n')

if 'final' in globals():
    print('Recommendation: Switch', final[0], 'vote from', final[1], 'to', final[2], 'and gain', final[3])
    info.write('Recommendation: Switch ' + final[0] + ' vote from ' + final[1] + ' to ' + final[2] + ' and gain ' + str(final[3]))

csv.close()
info.close()

copy2('state.csv','web/')
copy2('info.txt','web/')
