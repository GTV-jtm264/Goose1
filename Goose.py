import onetimepass as otp
import requests
import datetime
import time

'''
    TODO: Solve all TODO's
    TODO: pass trade_tokens to a file to secure the account inventory
    TODO: Program in randomness in when to sell
    TODO: Program in randomness in calculating the buy amount
    TODO: Program bot distribution to make it harder to detect

    Solve all TODO's

    There are various TODO's located throughout this file. They aren't super duper important
    but getting them done wold be nice

    The randomness is here to ensure it is much harder to detect what we are doing, that we have automated
    the process. The site owner probably will notice otherwise and ban our account from trading with them.
    We need to ensure that doesn't happen.
'''

'''
    Insert BitSkins API key here, and the my_secret below
'''
API = open('API.txt', 'r')
API_KEY = API.readline()
API.close()


'''
    This generates the two factor authentication for BitSkins.
    NOTE: this is not the same as steam's two factor authentication
'''
SECRET = open('secret.txt', 'r')
my_secret = SECRET.readline()

def get_code():
    return str(otp.get_totp(my_secret))

'''
    This just returns the day of the month IE: 4/20/2016 -> 20
'''
def day():
    now = datetime.datetime.now()
    return str(now.day)

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
    The pre-filter essentially goes through all the items in csgo and does some of the percent encoding needed
    for a few of the methods that require a market hash name.
'''
def filter_PRE():
    f = open('SkinList_PRE0.txt', 'w')
    r = get_all_item_prices()
    data = r.json()
    for i in range(0, len(data['prices'])):
        if float(data['prices'][i]['price'].encode('ascii', 'ignore')) <= 20:
            name = data['prices'][i]['market_hash_name'].encode('ascii', 'ignore')
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
    Filters out items by their name.
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
    Helper function to see if an item sells enough or not
'''
def get_volume(name):
    name = name[0:len(name)-1]
    url = 'https://bitskins.com/api/v1/get_price_data_for_items_on_sale/?api_key='
    url += API_KEY + '&code=' + get_code()
    url += '&names='
    url += name
    r = requests.get(url)
    data = r.json()
    try:
        if data['data']['items'][0]['recent_sales_info'] != None:
            if (data['data']['items'][0]['recent_sales_info']['hours'] <= 24):
                return 1
            else:
                return -1
        else:
            return -1
    except:
        return -1

'''
    This function filters out items that don't have enough volume to be worth selling atm
'''
def filter_VOL():
    f = open('SkinList_PRE0.txt', 'r')
    w = open('SkinList.txt', 'w')
    for line in f:
        if get_volume(line) != -1:
            w.write(line)
'''
    This function basically runs the other filters so its easy to call
'''
def filtered():
    log = open('Log_' + day() + '.txt', 'a')
    log.write('\n' + time.ctime() + '    Filtered: ...')
    filter_PRE()
    filter_name()
    filter_VOL()
    log.write('\n' + time.ctime() + '    Filtered: Success')
    log.close()

'''
    API call to get the current accounts balance and return it as a float value
'''
def balance():
    url = 'https://bitskins.com/api/v1/get_account_balance/?api_key='
    url += API_KEY + '&code=' + get_code()
    r = requests.get(url)
    data = r.json()
    log = open('Log_' + day() + '.txt', 'a')
    if data['status'] == 'success':
        log.write('\n' + time.ctime() + '    Balance retrieval: Success')
        log.close()
        return float(data['data']['available_balance'])
    else:
        log.write('\n' + time.ctime() + '    Balance retrieval: Failure')
        log.close()
        return -1
'''
    Pass this a market hash name, it will calculate if it is profitable,
    if it is profitable it will tell you what it suggest to sell at.
    I calculated it with 6% fee's on the steam suggested price, not the actual %4.8-5% fee on the actual sell price.
    This means I over estimate the cost of the item twice on purpose, to ensure I actually make a profit
'''


def calculate(name):
    log = open('Log_' + day() + '.txt', 'a')
    log.write('\n' + time.ctime() + '    Checking item: ' + name[0:-2])
    log.close()
    data = get_price(name)
    # if data on the item exist, p
    if data != -1:
        # if its not mine
        if not data[0]:
            actual = data[2]
            suggested = data[3]
            if suggested <= 10:
                diff = suggested - actual
                cost = suggested * .05
                sell = actual + cost + diff*.18
                if (sell - cost - actual) >= .05:
                    purchase(data[1], actual, sell)
                    withdraw_batch(data[1])

'''
    API call to retrieve all the items on sale @ BitSkins.com
'''


def get_all_item_prices():
    url = 'https://bitskins.com/api/v1/get_all_item_prices/?api_key='
    url += API_KEY + '&code=' + get_code()
    r = requests.get(url)
    data = r.json()
    log = open('Log_' + day() + '.txt', 'a')
    if data['status'] == 'success':
        log.write('\n' + time.ctime() + '    Price list retrieved: Success')
        log.close()
        return r
    else:
        log.write('\n' + time.ctime() + '    Price list retrieved: Failure')
        log.close()


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
    r = requests.get(url)
    data = r.json()
    print(r.text)
    log = open('Log_' + day() + '.txt', 'a')
    if data['status'] == 'success':
        log.write('\n' + time.ctime() + '    Purchased: ' + ID + ' @ ' + buy + ' to sell for ' + sell)
        log.close()
        f = open('myInventory.txt', 'a')
        f.write(str(ID) + ',' + str(sell) + ',' + str(buy))
        f.close()
        return 1
    else:
        log.write('\n' + time.ctime() + '    Unable to purchase: ' + ID + ' @ ' + buy)
        log.close()
        return -1
'''
    API call to get the information on: is it mine, itemID, actual price, and the steam suggested price
'''


def get_price(name):
    url = 'https://bitskins.com/api/v1/get_inventory_on_sale/?api_key='
    url += API_KEY + '&code=' + get_code()
    url += '&page=1&sort_by=price&order=asc&market_hash_name='
    url += name
    url += '&has_stickers=-1'
    r = requests.get(url)
    data = r.json()
    if data['status'] == 'success':
        try:
            suggested = float(str(data['data']['items'][0]['suggested_price']))
            actual = float(str(data['data']['items'][0]['price']))
            itemID = str(data['data']['items'][0]['item_id'])
            isMine = data['data']['items'][0]['is_mine']
            return [isMine, itemID, actual, suggested]
        except IndexError:
            return -1
    else:
        log = open('Log_' + day() + '.txt', 'a')
        log.write('\n' + time.ctime() + '    Unable to retrieve price of ' + name)
        log.close()
        return -1

'''
    API call to essentially ask for the items we bought to be sent to our steam account.
'''


def withdraw_batch(ID):
    url = 'https://bitskins.com/api/v1/withdraw_item/?api_key='
    url += API_KEY + '&code=' + get_code() + '&item_ids=' + str(ID)
    r = requests.get(url)
    data = r.json()
    log = open('Log_' + day() + '.txt', 'a')
    if data['status'] == 'success':
        log.write('\n' + time.ctime() + '    Withdrew: ' + ID)
        log.close()
        return 1
    else:
        log.write('\n' + time.ctime() + '    Unable to withdraw: ' + ID)
        log.close()

'''
    RUN function that controls the entire thing, we are going to need to add in quite a few more checks to see
    that the functions above are doing what they are supposed to and cleaning up after themself. This is basically the
    beta of Goose.
'''
'''
    API call to sell the item associated with ID, at the price of sell
'''

'''
    TODO: pass trade_tokens to a file to secure the account inventory
'''


def gen_sell(ID, sell):
    url = 'https://bitskins.com/api/v1/list_item_for_sale/?api_key='
    url += str(API_KEY) + '&code='
    url += get_code() + '&item_ids='
    url += str(ID) + '&prices='
    url += url + str(sell)
    r = requests.get(url)
    data = r.json()
    log = open('Log_' + day() + '.txt', 'a')
    if data['status'] == 'success':
        log.write('\n' + time.ctime() + '    Listed: ' + ID + ' on the market')
        log.close()
        token = open('TokenList.txt', 'a')
        token.write(data['data']['trade_tokens'][0])
        token.close()
        return data['data']['trade_tokens'][0]
    else:
        log.write('\n' + time.ctime() + '    Unable to list: ' + ID + ' on the market')
        log.close()
        return -1

'''
    This function runs through the items to sell from myInventory. Attempts to sell them all
    After it list all the items for sale it wipes the file clean.
'''


def seller():
    log = open('Log_' + day() + '.txt', 'a')
    log.write('\n' + time.ctime() + '    Selling items!')
    f = open('myInventory.txt', 'r')
    for line in f:
        data = line.split(',')
        gen_sell(data[0], data[1])
    f.close()
    f = open('myInventory.txt', 'w')
    f.close()
    log.write('\n' + time.ctime() + '    Finished selling items!')
    log.close()

'''
    API Call to get inventory
'''
'''
    TODO: We need to play around with this for a bit. This will get all the account's inventory data
    but we need the price we bought it at and the price we should sell it at on load. It wont work for existing items
    in our inventory. For now i believe it will work fine.
'''

def get_inventory():
    url = 'https://bitskins.com/api/v1/get_my_inventory/?api_key='
    url += API_KEY + '&code=' + get_code()
    r = requests.get(url)
    data = r.json()
    f = open('myInventory.txt', 'w')
    for i in range(0, len(data['data']['steam_inventory']['items'])):
        f.write(data['data']['steam_inventory']['items'][i]['item_ids'][0].encode('ascii', 'ignore') + ',' + '\n')


def run():
    log = open('Log_' + day() + '.txt', 'a')
    log.write('\n' + time.ctime() + '    Starting Goose:')
    log.close()
    f = open('SkinList.txt', 'r')
    while balance() >= 0.00:
        count = 0
        for line in f:
            count += 1
            if count % 100 == 0:
                seller()
            calculate(line)
            log = open('Log_' + day() + '.txt', 'a')
            log.write('\n')
            log.close()
filtered()