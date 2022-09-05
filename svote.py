#!/usr/bin/env python3

# Imports
from config import *
import os
import json
import requests
from shutil import copy2

# Functions
def api_get(url):
    try:
        resp = requests.get(url, timeout=10)
        return resp.json()

    except:
        print('Could not retrieve: ' + url)
        quit()

def cur_rank_get(delegate):
    votes = delegate_votes_dict[delegate]
    sorted_votes = sorted(delegate_votes_dict.values(), key = int, reverse=True)
    return sorted_votes.index(votes)+1

def update_ranks():
    for delegate in delegate_votes_dict:
        del_rank = cur_rank_get(delegate)
        delegate_ranks_dict[delegate] = del_rank

def update_rewards():
    for delegate in delegate_share_dict:
        if delegate_percent_dict[delegate] > 0:
            delegate_rewards_dict[delegate] = round(percent_votes * delegate_percent_dict[delegate] / delegate_votes_dict[delegate] * 10800 / active_delegates * dynamic_rewards[str(delegate_ranks_dict[delegate])] * delegate_share_dict[delegate] / 100 * (100 - donations) / 100)

# Main
info = open('info.txt','w+')
csv = open('state.csv','w+')
csv.write('Delegate,Share,Votes,Daily\n')
delegate_share_dict = {}
delegate_votes_dict = {}
delegate_ranks_dict = {}
delegate_rewards_dict = {}
delegate_percent_dict = {}
atomic = 100000000
cur_reward = 0
donations = 0

share_data = api_get(sapi)
address_data = api_get(api + '/wallets/' + address)
address_balance = int(address_data['data']['balance'])
address_votes_dict = address_data['data']['votingFor']
percent_votes = round(address_balance / 100)
percent_assigned = 0
votes_len = len(address_votes_dict)
network_data = api_get(api + '/node/configuration')
active_delegates = network_data['data']['constants']['activeDelegates']
delegate_data = api_get(api + '/delegates?limit=' + str(active_delegates+2))
share_count = share_data['total']
delegate_count = delegate_data['meta']['count']
dynamic_rewards = network_data['data']['constants']['dynamicReward']['ranks']
dynamic_rewards[str(int(active_delegates+1))] = 0
dynamic_rewards[str(int(active_delegates+2))] = 0

if address_balance <= atomic:
    print('Address balance too low')
    quit()

if network_data['data']['constants'].get('donations'):
    for wallet in network_data['data']['constants']['donations']:
        donations += network_data['data']['constants']['donations'][wallet]['percent']

for i in range(0, share_count):
    del_name = share_data['data'][i]['username']
    del_rank = share_data['data'][i]['rank']
    del_share = share_data['data'][i]['payout']
    del_interval = share_data['data'][i]['payout_interval']
    if del_rank in range(1, int(active_delegates) + 3) and del_share in range(min_share, max_share + 1) and del_interval in range(min_time, max_time + 1) and del_name not in disallowed:
        delegate_share_dict[del_name] = del_share
        delegate_rewards_dict[del_name] = 0
        delegate_percent_dict[del_name] = 0

for i in range(0, delegate_count):
    del_name = delegate_data['data'][i]['username']
    delegate_votes_dict[del_name] = int(delegate_data['data'][i]['votesReceived']['votes'])

update_ranks()
old_ranks_dict = delegate_ranks_dict.copy()
old_votes_dict = delegate_votes_dict.copy()

if votes_len > 0:
    for delegate, data in address_votes_dict.items():
        percent = data['percent']
        balance = round(address_balance * percent / 100)
        cur_rank = old_ranks_dict[delegate]
        delegate_votes_dict[delegate] -= balance
        if delegate in delegate_share_dict and cur_rank <= active_delegates:
            cur_reward += round(balance / old_votes_dict[delegate] * 10800 / active_delegates * dynamic_rewards[str(cur_rank)] * delegate_share_dict[delegate] / 100 * (100 - donations) / 100 / atomic, 3)

update_ranks()

for delegate in delegate_ranks_dict:
    del_rank = delegate_ranks_dict[delegate]
    if del_rank == active_delegates:
        last_in = delegate
    elif del_rank == active_delegates + 1:
        first_out = delegate

first_vote_in = bool(delegate_votes_dict[last_in] < delegate_votes_dict[first_out] + address_balance)

if first_vote_in and first_out in delegate_share_dict:
    vote_in = True
    to_vote = first_out
    if last_in in address_votes_dict and last_in in delegate_share_dict:
        if delegate_share_dict[last_in] > delegate_share_dict[first_out]:
            vote_in = False
else:
    vote_in = False

if vote_in:
    to_assign = 0
    while delegate_votes_dict[last_in] >= delegate_votes_dict[to_vote] + to_assign and percent_assigned < 100:
        to_assign += percent_votes
        percent_assigned += 1
    delegate_votes_dict[to_vote] += to_assign
    update_ranks()
    delegate_percent_dict[to_vote] = percent_assigned
    update_rewards()

while percent_assigned < 100:
    temp_reward = 0
    for delegate in delegate_share_dict:
        delegate_votes_temp = delegate_votes_dict.copy()
        delegate_ranks_temp = delegate_ranks_dict.copy()
        delegate_percent_temp = delegate_percent_dict.copy()
        delegate_rewards_temp = delegate_rewards_dict.copy()
        if delegate_ranks_dict[delegate] <= active_delegates:
            delegate_votes_temp[delegate] += percent_votes
            for x in delegate_votes_temp:
                votes = delegate_votes_temp[x]
                sorted_votes = sorted(delegate_votes_temp.values(), key = int, reverse=True)
                del_rank = sorted_votes.index(votes)+1
                delegate_ranks_temp[x] = del_rank
            delegate_percent_temp[delegate] += 1
            for x in delegate_share_dict:
                if delegate_percent_temp[x] > 0:
                    delegate_rewards_temp[x] = round(percent_votes * delegate_percent_temp[x] / delegate_votes_temp[x] * 10800 / active_delegates * dynamic_rewards[str(delegate_ranks_temp[x])] * delegate_share_dict[x] / 100 * (100 - donations) / 100)
            old_total = sum(delegate_rewards_dict.values())
            new_total = sum(delegate_rewards_temp.values())
            new_reward = new_total - old_total
            if new_reward > temp_reward:
                temp_reward = new_reward
                temp_delegate = delegate
    delegate_votes_dict[temp_delegate] += percent_votes
    update_ranks()
    delegate_percent_dict[temp_delegate] += 1
    update_rewards()
    percent_assigned += 1

delegate_percent_final = {x:y for x,y in delegate_percent_dict.items() if y>0}
delegate_rewards_final = {x:y for x,y in delegate_rewards_dict.items() if y>0}
new_reward = round(sum(delegate_rewards_final.values()) / atomic, 3)

print(f"{'Delegate':^30}", f"{'Share':^5}", f"{'Votes':^11}", f"{'Daily':^9}")
for name, percent in delegate_percent_final.items():
    delegate_info = name + '[' + str(delegate_ranks_dict[name]) + ']' + '[' + str(delegate_share_dict[name]) + '%]'
    print(f"{delegate_info:>30}", f"{str(percent) + '%':>5}", f"{round(percent * percent_votes / atomic, 3):>11.3f}", f"{round(delegate_rewards_final[name] / atomic, 3):>9.3f}")
    csv.write(delegate_info + ',' + str(percent) + '%,' + str(f"{round(percent * percent_votes / atomic, 3):.3f}") + ',' + str(f"{round(delegate_rewards_final[name] / atomic, 3):.3f}") + '\n')
print(f"{'Total':^30}", f"{'100%':>5}", f"{round(address_balance / atomic, 3):>11.3f}", f"{new_reward:>9.3f}")
csv.write('Total,100%,' + str(f"{round(address_balance / atomic, 3):.3f}") + ',' + str(f"{new_reward:.3f}") + '\n')

if new_reward > cur_reward + gain:
    print('Currently earning', f"{cur_reward:.3f}", 'SXP/d. Vote to gain', f"{new_reward - cur_reward:.3f}", 'SXP/d.')
    info.write('Currently earning ' + str(f"{cur_reward:.3f}") + ' SXP/d. Vote to gain ' + str(f"{new_reward - cur_reward:.3f}") + ' SXP/d.')
else:
    print('Currently earning', f"{cur_reward:.3f}", 'SXP/d.')
    info.write('Currently earning ' + str(f"{cur_reward:.3f}") + ' SXP/d.')

csv.close()
info.close()

copy2('state.csv','web/')
copy2('info.txt','web/')
