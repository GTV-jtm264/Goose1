import onetimepass as otp
import requests
import json
import math
'''
    Insert BitSkins API key here, and the my_secret below
'''
API_KEY = ''

'''
    This generates the two factor authentication for BitSkins.
    NOTE: this is not the same as steam's two factor authentication
'''


def get_code():
    my_secret = ''
    return str(otp.get_totp(my_secret))

'''
    The pre-filter essentially goes through all the items in csgo and does some of the percent encoding needed
    for a few of the methods that require a market hash name.
'''


def filter_PRE():
    f = open('SkinList_PRE0.txt', 'w')
    r = get_all_item_prices()
    data = r.json()
    for i in range(0, len(data['prices'])):
        if float(data['prices'][i]['price'].encode('ascii', 'ignore')) <= 20:
            name = data['prices'][i]['market_hash_name'].encode('ascii','ignore')
            if ' StatTrak ' in name:
                name = '%E2%98%85' + name[1:10] + '%E2%84%A2' + name[8:]
            if 'StatTrak ' in name:
                name = name[0:8] + '%E2%84%A2' + name[8:]
            if name[0] == ' ':
                name = name[1:]
            name = generate_hash(name)
            f.write(name + '\n')
    f.close()

'''
    This filters out un-desirable trades that do not have enough variance / volume to make a reasonable profit.
    Feel free to improve this part / make an actual filter to filter out low daily volume items.
'''


def filter_name():
    f = open('SkinList_PRE0.txt', 'r')
    w = open('SkinList.txt', 'w')
    for line in f:
        if 'Souvenir' not in line and 'Sticker' not in line and 'Knife' not in line:
            if 'Karambit' not in line and 'Bayonet' not in line and 'Capsule' not in line:
                if 'Daggers' not in line and 'Music' not in line and 'Case' not in line:
                    if 'Gift' not in line and 'M249' not in line and 'Negev' not in line:
                        if 'Sawed' not in line and 'Name%20Tag' not in line and 'Foil' not in line:
                            if 'Participation' not in line and 'ESL' not in line and 'Operation' not in line:
                                if 'Swap%20Tool' not in line and 'Key' not in line and 'Presents' not in line:

                                    w.write(line)
    f.close()
    w.close()

'''
    This just runs the previous two functions into a easy to call function
'''


def filtered():
    filter_PRE()
    filter_name()

'''
    API call to get the current accounts balance and return it as a float value
'''


def balance():
    url = 'https://bitskins.com/api/v1/get_account_balance/?api_key='
    url += API_KEY + '&code=' + get_code()
    r = requests.get(url)
    data = r.json()
    return float(data['data']['available_balance'])

'''
    Pass this a market hash name, it will calculate if it is profitable,
    if it is profitable it will tell you what it suggest to sell at.
    I calculated it with 6% fee's on the steam suggested price, not the actual %4.8-5% fee on the actual sell price.
    This means I over estimate the cost of the item twice on purpose, to ensure I actually make a profit
'''


def calculate(name):
    print('-------------------------------------')
    print('Checking new item')
    data = get_price(name)
    # if data on the item exist, p
    if data != -1:
        # if its not mine
        if not data[0]:
            actual = data[2]
            suggested = data[3]
            if suggested <= 10:
                print('actual: ' + str(actual))
                print('sugges: ' + str(suggested))
                diff = suggested - actual
                cost = suggested * .06
                sell = actual + cost + diff*.2
                if (sell - cost - actual) >= .05:
                    #purchase(data[1], actual, sell)
                    #withdraw_batch(data[1])
                    print("################################")
                    print('     Bought: ' + str(name))
                    print('     Sell at: ' + str(sell))
                    print("################################")

'''
    API call to sell the item associated with ID, at the price of sell
'''


def gen_sell(ID, sell):
    url = 'https://bitskins.com/api/v1/list_item_for_sale/?api_key='
    url += str(API_KEY) + '&code='
    url += get_code() + '&item_ids='
    url += str(ID) + '&prices='
    url += url + str(sell)
    return requests.get(url)

'''
    This function runs through the items to sell from myInventory. Attempts to sell them all
    After it list all the items for sale it wipes the file clean.
'''


def seller():
    f = open('myInventory.txt', 'r')
    for line in f:
        data = line.split(',')
        gen_sell(data[0], data[1])
    f.close()
    f = open('myInventory.txt', 'w')
    f.close()

'''
    The final part of generating a valid percent encoded market hash name
'''
def generate_hash(name): 
    name = name.replace(" ", "%20")
    name = name.replace("|", "%7C")
    name = name.replace("(", "%28")
    name = name.replace(")", "%29")
    return name

'''
    API call to retrieve all the items on sale @ BitSkins.com
'''


def get_all_item_prices():
    url = 'https://bitskins.com/api/v1/get_all_item_prices/?api_key='
    url += API_KEY + '&code=' + get_code()
    return requests.get(url)

'''
    API call to purchase the item associated with item ID at the price of buy,
    it writes to a file once it is done. This part needs some work to ensure that it checks
    that the item was able to be purchased.
'''


def purchase(ID, buy, sell):
    buy = "{0:.2f}".format(buy)
    sell = "{0:.2f}".format(sell)
    url = 'https://bitskins.com/api/v1/buy_item/?api_key='
    url += API_KEY + '&code=' + get_code() + '&item_ids=' + str(ID) + '&prices=' + str(buy)
    data = requests.get(url)
    f = open('myInventory.txt', 'a')
    f.write(str(ID) + ',' + str(sell) + ',' + str(buy))
    f.close()
    return data

'''
    API call to get the information on: is it mine, itemID, actual price, and the steam suggested price
'''


def get_price(name):
    url = 'https://bitskins.com/api/v1/get_inventory_on_sale/?api_key='
    url += API_KEY + '&code=' + get_code()
    url += '&page=1&sort_by=price&order=asc&market_hash_name='
    url += generate_hash(name)
    url += '&has_stickers=-1'
    r = requests.get(url)
    data = r.json()
    try:
        suggested = float(str(data['data']['items'][0]['suggested_price']))
        actual = float(str(data['data']['items'][0]['price']))
        itemID = str(data['data']['items'][0]['item_id'])
        isMine = data['data']['items'][0]['is_mine']
        return [isMine, itemID, actual, suggested]
    except IndexError:
        return -1

'''
    API call to essentially ask for the items we bought to be sent to our steam account.
'''


def withdraw_batch(ID):
    url = 'https://bitskins.com/api/v1/get_all_item_prices/?api_key='
    url += API_KEY + '&code=' + get_code() + '&item_ids=' + str(ID)
    return requests.get(url)

'''
    RUN function that controls the entire thing, we are going to need to add in quite a few more checks to see
    that the functions above are doing what they are supposed to and cleaning up after themself. This is basically the
    beta of Goose.
'''


def run():
    filtered()
    f = open('SkinList.txt', 'r')
    while balance() >= 0.00:
        count = 0
        for line in f:
            if count % 100:
                pass
                #seller()
            calculate(line)
            count += 1










































