# 获取所用数据集的链接

AFQMC                   蚂蚁金融语义相似度数据集     https://tianchi.aliyun.com/dataset/dataDetail?dataId=106411
Chinese-STS-B           中文SNLI数据集              https://github.com/pluto-junzeng/CNSD
ChineseTextualInference 中文蕴含关系数据集           https://github.com/liuhuanyong/ChineseTextualInference
CINLID                  中文成语语义推理数据集       https://www.heywhale.com/mw/dataset/608a8c45d0bc41001722dc37/content
CMNLI                   MNLI 自然语言推理数据集      https://storage.googleapis.com/cluebenchmark/tasks/cmnli_public.zip
CSNLI                   SNLI 自然语言推理数据集      https://gitee.com/jiaodaxin/CNSD
LCQMC                   哈工大 LCQMC 数据集         http://icrc.hitsz.edu.cn/Article/show/171.html
OCNLI                   中文原版自然语言推理数据集    https://storage.googleapis.com/cluebenchmark/tasks/ocnli_public.zip
OPPO-xiaobu             小布对话文本语义匹配数据集    https://tianchi.aliyun.com/competition/entrance/531851/introduction
PAWS-X                  谷歌 PAWS-X 数据集           https://github.com/google-research-datasets/paws
PKU-Paraphrase-Bank     北大中文文本复述数据集        https://github.com/pkucoli/PKU-Paraphrase-Bank/

# 将数据集从json（jsonl）转换为tsv的脚本的使用方法

```
python json2tsv.py [simClue/mnli/snli/CTI] [dataset1-path] [dataset2-path] ... [output-path]
```
