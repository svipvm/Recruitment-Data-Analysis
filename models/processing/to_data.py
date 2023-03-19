origin_data_file = 'data/train.txt'
train_data_file = '../ChineseTextualInference/train.tsv'
dev_data_file = '../ChineseTextualInference/dev.tsv'
data_label_map = { "neutral": 0, "contradiction": 2, "entailment": 1}
split_point = 100

data_index = 0
datasets = [[], []]

with open(origin_data_file, 'r', encoding='UTF-8') as f:
    lines = f.readlines()

print(len(lines))
for idx, line in enumerate(lines):
    # text = line.strip()
    text = line
    label = text.split('\t')[-1][:-1]
    text = text.replace(label, str(data_label_map[label]))
    if len(text.rstrip("\r\n").split("\t")) != 3: continue
    datasets[data_index].append(text)
    # print(datasets[data_index])
    data_index = 1 if idx % split_point == 0 else 0
    # break

print(len(datasets[0]), len(datasets[1]))

with open(train_data_file, 'w', encoding='UTF-8') as f:
    datasets[0] = ['text_a\ttext_b\tlabel\n'] + datasets[0]
    f.writelines(datasets[0])

with open(dev_data_file, 'w', encoding='UTF-8') as f:
    datasets[1] = ['text_a\ttext_b\tlabel\n'] + datasets[1]
    f.writelines(datasets[1])

print(datasets[0][1].rstrip("\r\n").split("\t"))