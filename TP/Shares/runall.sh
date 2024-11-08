#!/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
source /home/samsmu/anaconda3/bin/activate quant #correct
#python Documents/my_python_file_name.py WRONG SEPARATLY GO TO FOLER WHTAN EXECUTE EITH python
cd /home/samsmu/Code/Learn/QuantMod/TP/Shares/ #correct
python dataload.py sandbox #correct
python rebalance.py sandbox #correct
python orders.py sandbox #correct
conda deactivate