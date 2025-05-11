import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import Flask, render_template, request, redirect, flash
from models import db, ContactMessage
from flask import session

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///messages.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'something-secret'

db.init_app(app)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        message = request.form["message"]

        new_msg = ContactMessage(name=name, email=email, phone=phone, message=message)
        db.session.add(new_msg)
        db.session.commit()

        # --- ارسال ایمیل ---
        sender_email = "info.almaskavir@gmail.com"
        sender_password = "gwtz tcaf nrsn ttkk"
        receiver_email = "info@acam-co.ir"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "پیام جدید از فرم تماس سایت"
        msg["From"] = sender_email
        msg["To"] = receiver_email

        text = f"""
        نام: {name}
        ایمیل: {email}
        تلفن: {phone}
        پیام:
        {message}
        """

        part = MIMEText(text, "plain", "utf-8")
        msg.attach(part)

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, receiver_email, msg.as_string())
        except Exception as e:
            print("خطا در ارسال ایمیل:", e)

        flash("پیام شما با موفقیت ذخیره و ارسال شد. متشکریم!")
        return redirect("/contact")

    return render_template("contact.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/metal")
def metal():
    return render_template("metal.html")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # مقادیر ورود ثابت برای شروع
        if username == "admin" and password == "1234":
            session["admin_logged_in"] = True
            return redirect("/admin/messages")
        else:
            flash("نام کاربری یا رمز عبور اشتباه است.")
            return redirect("/admin/login")

    return render_template("admin_login.html")

@app.route("/admin/messages")
def admin_messages():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    messages = ContactMessage.query.all()
    return render_template("admin_messages.html", messages=messages)

@app.route("/admin/delete/<int:msg_id>", methods=["POST"])
def delete_message(msg_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    msg = ContactMessage.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    flash("پیام حذف شد.")
    return redirect("/admin/messages")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("با موفقیت خارج شدید.")
    return redirect("/admin/login")

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
