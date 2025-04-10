# Introduction
First, the output file needs to generate an executable path, and then the execute-single file is used to analyze the executable path. 
Finally, the slot obtained by executing a single path is compared with the slot in the original sol file. 
If the slot matches, it indicates that there is a delegate call vulnerability.

The description here is relatively simple, if you have questions please consult the author.

This library includes an example

# Deploy
```Bash
cd Delegate-Tracker
python3 -m venv slither
#python3 = 3.8.10
source slither/bin/activate
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple slither-analyzer solc-select colorama
#python versions other than 3.8.10 require additional execution of the following code
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple eth-typing==3.1.0 eth-utils==2.1.0 eth-rlp==0.3.0 eth-account==0.8.0 web3==6.20.2 hexbytes==0.3.1

cd /home/cc/Desktop/DelegateTracker
python3 -m venv manticore
#python3 = 3.8.10
source manticore/bin/activate
sudo apt-get upgrade
sudo apt-get install python3-dev python3-wheel build-essential
pip3 install --upgrade pip setuptools wheel -i https://pypi.tuna.tsinghua.edu.cn/simple
pip3 install manticore[native] solc-select colorama -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install protobuf==3.20.1 --force-reinstall
```
