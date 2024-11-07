#!/bin/bash

source ~/anaconda3/bin/activate quant #correct
#python Documents/my_python_file_name.py WRONG SEPARATLY GO TO FOLER WHTAN EXECUTE EITH python
cd ~/Code/Learn/QuantMod/TP/Shares/ #correct
python dataload.py sandbox #correct
python rebalance.py sandbox #correct
python orders.py sandbox #correct
conda deactivate