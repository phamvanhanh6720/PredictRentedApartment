from typing import List


def list_tags(data_point: dict) -> List[List[str]]:
    tags_list = []
    text = data_point['data']
    labels_list = data_point['label']

    arranged_tags =  arrange_label(data_point)

    for label_tag in arranged_tags:
        tag = text[label_tag[0]: label_tag[1]]
        label = label_tag[2]
        tag = tag.strip(' \n')
        if tag in ['', ' ']:
            continue
        else:
            tags_list.append([tag, label])

    return tags_list


def arrange_label(data_point: dict):
    labels_list = data_point['label']
    text = data_point['data']
    data_len = len(text)

    tags_list = []
    if len(labels_list) == 1:
        first_point = labels_list[0][0]
        second_point = labels_list[0][1]
        if first_point > 0:
            tags_list.append([0, first_point, 'O'])
        if second_point < data_len:
            tags_list.append(labels_list[0])
            tags_list.append([second_point, data_len, 'O'])

        return tags_list

    for i in range(0, len(labels_list) - 1):
        label = labels_list[i]
        next_label = labels_list[i+1]

        first_point = label[0]
        second_point = label[1]
        third_point = next_label[0]

        if first_point > 0 and i == 0:
            tags_list.append([0, first_point, 'O'])

        tags_list.append(label)
        if third_point <= second_point:
            continue
        else:
            tags_list.append([second_point, third_point, 'O'])

    last_tag = labels_list[-1]
    if last_tag[1] < data_len:
        tags_list.append(last_tag)
        tags_list.append([last_tag[1], data_len, 'O'])
    else:
        tags_list.append(last_tag)

    return tags_list