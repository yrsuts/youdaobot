#! /home/cooper/venv/bin/python
import re
import requests
from bs4 import BeautifulSoup


class Youdao:
    __slots__ = ['word', 'soup', 'block', 'iserror']

    def __init__(self, word):
        self.word = word
        self.soup = self.get_soup()
        self.block = self.get_block()
        self.iserror = not self.block

    def get_soup(self):
        s = requests.session()
        s.keep_alive = False
        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                AppleWebKit/537.36 (KHTML, like Gecko) \
                Chrome/68.0.3440.106 Safari/537.36'
        }
        word = self.word
        if word:
            url = "http://www.youdao.com/w/" + "{}".format(word)
            page = s.get(url=url, headers=headers)
            if page.status_code == 200:
                soup = BeautifulSoup(page.content, 'html.parser')
            else:
                soup = None
            return soup

    def get_block(self):
        soup = self.soup
        block = soup.find(
            id='phrsListTab',
            class_="trans-wrapper clearfix",
        ) if soup else None
        return block

    def get_prons(self):
        prons_to_return = []
        block = self.block
        if block:
            prons = block.find('div', class_="baav")
            if prons:
                prons = prons.find_all('span', class_='pronounce')
            if prons:
                for pron in prons:
                    pron = re.sub(r'\n', '', pron.get_text())
                    pron = re.sub(r'\s{3,}', '', pron)
                    if len(pron) > 1:
                        prons_to_return.append(pron)
        return prons_to_return

    def get_trans(self):
        trans_to_return = []
        block = self.block
        if block:
            trans_container = block.find('div', class_="trans-container")
            if trans_container:
                trans = trans_container.find('ul')
                if trans:
                    trans = trans.find_all('li')
                    if trans:
                        for tran in trans:
                            tran = tran.get_text()
                            trans_to_return.append(tran)
                additional = trans_container.find('p', class_="additional")
                if additional:
                    string = additional.get_text()
                    string = re.sub(r"\s", '', string)
                    trans_to_return.append(string)
        return trans_to_return

    def get_phrases(self):
        phrases_to_return = []
        soup = self.soup
        if soup:
            wordGroup = soup.find(
                    id="wordGroup",
                    class_="trans-container tab-content hide more-collapse"
            )
            if wordGroup:
                phrases = wordGroup.find_all('p', class_="wordGroup")
                if phrases:
                    for i, phrase in enumerate(phrases):
                        contenttitle = phrase.find(
                            'span', class_='contentTitle'
                        )
                        en = '{}. *{}*'.format(
                            (i + 1), contenttitle.get_text()
                            )
                        cn = str(phrase.contents[2]).strip()
                        cn = re.sub(r'\s{5,}', '', cn)
                        phrases_to_return.append([en, cn])

        return phrases_to_return

    def get_examples(self):
        examples_to_return = []
        soup = self.soup
        if soup:
            collinsResult = soup.find(
                id="collinsResult", class_="tab-content",
            )
            if collinsResult:
                examples = collinsResult.find_all('div', class_="examples")
                if examples:
                    for i, example in enumerate(examples):
                        texts = example.find_all('p')
                        text_en = '{}. *{}*'.format(
                            (i + 1), texts[0].get_text().strip()
                        )
                        text_cn = texts[1].get_text()
                        examples_to_return.append([text_en, text_cn])
                        if i >= 5:
                            break
        return examples_to_return

    def get_error_block(self):
        soup = self.soup
        if soup:
            error_block = soup.find("div", class_="error-typo")
            if error_block:
                return error_block
            else:
                return None
        else:
            return None


def test():
    while True:
        word = input('word: ')
        youdao = Youdao(word)
        trans = youdao.get_trans()
        print(trans)


if __name__ == '__main__':
    test()
