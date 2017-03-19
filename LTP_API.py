'''
pattern: ws(分词)，pos(词性标注)，ner(命名实体识别)，dp(依存句法分析)，sdp(语义依存分析)，srl(语义角色标注),all(全部任务)
fromat: xml(XML格式)，json(JSON格式)，conll(CONLL格式)，plain(简洁文本格式)
api_key : z8o079p31CVWTcjD2s2hBgjTxhWPOBzNcpYWMi2q
'''

import json
import collections
import requests
import sys
import os
import time


DIV = '--------------------------------------------------------------------------------'


class TextAnalysisByLTP:

    def __init__(self, path, dir_path_flag=False):
        self.dir_flag = dir_path_flag
        self.__url_get_base = "http://api.ltp-cloud.com/analysis/?"
        self.__api_key = 'z8o079p31CVWTcjD2s2hBgjTxhWPOBzNcpYWMi2q'
        self.__format = 'json'
        self.__path = path
        self.__output = 'output'
        self.__output_num = 1
        self.ner = []
        self.punctuation = ',.，。：、'
        self.hed = []
        self.result_path = os.getcwd() + '\\' + 'LTP_result'
        self.filename = ''
        self.process_count = 0
        self.fail_count = 0


    @staticmethod
    def readfile(path):
        with open(path, 'r', encoding='utf-8_sig') as f:
            file = f.readlines()
        return file

    def get(self, text, pattern):
        url = "%sapi_key=%s&text=%s&format=%s&pattern=%s" % (self.__url_get_base, self.__api_key, text, self.__format, pattern)
        r = requests.get(url)
        return r.text, r.status_code

    @staticmethod
    def __del_semicolon(sentence):
        for i in ';；':
            sentence = sentence.replace(i, ' ')
        return sentence

    def __del_punc(self, sentence):
        for i in self.punctuation:
            sentence = sentence.replace(i, ' ')
        return sentence

    @staticmethod
    def stopword(sentence):
        with open('stopword', encoding='utf-8') as f:
            stopword = f.readlines()
        for word in sentence:
            if word in stopword:
                sentence.pop(word)

    @staticmethod
    def __ws(line_json):
        sentence_token = []
        for word in line_json:
            ws_str = word['cont']
            sentence_token.append(ws_str)
        return sentence_token

    @staticmethod
    def __pos(line_json):
        sentence_token = []
        for word in line_json:
            cont = word['cont']
            pos = word['pos']
            pos_str = cont + '|' + pos
            sentence_token.append(pos_str)
        return sentence_token

    def __ner(self, line_json):
        name_entity = []
        sentence_token = []
        for word in line_json:
            cont = word['cont']
            pos = word['pos']
            ner = word['ne']
            ner_str = cont + '|' + pos + '|' + ner
            sentence_token.append(ner_str)
            if ner != 'O':
                name_entity.append(cont + '|' + ner)
        self.ner += name_entity
        return sentence_token

    def __dp(self, line_json):
        for word in line_json:
            id = word['id']
            cont = word['cont']
            pos = word['pos']
            parent = word['parent']
            relate = word['relate']
            print(word)

            if word['relate'] == 'HED':
                self.hed.append(word['cont'])

    def __writefile(self, processed_txt, pattern, count_flag=False):
        if count_flag:
            output_file = self.result_path + '\\' + pattern + '_' + 'count' + '_' + self.filename + '.txt'
        else:
            output_file = self.result_path + '\\' + pattern + '_' + self.filename + '.txt'
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(processed_txt)

    def __count(self, count_list, pattern):
        if pattern == 'ner':
            count_list = self.ner
        if pattern == 'dp':
            count_list = self.hed
            self.filename = 'sum'
        word_freq = collections.Counter(count_list)
        count_seq = sorted(word_freq.items(), key=lambda d: d[1], reverse=True)
        self.__writefile(str(count_seq), pattern, count_flag=True)
        return dict(word_freq.items())

    def __event(self,line_json):
        event={}
        #查找核心词，即事件谓语
        for word in line_json:
            if word['relate'] == 'HED' and word['pos'] == 'v':
                event['predicate'] = word['cont']
                pid = word['id']
        #查找主语和宾语
        for word in line_json:
            if word['parent'] == pid:
                if word['relate'] == 'SBV':
                    if word['pos'] == 'v':
                        #主语为事件
                        sbid = word['id']
                        sbevent = {}
                        sbevent['predicate'] = word['cont']
                        for word1 in line_json:
                            if word1['parent'] == sbid and word1['relate'] == 'ADV' and word1['cont'] == '别':
                                sbevent['predicate'] = word1['cont']+word['cont']
                        for word1 in line_json:
                            if word1['parent'] == sbid:
                                if word1['relate'] == 'SBV':
                                    sbevent['subject'] = word1['cont']
                                elif word1['relate'] == 'VOB':
                                    sbevent['object'] = word1['cont']
                        event['subject'] = sbevent
                    else:
                        event['subject'] = word['cont']
                elif word['relate'] == 'VOB':
                    if word['pos'] == 'v':
                        #宾语为事件
                        obid = word['id']
                        obevent = {}
                        obevent['predicate'] = word['cont']
                        for word1 in line_json:
                            if word1['parent'] == obid and word1['relate'] == 'ADV' and word1['cont'] == '别':
                                obevent['predicate'] = word1['cont'] + word['cont']
                        for word2 in line_json:
                            if word2['parent'] == obid:
                                if word2['relate'] == 'SBV':
                                    obevent['subject'] = word2['cont']
                                elif word2['relate'] == 'VOB':
                                    obevent['object'] = word2['cont']
                        event['object'] = obevent
                    else:
                        event['object'] = word['cont']
        print(event)

    def __getATT(self,word,line_json,strATT):
        id = word['id']
        for word1 in  line_json:
            if word1['parent'] == id and word1['realte'] == 'ATT':
                strATT += word1['cont']
            else:
                strATT = ''
        return strATT










    def process(self, pattern, output_count=True):
        count_list = []
        dir_name = 'LTP_result'
        for i in range(1, 100):
            if dir_name in os.listdir(os.getcwd()):
                self.result_path = self.result_path + '(' + str(i) + ')'
                dir_name = dir_name + '(' + str(i) + ')'
                continue
            else:
                os.makedirs(self.result_path)
                break
        if self.dir_flag:
            file_names = os.listdir(self.__path)
            for file_name in file_names:
                self.filename = file_name
                path = self.__path + '\\' + file_name
                file = self.readfile(path)
                processed_sent, count_list = self.__ltpget(file, pattern)
                if pattern != 'dp':
                    self.__writefile('\n'.join(processed_sent), pattern)
                    if output_count:
                        self.__count(count_list, pattern)
        else:
            file = self.readfile(self.__path)
            processed_sent, count_list = self.__ltpget(file, pattern)
            if pattern != 'dp':
                self.__writefile('\n'.join(processed_sent), pattern)
                if output_count:
                    self.__count(count_list, pattern)
            if pattern == 'dp':
                self.__count(count_list, pattern)
        return count_list

    def __ltpget(self, file, pattern):
        try_count = 0
        count_list = []
        processed_sent = []
        fail_list = []
        try:
            for line in file:
                if line == '\n':
                    processed_sent.append('\n')
                    continue
                try_count += 1
                line = self.__del_semicolon(line)
                line = self.__del_punc(line)
                result, code = self.get(line, pattern)
                print(code)
                while code == 503:
                    time.sleep(2)
                    result, code = self.get(line, pattern)
                if code == 200:
                    self.process_count += 1
                    line_json = json.loads(result)[0][0]
                   # print(line_json)
                    if pattern == 'ws':
                        sentence_token = self.__ws(line_json)
                    elif pattern == 'pos':
                        sentence_token = self.__pos(line_json)
                    elif pattern == 'ner':
                        sentence_token = self.__ner(line_json)
                    elif pattern == 'dp':
                        self.__dp(line_json)
                        print('Success prcoessing', str(self.process_count), 'sentence.   ', 'Fail', str(self.fail_count),
                              'sentence')
                        #事件抽取
                        self.__event(line_json)
                        continue
                    else:
                        return -1
                    str_token = ' '.join(sentence_token)
                    print('Success prcoessing', str(self.process_count), 'sentence.   ', 'Fail', str(self.fail_count), 'sentence')
                    count_list += sentence_token
                    processed_sent.append(str_token)
                else:
                    self.fail_count += 1
                    fail_list.append(try_count)
                    print(fail_list)
                    processed_sent.append('Processing failed')
                    continue
        except:
            print('final process:', str(self.process_count))
        return processed_sent, count_list

if __name__ == '__main__':
    file_path = r'C:\Users\kangwen\PycharmProjects\EventExtract\wanfangzhaiyao\wanfangzhaiyao_cut.txt'
    dic_path = r'C:\Users\kangwen\PycharmProjects\EventExtract\wanfangzhaiyao'
#    a = TextAnalysisByLTP(sys.argv[1])
#    a.process(sys.argv[2])
    a = TextAnalysisByLTP('testfile', dir_path_flag=False)
    a.process('dp', output_count=True)

