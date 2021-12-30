from typing import List

import torch
import numpy as np

label_list = ['O', 'B-APART', 'I-APART', 'B-LOC', 'I-LOC', 'B-AREA', 'I-AREA', 'B-ROOM',
              'I-ROOM', 'B-FUR-TYPE', 'I-FUR-TYPE', 'B-PRICE', 'I-PRICE', 'B-CONV', 'I-CONV',
              'B-FUR', 'I-FUR', 'B-PJ', 'I-PJ', 'B-ID', 'I-ID']


def extract_entities(ner_model, tokenizer, cleaned_text: str) -> List[List[str]]:
    input_ids = torch.tensor([tokenizer.encode(cleaned_text)])  # lấy id của các tokens tương ứng
    # không dùng tokenize(decode(encode)), text sẽ bị lỗi khi tokenize do conflict với tokenizer mặc định
    tokens = tokenizer.convert_ids_to_tokens(tokenizer.encode(cleaned_text))  # lấy các token để đánh tags

    outputs = ner_model(input_ids).logits
    predictions = torch.argmax(outputs, dim=2)

    entities = [[token, label_list[pred]] for token, pred in zip(tokens, predictions[0].numpy()) if label_list[pred] != 'O']

    begin_tags = [0] * len(entities)
    for i in range(len(entities)):
        entity = entities[i]
        if 'B' in entity[1]:
            begin_tags[i] = 1

    idxs = list(np.where(np.array(begin_tags)==1)[0])
    results = []

    try:
        if len(idxs) > 1:
            for i in range(len(idxs) - 1):
                first_idx = idxs[i]
                last_idx = idxs[i+1]

                text = ' '.join([entity[0] for entity in entities[first_idx: last_idx]])
                text = text.replace('@@ ', '')
                text = text.replace('@@', '')
                results.append([text, entities[first_idx][1].replace('B-', '')])
    except Exception as e:
        print(e)

    last_b_idx = idxs[-1]
    last_i_idx = last_b_idx
    for entity in entities[last_b_idx:]:
        if 'O' != entity[1]:
            last_i_idx += 1

    if last_i_idx != last_b_idx:
        text = ' '.join([entity[0] for entity in entities[last_b_idx: last_i_idx]])
        text = text.replace('@@ ', '')
        text = text.replace('@@', '')
        results.append([text, entities[last_b_idx][1].replace('B-', '')])
    else:
        results.append([entities[last_b_idx][0], entities[last_b_idx][1].replace('B-', '')])

    return results