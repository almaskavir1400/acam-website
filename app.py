import smtplib
import pdfkit  # نصب با pip install pdfkit و wkhtmltopdf
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, redirect, flash, session
from models import db, ContactMessage, Service, JoinRequest
from flask import jsonify
from flask import make_response



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///messages.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'something-secret'

db.init_app(app)

# صفحه اصلی با فرم تماس سریع
@app.route("/", methods=["GET"])
def home():
    services = Service.query.all()
    return render_template("home.html", services=services)

@app.route("/send-message-from-home", methods=["POST"])
def send_message_from_home():
    name = request.form["name"]
    email = request.form["email"]
    phone = request.form["phone"]
    message = request.form["message"]

    new_msg = ContactMessage(name=name, email=email, phone=phone, message=message)
    db.session.add(new_msg)
    db.session.commit()

    # ارسال ایمیل
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

    flash("پیام شما با موفقیت ارسال شد.")
    return redirect("/")

# صفحه تماس با ما
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

        send_email(name, email, phone, message)

        flash("پیام شما با موفقیت ذخیره و ارسال شد. متشکریم!")
        return redirect("/contact")

    return render_template("contact.html")

# تابع ارسال ایمیل (برای فرم تماس و همکاری مشترک)
def send_email(name, email, phone, message):
    sender_email = "info.almaskavir@gmail.com"
    sender_password = "gwtz tcaf nrsn ttkk"  # رمز اپلیکیشن جیمیل
    receiver_email = "info@acam-co.ir"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "پیام جدید از سایت"
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
        import traceback
        print("❌ خطا در ارسال ایمیل:")
        traceback.print_exc()

# صفحه خدمات
@app.route("/electrical")
def bargh_sanati():
    services = Service.query.all()
    return render_template("electrical.html", services=services)

# صفحه فلزکاری
@app.route("/metal")
def metal():
    return render_template("metal.html")

# صفحه همکاری با ما
@app.route('/cooperation')
def cooperation():
    return render_template('cooperation.html')

@app.route('/api/join-request', methods=['POST'])
def join_request():
    data = request.get_json()
    req = JoinRequest(
        fullname=data.get('fullname'),
        father=data.get('father'),
        gender=data.get('gender'),
        birthdate=data.get('birthdate'),
        national_id=data.get('national_id'),
        id_location=data.get('id_location'),
        marital_status=data.get('marital_status'),
        children=data.get('children'),
        military=data.get('military'),
        address=data.get('address'),
        phone=data.get('phone'),
        email=data.get('email'),
        education=data.get('education'),
        experience=data.get('experience'),
        message=data.get('message')
    )
    db.session.add(req)
    db.session.commit()
    
    send_email(
        name=data.get("fullname", ""),
        email=data.get("email", ""),
        phone=data.get("phone", ""),
        message=f"""درخواست همکاری جدید:

سابقه کار: {data.get('experience', '')}

توضیحات:
{data.get('message', '')}
"""
    )
    return jsonify({"message": "درخواست شما با موفقیت ثبت شد."})


@app.route("/admin/join-requests")
def admin_join_requests():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    requests = JoinRequest.query.order_by(JoinRequest.timestamp.desc()).all()
    return render_template("admin_join_requests.html", requests=requests)

@app.route("/admin/join-requests/delete/<int:req_id>", methods=["POST"])
def delete_join_request(req_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    req = JoinRequest.query.get_or_404(req_id)
    db.session.delete(req)
    db.session.commit()
    flash("درخواست حذف شد.")
    return redirect("/admin/join-requests")

@app.route("/admin/join-requests/view/<int:req_id>")
def view_join_request(req_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    req = JoinRequest.query.get_or_404(req_id)
    return render_template("join_request_detail.html", req=req)

@app.route("/admin/join-requests/pdf/<int:req_id>")
def download_join_request_pdf(req_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    req = JoinRequest.query.get_or_404(req_id)
    rendered = render_template("join_request_pdf.html", req=req)

    # 🔧 مسیر wkhtmltopdf.exe را مشخص کن
    path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

    pdf = pdfkit.from_string(rendered, False, configuration=config)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=request_{req.id}.pdf'
    return response

# ورود به پنل مدیریت
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "1234":
            session["admin_logged_in"] = True
            return redirect("/admin/messages")
        else:
            flash("نام کاربری یا رمز عبور اشتباه است.")
            return redirect("/admin/login")

    return render_template("admin_login.html")

# مشاهده پیام‌ها در پنل مدیریت
@app.route("/admin/messages")
def admin_messages():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    messages = ContactMessage.query.all()
    return render_template("admin_messages.html", messages=messages)

# حذف پیام در پنل مدیریت
@app.route("/admin/delete/<int:msg_id>", methods=["POST"])
def delete_message(msg_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    msg = ContactMessage.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    flash("پیام حذف شد.")
    return redirect("/admin/messages")

# خروج از پنل مدیریت
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("با موفقیت خارج شدید.")
    return redirect("/admin/login")

# مدیریت خدمات
@app.route("/admin/services", methods=["GET", "POST"])
def admin_services():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        new_service = Service(title=title, description=description)
        db.session.add(new_service)
        db.session.commit()
        flash("خدمت جدید اضافه شد.")
        return redirect("/admin/services")

    services = Service.query.all()
    return render_template("admin_services.html", services=services)

# حذف خدمت
@app.route("/admin/services/delete/<int:service_id>", methods=["POST"])
def delete_service(service_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    flash("خدمت حذف شد.")
    return redirect("/admin/services")

# ویرایش خدمت
@app.route("/admin/services/edit/<int:service_id>", methods=["GET", "POST"])
def edit_service(service_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    service = Service.query.get_or_404(service_id)

    if request.method == "POST":
        service.title = request.form["title"]
        service.description = request.form["description"]
        db.session.commit()
        flash("خدمت ویرایش شد.")
        return redirect("/admin/services")

    return render_template("edit_service.html", service=service)

@app.route("/api/send-message", methods=["POST"])
def api_send_message():
    try:
        name = request.json.get("name")
        email = request.json.get("email")
        phone = request.json.get("phone")
        message = request.json.get("message")

        new_msg = ContactMessage(name=name, email=email, phone=phone, message=message)
        db.session.add(new_msg)
        db.session.commit()

        # ✅ این خط اضافه شد تا ایمیل هم ارسال شود
        send_email(name, email, phone, message)

        return {"success": True, "message": "پیام شما با موفقیت ثبت شد ✅"}, 200
    except Exception as e:
        import traceback
        print("❌ خطا در ارسال فرم AJAX:")
        traceback.print_exc()
        return {"success": False, "message": "خطایی رخ داد"}, 500
    
# ساخت دیتابیس در اجرای اولیه
with app.app_context():
    db.create_all()

# اجرای برنامه
if __name__ == "__main__":
    app.run(debug=True)
