# -*- coding: utf-8 -*-

import os
import re
import requests
from multiprocessing.dummy import Pool
from lxml import etree
import copy
import argparse
# proxy
PROXIES = {
    'http': 'socks5://127.0.0.1:1086',
    'https': 'socks5://127.0.0.1:1086'
}

SAVE_FOLDER = '/tmp'
RETRY = 10


def total_match(r):
    xml = etree.fromstring(r.encode('utf8'))
    return int(xml.xpath('//posts/@total')[0])


def video_match(r):
    res = set()
    hd_pattern = re.compile(r'.*"hdUrl":("([^\s,]*)"|false),')
    default_pattern = re.compile(r'.*src="(\S*)" ', re.DOTALL)
    xml = etree.fromstring(r.encode('utf8'))
    for _ in xml.xpath('//video-player'):
        _ = _.text.replace('\\', '')
        hd_match = hd_pattern.match(_)
        default_match = default_pattern.match(_)
        if hd_match is not None and hd_match.group(1) != 'false':
            url = hd_match.group(2)
        elif default_match is not None:
            url = default_match.group(1)
        else:
            continue
        res.add(url)
    return list(res)


def photo_match(r):
    res = set()
    xml = etree.fromstring(r.encode('utf8'))
    for _ in xml.xpath('//photoset'):
        _ = _.xpath('//photo/photo-url')
        for i in _:
            res.add(i.text)
    return list(res)


def pool(func, data, num=2):
    p = Pool(num)
    t = p.map_async(func, data)
    t.wait()
    # return t.get()


class CrawlerScheduler(object):
    def __init__(self, user):
        self.user = user
        self.url = 'http://{user}.tumblr.com/api/read'.format(user=self.user)
        self.params = {'num': self.total}
        self.targets = [self.photo_url, self.video_url]
        self.save = os.path.join(SAVE_FOLDER, user)
        if not os.path.exists(self.save):
            os.makedirs(self.save)

    @property
    def photo_url(self):
        self.photo = self.params.copy()
        self.photo.setdefault('type', 'photo')
        return self.photo

    @property
    def video_url(self):
        self.video = self.params.copy()
        self.video.setdefault('type', 'photo')
        return self.video

    @property
    def total(self):
        r = self.__connection(url=self.url)
        return total_match(r)

    def __connection(self, **kwargs):
        r = requests.get(url=kwargs.get('url'),
                         params=kwargs.get('params', None),
                         proxies=PROXIES)
        if r.status_code == 404:
            return
        r.encoding = 'utf8'
        return r.text

    def __parse(self):
        html = self.__connection(url=self.url, params=self.params)
        self.photo = photo_match(r=html)
        self.video = video_match(r=html)

    def crawler(self):
        self.__parse()
        pool(self.download, self.photo + self.video, 100)
        print('Download Finished')

    def download(self, url):
        filename = os.path.join(self.save, url.split('/')[-1])
        if '.' not in filename:
            filename = '{}.mp4'.format(filename)
        retry_times = 0
        while retry_times < RETRY:
            try:
                r = requests.get(url=url, proxies=PROXIES, stream=True)
                if r.status_code == 403:
                    retry_times = RETRY
                    print("Access Denied when retrieve %s.\n" % url)
                    raise Exception("Access Denied")
                with open(filename, 'wb') as fh:
                    for chunk in r.iter_content(chunk_size=1024):
                        fh.write(chunk)
                break
            except:
                # try again
                retry_times += 1


def test():
    Crawler = CrawlerScheduler('saotunnannan')
    Crawler.crawler()


def main():
    parser = argparse.ArgumentParser(description='Short sample app')

    parser.add_argument('--name', dest='name', type=str,
                        help='''sister's name''')
    args = parser.parse_args()
    Crawler = CrawlerScheduler(args.name)
    Crawler.crawler()


if __name__ == "__main__":
    main()
