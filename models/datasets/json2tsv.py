import json
import csv
from sys import argv

files_num = len(argv)
#print(files_num)
text_a = []
text_b = []
label = []
dataset_kind = argv[1]
output_path = argv[files_num - 1]
for i in range(2,files_num - 1):
    file_path = argv[i]
    #print(file_path)
    with open(file_path , 'r', encoding="utf-8") as f1:
        lines = f1.readlines()
        #print(lines)
    for line in lines:
        content = json.loads(line.strip('\n'))
        text_a.append(content["sentence1"])
        text_b.append(content["sentence2"])
        if dataset_kind == "mnli" or dataset_kind == "snli" or dataset_kind == "CTI":
            if (content["gold_label"] == "entailment"):
                label_in = 0
            elif (content["gold_label"] == "contradiction"):
                label_in = 2
            else:
                label_in = 1
        elif dataset_kind == "simClue":
            if (content["label"] == "1"):
                label_in = 0
            elif ( content["label"] == "0"):
                label_in = 2
            else:
                label_in = 1
        else:
            print("dataset kind error!")
            break
        label.append(label_in)

with open(output_path, 'w', encoding="utf-8") as f2:
    tsv_w = csv.writer(f2, delimiter='\t', lineterminator='\n')
    tsv_w.writerow(['text_a', 'text_b', "label"])
    for num in range(len(text_a)):
        tsv_w.writerow([text_a[num], text_b[num], label[num]])