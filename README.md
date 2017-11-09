### 依赖项安装：
```
pip2 install -U requests requests[socks]==2.12.0 lxml
```
or in Python3
```
pip3 install -U requests requests[socks]==2.12.0 lxml
```
### 修改 proxies
```python
PROXIES = {
    'http': 'socks5://127.0.0.1:1086',
    'https': 'socks5://127.0.0.1:1086'
}
```
修改为自己的 proxy 信息
```
python(2|3) ripper.py --name 小姐姐的名字
```