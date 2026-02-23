"# learning-activities" 
# 如何运行？
1.克隆项目
找到一个你想要置放项目的文件夹，打开控制台执行
```sh
git clone <仓库地址>
```
然后
```sh
cd <项目目录>
```
2.创建虚拟环境
```sh
python -m venv <你想要的环境名>
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```
然后安装依赖
```sh
pip install -r requirements.txt
```
3.执行数据库迁移
```sh
python manage.py migrate
```
4.最后运行服务器
```sh
manage.py runserver
```
