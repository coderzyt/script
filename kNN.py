#! D://Anaconda/python

import urllib3
import json
import codecs

baseUrl = 'http://api.opendota.com/api'

def getAllMatches():
    f = codecs.open("data.json", "r", encoding="utf-8")
    jsonStr = json.load(f)
    print(jsonStr)

def main():
    pass

if __name__ == '__main__':
    getAllMatches()