# Prepare datasets 

## Training classification dataset example format:<br>

1. Suggest split dataset of ratio is 10:1:1.(train:val:test)

```
train
├── class_1
│   ├── 1.jpg
│   ├── 2.jpg
│   ├── 3.jpg
...
│   ├── 29.jpg
│   └── 30.jpg
└── class_2
    ├── 1.jpg
    ├── 2.jpg
    ├── 3.jpg
    ...
    ├── 29.jpg
    └── 30.jpg


valid
├── class_1
│   ├── 1.jpg
│   ├── 2.jpg
│   └── 3.jpg
└── class_2
    ├── 1.jpg
    ├── 2.jpg
    └── 3.jpg

test
├── class_1
│   ├── 1.jpg
│   ├── 2.jpg
│   └── 3.jpg
└── class_2
    ├── 1.jpg
    ├── 2.jpg
    └── 3.jpg
```
<br>

## Training YOLO dataset example format:<br>

1. Suggest split dataset of ratio is 10:1:1.(train:val:test)
2. The .txt is class_index, X, Y, W, H of YOLO format, you may use [labelimg](https://github.com/tzutalin/labelImg) to  get lable.txt


```
train
├── 0.jpg
├── 0.txt
├── 10000.jpg
├── 10000.txt
├── 10001.jpg
├── 1000.jpg
├── 1000.txt
├── 10069.jpg
├── 10069.txt
├── 1006.jpg
├── 1006.txt
├── 10078.jpg
...
├── 840.jpg
└── 840.txt


vaild
├── 0.jpg
├── 0.txt
├── 10000.jpg
├── 10000.txt
├── 10001.jpg
├── 10001.txt
├── 10002.jpg
├── 10002.txt
...
├── 840.jpg
└── 840.txt

test
├── 0.jpg
├── 0.txt
├── 10000.jpg
├── 10000.txt
├── 10001.jpg
├── 10001.txt
├── 10002.jpg
├── 10002.txt
...
├── 840.jpg
└── 840.txt

```