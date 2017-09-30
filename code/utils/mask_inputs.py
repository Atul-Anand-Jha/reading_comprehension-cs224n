import os
import sys
from os.path import join as pjoin
import numpy as np
import Config

cfg = Config.Config()
ROOT_DIR = cfg.ROOT_DIR

suffixes = ['context', 'question']

# for test
def mask_input_test(suffixes, set_name='train'):
    save_path = pjoin(ROOT_DIR, 'cache')
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    for suf in suffixes:
        max_len = cfg.context_max_len if suf == 'context' else cfg.question_max_len
        file_name = set_name + '.' + suf + '_masked'
        file_path = pjoin(save_path, file_name)

        data_path = pjoin(ROOT_DIR, 'data/squad', set_name + '.ids.' + suf)
        print('Reading data from {}'.format(data_path))
        with open(data_path, 'r') as fdata:
            raw_data = [map(int,d.strip().split(' ')) for d in fdata.readlines()]

        mask_data = [mask_input(rd, max_len) for rd in raw_data]
        np.save(file_path, np.array(mask_data))

        # temp return
        return file_path
        # with open(file_path, 'wb') as fin:
        #     for rd in raw_data:
        #         mask = [True] * len(rd)
        #         if len(rd) > max_len:
        #             fin.write('%s %s' % (rd[:max_len], mask[:max_len]).join('\n'))
        #         else:
        #             fin.write(''.join('%s %s' % (rd + [0]*(max_len - len(rd)),
        #                        mask+[False]*(max_len - len(rd)))))

def read_answers(data_dir, set_names=['train', 'val'], suffix = '.span'):
    '''
    :param data_dir: data directory
    :param set_names: names of datasets, it should be a list
    :param suffix: the suffix of the anser, i.e. '.span'
    :return:

    '''

    #TODO: change the suffix accordingly.

    assert isinstance(set_names, list), 'the type of set_names should be list.'
    assert isinstance(suffix, str), 'the type of set_names should be string.'

    dict = {}
    for sn in set_names:
        data_path = pjoin(data_dir, sn + suffix)
        assert os.path.exists(data_path), 'the path {} does not exist, please check again.'.format(data_path)
        print('Reading answer from file: {}{}'.format(sn, suffix))
        with open(data_path, 'r') as fdata:
            answer = [map(int, line.strip().split(' ')) for line in fdata.readlines()]
        name = sn + '_answer'
        # TODO: need to validate the right way of representing the answer.
        dict[name] = answer

    return dict

def mask_dataset(data_dir, set_names=['train', 'val'], suffixes=['context', 'question']):
    dict = {}
    for sn in set_names:
        for suf in suffixes:
            max_len = cfg.context_max_len if suf == 'context' else cfg.question_max_len
            data_path = pjoin(data_dir,sn+'.ids.'+suf)
            print('------------ cute line ----------------')
            print('Reading dataset: {}-{}'.format(sn, suf))
            with open(data_path, 'r') as fdata:
                raw_data = [map(int, line.strip().split(' ')) for line in fdata.readlines()]
            print('The raw data length is {}'.format(len(raw_data)))
            name = sn + '_' + suf
            # masked_data = [mask_input(rd, max_len) for rd in raw_data]
            dict[name] = raw_data

    return dict

# return (data, mask)
def mask_input(data_list, max_len):
    l = len(data_list)
    mask = [True] * l
    if l > max_len:
        return data_list[:max_len], mask[:max_len]
    else:
        return data_list + [0] * (max_len - l), mask + [False] * (max_len - l)


if __name__ == '__main__':
    data_path = pjoin(ROOT_DIR, 'data/squad')
    # test1
    # data = mask_dataset(data_path)
    # for k,v in data.items():
    #     print('Length of {} is: {}'.format(k, len(v)))

    # test2
    # data = mask_dataset(data_path, ['test'], ['test'])
    # import sys
    # print(data)
    # print(sys.getsizeof(data) / 1.0e6)

    # test3
    # file_path = mask_input_test(['test'], 'test')
    # print(np.load(file_path + '.npy'))

    # test4
    # mask_input_test(suffixes)

    # read answer test
    dict_an = read_answers(data_path)
    for k, v in dict_an.items():
        print('set name : {} with top 10 values: {}'.format(k, v[:10]))

