from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.handlers.sha2_crypt import sha256_crypt
from functools import wraps

# User Login Decorator


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash(
                message="Bu sayfayı görüntülemek için lütfen giriş yapın...", category="danger")
            return redirect(location=url_for("login"))
    return decorated_function

# User Register Form


class RegisterForm(Form):
    name = StringField(label="İsim Soyisim", validators=[
                       validators.Length(min=4, max=25, message="Bu alan 4 ila 25 karakter uzunluğunda olmalıdır...")])
    username = StringField(label="Kullanıcı Adı", validators=[
                           validators.Length(min=5, max=35, message="Bu alan 5 ila 35 karakter uzunluğunda olmalıdır...")])
    email = StringField(label="Email Adresi", validators=[validators.Email(
        message="Lütfen Geçerli Bir Email Adresi Girin...")])
    password = PasswordField(label="Parola", validators=[
        validators.DataRequired(message="Lütfen bir parola belirleyin"),
        validators.EqualTo(fieldname="confirm",
                           message="Parolanız Uyuşmuyor...")
    ])
    confirm = PasswordField(label="Parola Doğrula")


class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")


app = Flask(__name__)
app.secret_key = "hbblog"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "hakkicanbulucblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"


mysql = MySQL(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/article/<string:id>")
def detail(id):
    return "Article ID: " + id


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        sorgu = "SELECT * FROM users where username = %s"

        result = cursor.execute(sorgu, (username,))

        if result > 0:
            flash(message="Böyle bir kullanıcı adı bulunmaktadır...",
                  category="danger")
            return redirect(location=url_for("register"))
        else:
            sorgu = "INSERT into users(name,email,username,password) VALUES(%s,%s,%s,%s)"

            cursor.execute(sorgu, (name, email, username, password))
            mysql.connection.commit()
            cursor.close()
            flash(message="Başarıyla Kayıt Oldunuz...", category="success")
            return redirect(location=url_for("login"))
    else:
        return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "SELECT * FROM users where username = %s"

        result = cursor.execute(sorgu, (username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered, real_password):
                flash(message="Başarıyla Giriş Yaptınız...", category="success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(location=url_for("index"))
            else:
                flash(message="Parola Hatalı...", category="danger")
                return redirect(location=url_for("login"))
        else:
            flash(message="Böyle bir kullanıcı bulunmuyor...", category="danger")
            return redirect(location="login")
    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(location=url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    sorgu = "SELECT * FROM projects where author = %s"

    result = cursor.execute(sorgu, (session["username"],))

    if result > 0:
        projects = cursor.fetchall()
        return render_template("dashboard.html", projects=projects)
    else:
        return render_template("dashboard.html")


@app.route("/addproject", methods=["GET", "POST"])
def addproject():
    form = ProjectForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "INSERT INTO projects(title, author, content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu, (title, session["username"], content))

        mysql.connection.commit()

        cursor.close()

        flash(message="Proje Başarıyla Eklendi", category="success")
        return redirect(location=url_for("dashboard"))
    return render_template("addproject.html", form=form)

# Article Form


class ProjectForm(Form):
    title = StringField("Proje Başlığı", validators=[
                        validators.Length(min=5, max=100)])
    content = TextAreaField("Proje İçeriği", validators=[
                            validators.Length(min=10)])


@app.route("/projects")
def projects():
    cursor = mysql.connection.cursor()

    sorgu = "SELECT * FROM projects"

    result = cursor.execute(sorgu)

    if result > 0:
        projects = cursor.fetchall()
        return render_template("projects.html", projects=projects)
    else:
        return render_template("projects.html")


@app.route("/project/<string:id>")
def project(id):
    cursor = mysql.connection.cursor()

    sorgu = "SELECT * FROM projects where id = %s"

    result = cursor.execute(sorgu, (id,))

    if result > 0:
        project = cursor.fetchone()
        return render_template("project.html", project=project)
    else:
        return render_template("project.html")


@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    sorgu = "SELECT * FROM projects where author = %s and id = %s"

    result = cursor.execute(sorgu, (session["username"], id))

    if result > 0:
        sorgu1 = "DELETE FROM projects where id = %s"

        cursor.execute(sorgu1, (id,))

        mysql.connection.commit()

        return redirect(location=url_for("dashboard"))
    else:
        flash(message="Böyle bir proje yok veya bu işleme yetkiniz yok...",
              category="danger")
        return redirect(url_for("index"))


@app.route("/edit/<string:id>", methods=["GET", "POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()

        sorgu = "SELECT * FROM projects where id = %s and author = %s"
        result = cursor.execute(sorgu, (id, session["username"]))

        if result == 0:
            flash(message="Böyle bir proje yok veya bu işleme yetkiniz yok",
                  category="danger")
            return redirect(location=url_for("index"))
        else:
            project = cursor.fetchone()
            form = ProjectForm()

            form.title.data = project["title"]
            form.content.data = project["content"]
            return render_template("update.html", form=form)

    else:
        form = ProjectForm(request.form)

        newTitle = form.title.data
        newContent = form.content.data

        sorgu1 = "UPDATE projects SET title = %s, content = %s where id = %s"

        cursor = mysql.connection.cursor()

        cursor.execute(sorgu1, (newTitle, newContent, id))

        mysql.connection.commit()

        flash(message="Proje başarıyla güncellendi", category="success")

        return redirect(location=url_for("dashboard"))

@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return redirect(location=url_for("index"))
    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()

        sorgu = "SELECT * FROM projects where title like '%" + keyword + "%'"

        result = cursor.execute(sorgu)

        if result == 0:
            flash(message="Aranan kelimeye uygun makale bulunumadı...",
                  category="warning")
            return redirect(location=url_for("projects"))
        else:
            projects = cursor.fetchall()
            return render_template("projects.html", projects=projects)


if(__name__ == "__main__"):
    app.run(debug=True)
