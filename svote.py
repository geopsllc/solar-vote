#!/usr/bin/env python3

# Imports
from config import *
import os
import json
import requests
import asyncio
import aiohttp
from shutil import copy2

# Classes
class Address():

    def __init__(self):
        pass

    def set_balance(self, balance):
        self.balance = balance

    def set_voted_name(self, name):
        self.voted_name = name

    def set_voted_rank(self, rank):
        self.voted_rank = rank

    def set_total(self, total):
        self.total = total

    def set_vote_name(self, name):
        self.vote_name = name

    def set_rewards_map(self, map):
        self.rewards_map = map.copy()

    def set_ranks_map(self, map):
        self.ranks_map = map.copy()

# Functions
def api_get(url):
    try:
        resp = requests.get(url, timeout=10)
        return resp.json()

    except:
        print('Could not retrieve: ' + url)
        quit()

def cur_rank_get(name):
    delegate_votes_temp = delegate_votes_dict.copy()
    votes = delegate_votes_temp[name]
    sorted_votes = sorted(delegate_votes_temp.values(), key = int, reverse=True)
    return sorted_votes.index(votes)+1

async def async_get(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20) as resp:
                return await resp.json()

    except:
        print('Could not retrieve: ' + url)
        quit()

async def get_address_data(name, address):
    address_data = await async_get(api + '/wallets/' + address)
    address_balance = address_data['data']['balance']
    address_votes = address_data['data']['votingFor']
    votes_len = len(address_votes)

    if votes_len == 1:
        voted_name = list(address_votes.keys())[0]
        voted_balance = delegate_votes_dict[voted_name]
        voted_rank = cur_rank_get(voted_name)
        if voted_rank in range(1, int(active_delegates) + 1) and voted_name in delegate_share_dict:
            reward = round(int(address_balance) / int(voted_balance) * 10800 / int(active_delegates) * dynamic_rewards[str(voted_rank)] * delegate_share_dict[voted_name] / 100 * (100 - devfund) / 100 / atomic, 3)
        else:
            reward = 0
    elif votes_len == 0:
        voted_name = 'N/A'
        voted_rank = '0'
        reward = 0
    else:
        print('Address', name, 'voting for more than 1 delegate!')
        quit()

    class_dict[name] = Address()
    class_dict[name].set_balance(int(address_balance))
    class_dict[name].set_voted_name(voted_name)
    class_dict[name].set_voted_rank(int(voted_rank))
    class_dict[name].set_vote_name(voted_name)
    class_dict[name].set_total(0)

    current_rewards_dict[name] = reward
    current_ranks_dict[name] = int(voted_rank)

def address_reward(name):
    for delegate in delegate_share_dict:
        delegate_votes_temp = delegate_votes_dict.copy()
        current_rewards_temp = current_rewards_dict.copy()
        current_ranks_temp = current_ranks_dict.copy()

        if delegate != class_dict[name].voted_name and delegate != 'N/A':
            delegate_votes_temp[delegate] += class_dict[name].balance

            if class_dict[name].voted_name != 'N/A':
                delegate_votes_temp[class_dict[name].voted_name] -= class_dict[name].balance

            sorted_votes = sorted(delegate_votes_temp.values(), key = int, reverse=True)
            new_rank = sorted_votes.index(delegate_votes_temp[delegate])+1

            if class_dict[name].voted_name != 'N/A':
                old_rank = sorted_votes.index(delegate_votes_temp[class_dict[name].voted_name])+1
            else:
                old_rank = 0

            if current_ranks_dict[name] <= int(active_delegates):
                old_rank_change = old_rank - current_ranks_dict[name]
            else:
                old_rank_change = 0

            if new_rank in range(1, int(active_delegates) + 1) and (old_rank <= int(active_delegates) or old_rank_change == 0):
                current_rewards_temp[name] = round(class_dict[name].balance / delegate_votes_temp[delegate] * 10800 / int(active_delegates) * dynamic_rewards[str(new_rank)] * delegate_share_dict[delegate] / 100 * (100 - devfund) / 100 / atomic, 3)
                current_ranks_temp[name] = new_rank

                for temp_name in addresses:

                    if temp_name != name and class_dict[temp_name].voted_name == delegate:
                        current_rewards_temp[temp_name] = round(class_dict[temp_name].balance / delegate_votes_temp[delegate] * 10800 / int(active_delegates) * dynamic_rewards[str(new_rank)] * delegate_share_dict[delegate] / 100 * (100 - devfund) / 100 / atomic, 3)
                        current_ranks_temp[temp_name] = new_rank
                    elif temp_name != name and class_dict[temp_name].voted_name == class_dict[name].voted_name and class_dict[name].voted_name != 'N/A' and class_dict[name].voted_name in delegate_share_dict:
                        current_rewards_temp[temp_name] = round(class_dict[temp_name].balance / delegate_votes_temp[class_dict[name].voted_name] * 10800 / int(active_delegates) * dynamic_rewards[str(old_rank)] * delegate_share_dict[class_dict[name].voted_name] / 100 * (100 - devfund) / 100 / atomic, 3)
                        current_ranks_temp[temp_name] = old_rank
                    elif temp_name != name and class_dict[temp_name].voted_name not in {class_dict[name].voted_name, 'N/A'} and class_dict[temp_name].voted_name in delegate_share_dict:
                        temp_rank = sorted_votes.index(delegate_votes_temp[class_dict[temp_name].voted_name])+1
                        if temp_rank != current_ranks_temp[temp_name]:
                            if temp_rank <= int(active_delegates):
                                current_rewards_temp[temp_name] = round(class_dict[temp_name].balance / delegate_votes_temp[class_dict[temp_name].voted_name] * 10800 / int(active_delegates) * dynamic_rewards[str(temp_rank)] * delegate_share_dict[class_dict[temp_name].voted_name] / 100 * (100 - devfund) / 100 / atomic, 3)
                            else:
                                current_rewards_temp[temp_name] = 0
                            current_ranks_temp[temp_name] = temp_rank

                temp_total = round(sum(current_rewards_temp.values()), 3)

                if class_dict[name].total < current_total:
                    class_dict[name].set_total(current_total)
                    class_dict[name].set_rewards_map(current_rewards_dict)
                    class_dict[name].set_ranks_map(current_ranks_dict)
                elif class_dict[name].total < temp_total:
                    class_dict[name].set_total(temp_total)
                    class_dict[name].set_rewards_map(current_rewards_temp)
                    class_dict[name].set_ranks_map(current_ranks_temp)
                    class_dict[name].set_vote_name(delegate)

# Main
info = open('info.txt','w+')
csv = open('state.csv','w+')
csv.write('Wallet,Balance,Current,Daily,Best,Daily,Δ\n')
delegate_share_dict = {}
delegate_votes_dict = {}
current_rewards_dict = {}
current_ranks_dict = {}
class_dict = {}
tasks = []
atomic = 100000000
devfund = 0

share_data = api_get(sapi)
network_data = api_get(api + '/node/configuration')
active_delegates = network_data['data']['constants']['activeDelegates']
delegate_data = api_get(api + '/delegates?limit=' + str(active_delegates+2))
share_count = share_data['total']
delegate_count = delegate_data['meta']['count']
dynamic_rewards = network_data['data']['constants']['dynamicReward']['ranks']
dynamic_rewards[str(int(active_delegates+1))] = 0
dynamic_rewards[str(int(active_delegates+2))] = 0

if network_data['data']['constants'].get('devFund'):
    for address in network_data['data']['constants']['devFund']:
        devfund += network_data['data']['constants']['devFund'][address]

for i in range(0, share_count):
    del_name = share_data['data'][i]['username']
    del_rank = share_data['data'][i]['rank']
    del_share = share_data['data'][i]['payout']
    del_interval = share_data['data'][i]['payout_interval']
    if del_rank in range(1, int(active_delegates) + 3) and del_share in range(min_share, max_share + 1) and del_interval in range(min_time, max_time + 1) and del_name not in disallowed:
        delegate_share_dict[del_name] = del_share

delegate_share_dict['N/A'] = 0

for i in range(0, delegate_count):
    del_name = delegate_data['data'][i]['username']
    delegate_votes_dict[del_name] = int(delegate_data['data'][i]['votesReceived']['votes'])

# Create list of async tasks
for name, address in addresses.items():
    tasks.append(asyncio.ensure_future(get_address_data(name, address)))

# Initialize async loop
loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(asyncio.wait(tasks))

finally:
    loop.close()

current_total = round(sum(current_rewards_dict.values()), 3)
best_total = current_total
balance_total = 0
best_name = ''

for name in addresses:
    address_reward(name)
    if class_dict[name].total > best_total:
        best_total = class_dict[name].total
        best_name = name

for name in addresses:
    balance_total += class_dict[name].balance

    if name == best_name:
        new_vote = class_dict[name].vote_name
    else:
        new_vote = class_dict[name].voted_name

    if class_dict[name].voted_name in disallowed:
        voting = class_dict[name].voted_name + '[' + str(class_dict[name].voted_rank) + ']' + '[0%]'
    else:
        voting = class_dict[name].voted_name + '[' + str(class_dict[name].voted_rank) + ']' + '[' + str(delegate_share_dict[class_dict[name].voted_name]) + '%]'

    if best_name == '':
        best_daily = round(current_rewards_dict[name], 2)
        best = new_vote + '[' + str(current_ranks_dict[name]) + ']' + '[' + str(delegate_share_dict[new_vote]) + '%]'
        delta = 0
    elif new_vote in disallowed:
        best_daily = 0
        best = new_vote + '[' + str(current_ranks_dict[name]) + ']' + '[0%]'
        delta = 0
    else:
        best_daily = round(class_dict[best_name].rewards_map[name], 2)
        best = new_vote + '[' + str(class_dict[best_name].ranks_map[name]) + ']' + '[' + str(delegate_share_dict[new_vote]) + '%]'
        delta = round(class_dict[best_name].rewards_map[name] - current_rewards_dict[name], 2)

    if delta == 0.0:
        delta = 0

    if name == best_name:
        name_special = name + '➤'
    else:
        name_special = name

    print('Wallet:', name_special, '-> Balance:', f'{int(class_dict[name].balance)/atomic:,.2f}', '-> Voting:', voting, '-> Daily:', round(current_rewards_dict[name], 2), '-> Best:', best, '-> Daily:', best_daily, '-> Δ:', delta)
    csv.write(name_special + ',' + str(round(int(class_dict[name].balance)/atomic, 2)) + ',' + voting + ',' + str(round(current_rewards_dict[name], 2)) + ',' + best + ',' + str(best_daily) + ',' + str(delta) + '\n')

delta = round(best_total - current_total, 2)

if delta == 0.0:
    delta = 0

print('Wallet: Total', '-> Balance:', f'{balance_total/atomic:,.2f}', '-> Voting: All', '-> Daily:', round(current_total, 2), '-> Best: All', '-> Daily:', round(best_total, 2), '-> Δ:', delta)
csv.write('Total,' + str(round(balance_total/atomic, 2)) + ',All,' + str(round(current_total, 2)) + ',All,' + str(round(best_total, 2)) + ',' + str(delta) + '\n')

if best_name != '' and delta > gain:
    print('Recommendation: Switch', best_name, 'vote from', class_dict[best_name].voted_name, 'to', class_dict[best_name].vote_name)
    info.write('Recommendation: Switch ' + best_name + ' vote from ' + class_dict[best_name].voted_name + ' to ' + class_dict[best_name].vote_name)

csv.close()
info.close()

copy2('state.csv','web/')
copy2('info.txt','web/')
