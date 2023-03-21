from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep

from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'

# Подключение к базе данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Создание таблицы в базе данных
class Whatsapp_mailing(db.Model):
    __tablename__ = 'whatsapp_mails'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), unique=True)
    count = db.Column(db.Integer)


# Если таблицы нету то тут она создается, после создания опять коментятся эти 2 строки
# app.app_context().push()
# db.create_all()

# Отрисовка index.html и работа формы с сохранением сообщения и колличества людей в базу данных
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        if request.form.get('count').isdigit():
            new_mailing = Whatsapp_mailing(
                text=request.form.get('text'),
                count=request.form.get('count'),
            )
            db.session.add(new_mailing)
            db.session.commit()
            flash('Успешно сохранено в базу данных. Теперь можно начать рассылку.','success')
        else:
            flash('Колличество контактов, должно быть числом.', 'error')
            return redirect(url_for('home'))
    return render_template("index.html")


# Выполнение рассылки из базы данных (последняя сохраненная запись) с помощью кноппки 'start mailing'
@app.route('/def')
def send_whatsapp_msg():
    try:
        last_mail = db.session.query(Whatsapp_mailing).order_by(Whatsapp_mailing.id.desc()).first()
        text = last_mail.text
        count = last_mail.count
    except AttributeError:
        flash('В базе данных нет ни одной записи.', 'error')
        return redirect(url_for('home'))

    driver = webdriver.Chrome()
    try:
        driver.get(url='https://web.whatsapp.com/')
        sleep(20)
        for i in range(1, count + 1):
            # Тут идет проверка есть ли архив в вотсапе, чтобы указать правильный путь до контакта
            try:
                people_xpath = driver.find_element(By.XPATH, f'//*[@id="pane-side"]/div[2]/div/div/div[{str(i)}]')
            except Exception as ex_:
                people_xpath = driver.find_element(By.XPATH, f'//*[@id="pane-side"]/div[1]/div/div/div[{str(i)}]')
            people_xpath.click()
            sleep(5)
            text_xpath = driver.find_element(By.XPATH, '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[1]')
            text_xpath.send_keys(text)
            text_xpath.send_keys('\n')
            sleep(5)
    except Exception as ex_:
        print(ex_)
    finally:
        driver.close()
        driver.quit()
        return 'Done!'


if __name__ == "__main__":
    app.run(debug=True)
