"# learning-activities" 
# How to run?
1.Clone the project
Find a folder where you want to place the project, open the console and execute
```sh
git clone <repository URL>
```
Then
```sh
cd <project directory>
```
2.Create a virtual environment
```sh
python -m venv <your desired environment name>
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```
Then install dependencies
```sh
pip install -r requirements.txt
```
3.Perform database migration
```sh
python manage.py migrate
```
4.Finally, run the server
```sh
python manage.py runserver
```
