from ast import keyword
from crypt import methods
import email
from sqlite3 import Cursor
from unicodedata import name
from unittest import result
from click import confirm
from flask import Flask, render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators,EmailField
from wtforms.validators import email_validator
from passlib.handlers.sha2_crypt import sha256_crypt
from functools import wraps

class Register(Form):
    name = StringField("İsim Soyisim",validators=[validators.Length(min = 4, max=35,message="4 ile 35 karakter arası giriş yapın!")])
    username = StringField("Kullanıcı Adı",validators=[validators.Length(min = 5, max=35,message="5 ile 35 karakter arası giriş yapın!")])
    email = StringField("Email Adresi",validators=[validators.Email(message="Lütfen geçerli bir email adresi girin!")])
    password = PasswordField("Parola",validators=[validators.DataRequired(message="Lütfen bir parola giriniz!"),
                                                    validators.EqualTo(fieldname="confirm",message="Parolanız uyuşmuyor!")])
    confirm = PasswordField("Parola Doğrula")

class Login(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")

app = Flask(__name__)

app.secret_key = "ozayblog"
app.config["MYSQL_HOST"] =  "127.0.0.1"
app.config["MYSQL_USER"] =  "root"
app.config["MYSQL_PASSWORD"] =  ""
app.config["MYSQL_DB"] =  "ozayblog"
app.config["MYSQL_CURSORCLASS"] =  "DictCursor"

mysql = MySQL(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lüfen giriş yapın!","danger")
            return redirect(url_for("login"))
    return decorated_function

@app.route('/')
def index():
    articles = [
        {"id":1,"title":"Deneme","content":"Deneme1 içeriği"},
        {"id":2,"title":"Deneme2","content":"Deneme2 içeriği"},
        {"id":3,"title":"Deneme3","content":"Deneme3 içeriği"}
    ]

    return render_template("index.html",articles =articles)

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/articles')
def articles():
    cursor = mysql.connection.cursor()
    query = "Select * From articles "
    result = cursor.execute(query)

    if result >0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles=articles)
    else:
        return render_template("articles.html")

@app.route('/article/<string:id>')
def detail(id):
    cursor = mysql.connection.cursor()
    query = "Select * From articles where id = %s"
    result = cursor.execute(query,(id,))
    if result>0:
        article = cursor.fetchone()
        return render_template("article.html",article = article)
    else:
        return render_template("article.html")

@app.route('/dashboard')
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    query = "Select * From articles where author = %s"
    result = cursor.execute(query,(session["username"],))
    if result>0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles) 
    else:
        return render_template("dashboard.html")    

@app.route('/addarticle',methods = ["GET", "POST"])
def addarticle():
    form = Article(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        query ="Insert into articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(query,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()

        flash("Makale Başarıyla Eklendi","success")
        return redirect(url_for("dashboard"))
    return render_template("addarticle.html", form = form)

@app.route('/delete/<string:id>')
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    query = "Select * From articles where author = %s and id= %s" 
    result = cursor.execute(query,(session["username"],id))
    if result>0:
        query2 = "Delete from articles where id = %s"
        cursor.execute(query2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu işlemi yapmaya yetkiniz yok","danger")
        return redirect(url_for("index"))

@app.route('/edit/<string:id>',methods = ["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        query = "Select * From articles where id =%s and author = %s"
        result = cursor.execute(query,(id,session["username"]))
        if result==0:
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")
            return redirect(url_for("index"))
        else:
            article =   cursor.fetchone()
            form = Article()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)
    else:
        form = Article(request.form)

        new_title = form.title.data
        new_content = form.content.data
        query2 = "Update articles Set title = %s,content = %s where id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(query2,(new_title,new_content,id))
        mysql.connection.commit()
        flash("Makale Başarıyla Güncellendi.","success")
        return redirect(url_for("dashboard"))

@app.route("/search",methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        query = "Select * from articles where title like '%" + keyword + "%'"
        result = cursor.execute(query)
        if result == 0:
            flash("Aranan kelimeye uygun makale bulunamadı...","danger")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html",articles = articles)
@app.route('/register',methods=["GET","POST"])
def register():
    form = Register(request.form)
    if request.method == "POST" and form.validate(  ):
        name =  form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        query =  "Insert into users(name,username,email,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(query,(name,username,email,password))
        mysql.connection.commit()
        cursor.close()

        flash("Başarıyla Kayıt Oldunuz...","success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html",form=form) 

@app.route('/login',methods = ["GET","POST"])
def login():
    form = Login(request.form)

    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        query = "Select * From users where username = %s"
        result = cursor.execute(query,(username,))
        if result >0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla Giriş Yaptınız.","success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Parolanız Hatalı...","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor...","danger")
            return redirect(url_for("login"))

    return render_template("login.html",form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash("Başarıyla Çıkış Yaptınız...","info")
    return redirect(url_for("index"))

class Article(Form):
    title = StringField("Makale Başlığı",validators=[validators.Length(min=5,max=100)])
    content = TextAreaField("Makale İçeriği",validators=[validators.Length(min=10)])


if __name__ == "__main__":
    app.run(debug=True)

