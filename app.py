# app.py
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, send_from_directory, abort)
from werkzeug.utils import secure_filename

from config import Config
from models import db
from models.student import Student
from models.organization import Organization
from models.opportunity import Opportunity
from models.application import Application


# App factory

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app

app = create_app()


# Context processor — expose session role to every template


@app.context_processor
def inject_session():
    return dict(session=session, now=datetime.utcnow, is_expired=is_expired)


# Helper utilities


def allowed_file(filename):
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS'])


def save_upload(file, subfolder=''):
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Prefix with timestamp to avoid collisions
        filename = f"{int(datetime.utcnow().timestamp())}_{filename}"
        dest = app.config['UPLOAD_FOLDER']
        if subfolder:
            dest = os.path.join(dest, subfolder)
        os.makedirs(dest, exist_ok=True)
        file.save(os.path.join(dest, filename))
        return filename
    return None


def match_percentage(student, opportunity):
    """
    Skills: 70 points  — matched required skills / total required
    Experience: 30 points — capped at required_exp, full 30 if req <= 0
    """
    skill_score = 0
    exp_score = 0

    # Skills
    student_skills = [s.strip().lower() for s in (student.skills or '').split(',') if s.strip()]
    required_skills = [s.strip().lower() for s in (opportunity.required_skills or '').split(',') if s.strip()]

    if student_skills and required_skills:
        matched = sum(1 for r in required_skills if r in student_skills)
        skill_score = (matched / len(required_skills)) * 70
    # else 0

    # Experience
    req_exp = opportunity.experience_required or 0
    student_exp = student.experience or 0
    if req_exp <= 0:
        exp_score = 30
    else:
        exp_score = min(student_exp / req_exp, 1.0) * 30

    total = round(skill_score + exp_score)
    return total


def profile_completion(student):
    """Return % of optional fields filled."""
    fields = [student.phone, student.address, student.education,
              student.skills, student.interests, student.resume]
    filled = sum(1 for f in fields if f)
    return round((filled / len(fields)) * 100)


def is_expired(opportunity):
    """A vacancy with no deadline never expires."""
    if not opportunity.deadline:
        return False
    return opportunity.deadline < datetime.utcnow().date()



# Email helper


def send_application_email(student, opportunity):
    """Send confirmation email — silently fails if MAIL_ENABLED is False."""
    if not app.config.get('MAIL_ENABLED'):
        return
    try:
        msg = EmailMessage()
        msg['Subject'] = f"Application Received – {opportunity.title}"
        msg['From'] = app.config['MAIL_SENDER']
        msg['To'] = student.email
        body = (
            f"Dear {student.full_name},\n\n"
            f"Your application for '{opportunity.title}' at "
            f"{opportunity.organization.organization_name} has been received.\n\n"
            f"Status: Pending\n\n"
            f"We will notify you of any updates.\n\n"
            f"Best regards,\nCareerHub Team"
        )
        msg.set_content(body)

        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as smtp:
            if app.config.get('MAIL_USE_TLS'):
                smtp.starttls()
            smtp.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            smtp.send_message(msg)
    except Exception as e:
        app.logger.warning(f"Email send failed: {e}")



# Decorators


def login_required_student(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'student':
            flash('Please log in as a student to access that page.', 'warning')
            return redirect(url_for('student_login'))
        return f(*args, **kwargs)
    return decorated


def login_required_org(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'org':
            flash('Please log in as an organization.', 'warning')
            return redirect(url_for('org_login'))
        return f(*args, **kwargs)
    return decorated


def login_required_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated



# Landing page

@app.route('/')
def home():
    today = datetime.utcnow().date()
    stats = {
        'students': Student.query.count(),
        'organizations': Organization.query.filter_by(verification_status='Verified').count(),
        'opportunities': Opportunity.query.filter(
            db.or_(Opportunity.deadline.is_(None), Opportunity.deadline >= today)
        ).count(),
        'applications': Application.query.count(),
    }
    latest_opps = (Opportunity.query
                   .filter(db.or_(Opportunity.deadline.is_(None), Opportunity.deadline >= today))
                   .order_by(Opportunity.created_at.desc())
                   .limit(3).all())
    return render_template('home.html', stats=stats, latest_opps=latest_opps)


# STUDENT ROUTES

@app.route('/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        errors = []
        if not full_name:
            errors.append('Full name is required.')
        if not email:
            errors.append('Email is required.')
        if not password:
            errors.append('Password is required.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if Student.query.filter_by(email=email).first():
            errors.append('Email already registered.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('register.html',
                                   full_name=full_name, email=email)

        student = Student(full_name=full_name, email=email)
        student.set_password(password)
        db.session.add(student)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('student_login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        student = Student.query.filter_by(email=email).first()
        if student and student.check_password(password):
            session.clear()
            session['role']       = 'student'
            session['student_id'] = student.student_id
            session['name']       = student.full_name
            flash(f'Welcome back, {student.full_name}!', 'success')
            return redirect(url_for('student_dashboard'))

        flash('Invalid email or password.', 'error')
    return render_template('login.html')


@app.route('/logout')
def student_logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))


@app.route('/dashboard')
@login_required_student
def student_dashboard():
    student = Student.query.get_or_404(session['student_id'])
    all_opps = Opportunity.query.order_by(Opportunity.created_at.desc()).all()

    # Recommended: match >= 50, top 4
    recommended = []
    for opp in all_opps:
        pct = match_percentage(student, opp)
        if pct >= 50:
            recommended.append((opp, pct))
    recommended.sort(key=lambda x: x[1], reverse=True)
    recommended = recommended[:4]

    # Latest 6
    latest = all_opps[:6]

    # Applications
    apps = (Application.query
            .filter_by(student_id=student.student_id)
            .order_by(Application.applied_at.desc())
            .all())

    completion = profile_completion(student)

    # Build match map for latest
    latest_match = {opp.opportunity_id: match_percentage(student, opp) for opp in latest}
    applied_ids  = {a.opportunity_id for a in apps}

    pending_count  = sum(1 for a in apps if a.status == 'Pending')
    accepted_count = sum(1 for a in apps if a.status == 'Accepted')
    rejected_count = sum(1 for a in apps if a.status == 'Rejected')

    return render_template('dashboard.html',
                           student=student,
                           recommended=recommended,
                           latest=latest,
                           latest_match=latest_match,
                           applications=apps,
                           applied_ids=applied_ids,
                           completion=completion,
                           pending_count=pending_count,
                           accepted_count=accepted_count,
                           rejected_count=rejected_count)


@app.route('/profile')
@login_required_student
def student_profile():
    student = Student.query.get_or_404(session['student_id'])
    completion = profile_completion(student)
    return render_template('profile.html', student=student, completion=completion)


@app.route('/manage-profile', methods=['GET', 'POST'])
@login_required_student
def manage_profile():
    student = Student.query.get_or_404(session['student_id'])

    if request.method == 'POST':
        action = request.form.get('action', 'update')

        if action == 'delete':
            # Delete the student and logout
            db.session.delete(student)
            db.session.commit()
            session.clear()
            flash('Your profile has been deleted.', 'success')
            return redirect(url_for('home'))

        # Update profile
        student.full_name  = request.form.get('full_name', student.full_name).strip()
        student.phone      = request.form.get('phone', '').strip()
        student.address    = request.form.get('address', '').strip()
        student.education  = request.form.get('education', '').strip()
        student.skills     = request.form.get('skills', '').strip()
        student.interests  = request.form.get('interests', '').strip()
        exp_raw            = request.form.get('experience', '0').strip()
        try:
            student.experience = int(exp_raw)
        except ValueError:
            student.experience = 0

        # Resume upload
        resume_file = request.files.get('resume')
        if resume_file and resume_file.filename:
            if allowed_file(resume_file.filename):
                filename = save_upload(resume_file)
                if filename:
                    student.resume = filename
            else:
                flash('Invalid file type. Only PDF, DOC, DOCX allowed.', 'error')
                return render_template('manage_profile.html', student=student)

        db.session.commit()
        session['name'] = student.full_name
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student_profile'))

    return render_template('manage_profile.html', student=student)


@app.route('/opportunities')
@login_required_student
def opportunities():
    student = Student.query.get_or_404(session['student_id'])
    filter_type = request.args.get('filter', 'all')
    query_text  = request.args.get('q', '').strip()
    location_f  = request.args.get('location', '').strip()
    type_f      = request.args.get('type', '').strip()

    q = Opportunity.query
    if query_text:
        like = f"%{query_text}%"
        q = q.filter(db.or_(
            Opportunity.title.ilike(like),
            Opportunity.required_skills.ilike(like),
            Opportunity.description.ilike(like)
        ))
    if location_f:
        q = q.filter(Opportunity.location.ilike(f"%{location_f}%"))
    if type_f:
        q = q.filter(Opportunity.opportunity_type == type_f)

    all_opps = q.order_by(Opportunity.created_at.desc()).all()
    applied_ids = {a.opportunity_id for a in student.applications}

    opp_list = []
    for opp in all_opps:
        pct = match_percentage(student, opp)
        if filter_type == 'recommended' and pct < 50:
            continue
        opp_list.append((opp, pct))

    # Distinct types/locations for the filter dropdowns
    all_types = sorted({o.opportunity_type for o in Opportunity.query.all() if o.opportunity_type})

    return render_template('opportunities.html',
                           opp_list=opp_list,
                           applied_ids=applied_ids,
                           filter_type=filter_type,
                           query_text=query_text,
                           location_f=location_f,
                           type_f=type_f,
                           all_types=all_types)


@app.route('/opportunity/<int:opportunity_id>')
@login_required_student
def opportunity_detail(opportunity_id):
    student = Student.query.get_or_404(session['student_id'])
    opp = Opportunity.query.get_or_404(opportunity_id)
    pct = match_percentage(student, opp)
    applied = Application.query.filter_by(
        student_id=student.student_id,
        opportunity_id=opp.opportunity_id
    ).first()
    return render_template('opportunity_detail.html',
                           opportunity=opp,
                           match_pct=pct,
                           applied=applied)


@app.route('/apply/<int:opportunity_id>', methods=['POST'])
@login_required_student
def apply_opportunity(opportunity_id):
    student = Student.query.get_or_404(session['student_id'])
    opp = Opportunity.query.get_or_404(opportunity_id)

    if is_expired(opp):
        flash('This vacancy has expired and is no longer accepting applications.', 'error')
        return redirect(url_for('opportunity_detail', opportunity_id=opportunity_id))

    # Check duplicate at application level
    existing = Application.query.filter_by(
        student_id=student.student_id,
        opportunity_id=opp.opportunity_id
    ).first()
    if existing:
        flash('You have already applied for this vacancy.', 'warning')
        return redirect(url_for('opportunity_detail', opportunity_id=opportunity_id))

    application = Application(
        student_id=student.student_id,
        opportunity_id=opp.opportunity_id,
        status='Pending'
    )
    try:
        db.session.add(application)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('You have already applied for this vacancy.', 'warning')
        return redirect(url_for('opportunity_detail', opportunity_id=opportunity_id))

    # Non-blocking email
    send_application_email(student, opp)

    flash(f'Application submitted for "{opp.title}"!', 'success')
    return redirect(url_for('my_applications'))


@app.route('/resume')
@login_required_student
def student_resume():
    student = Student.query.get_or_404(session['student_id'])
    if not student.resume:
        flash('You have not uploaded a resume yet.', 'warning')
        return redirect(url_for('student_profile'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], student.resume)


@app.route('/applications')
@login_required_student
def my_applications():
    student = Student.query.get_or_404(session['student_id'])
    apps = (Application.query
            .filter_by(student_id=student.student_id)
            .order_by(Application.applied_at.desc())
            .all())
    app_data = []
    for a in apps:
        pct = match_percentage(student, a.opportunity)
        app_data.append((a, pct))
    return render_template('applications.html', app_data=app_data, student=student)


# ORGANIZATION ROUTES

@app.route('/org/register', methods=['GET', 'POST'])
def org_register():
    if request.method == 'POST':
        org_name    = request.form.get('organization_name', '').strip()
        email       = request.form.get('email', '').strip().lower()
        password    = request.form.get('password', '')
        confirm     = request.form.get('confirm_password', '')
        phone       = request.form.get('phone', '').strip()
        address     = request.form.get('address', '').strip()
        description = request.form.get('description', '').strip()

        errors = []
        if not org_name:
            errors.append('Organization name is required.')
        if not email:
            errors.append('Email is required.')
        if not password:
            errors.append('Password is required.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if Organization.query.filter_by(email=email).first():
            errors.append('Email already registered.')

        # Verification document
        doc_file = request.files.get('verification_document')
        doc_filename = None
        if doc_file and doc_file.filename:
            if allowed_file(doc_file.filename):
                doc_filename = save_upload(doc_file)
            else:
                errors.append('Verification document must be PDF, DOC, or DOCX.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('organization_register.html',
                                   organization_name=org_name, email=email,
                                   phone=phone, address=address, description=description)

        org = Organization(
            organization_name=org_name,
            email=email,
            phone=phone,
            address=address,
            description=description,
            verification_document=doc_filename,
            verification_status='Pending'
        )
        org.set_password(password)
        db.session.add(org)
        db.session.commit()
        flash('Organization registered! Await admin verification before posting vacancies.', 'success')
        return redirect(url_for('org_login'))

    return render_template('organization_register.html')


@app.route('/org/login', methods=['GET', 'POST'])
def org_login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        org = Organization.query.filter_by(email=email).first()
        if org and org.check_password(password):
            session.clear()
            session['role']   = 'org'
            session['org_id'] = org.organization_id
            session['name']   = org.organization_name
            session['org_status'] = org.verification_status

            if org.verification_status == 'Pending':
                flash('Your organization is pending admin verification. You can view your dashboard but cannot post vacancies yet.', 'warning')
            elif org.verification_status == 'Rejected':
                flash('Your organization registration was rejected. Please contact admin.', 'error')
            else:
                flash(f'Welcome, {org.organization_name}!', 'success')

            return redirect(url_for('org_dashboard'))

        flash('Invalid email or password.', 'error')
    return render_template('organization_login.html')


@app.route('/org/logout')
def org_logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))


@app.route('/org/dashboard')
@login_required_org
def org_dashboard():
    org = Organization.query.get_or_404(session['org_id'])
    vacancies = Opportunity.query.filter_by(organization_id=org.organization_id).all()
    today = datetime.utcnow().date()
    active_count = sum(1 for v in vacancies if not v.deadline or v.deadline >= today)

    all_apps = []
    for v in vacancies:
        all_apps.extend(v.applications)
    all_apps.sort(key=lambda a: a.applied_at, reverse=True)

    total_apps    = len(all_apps)
    pending_count = sum(1 for a in all_apps if a.status == 'Pending')
    accepted_count = sum(1 for a in all_apps if a.status == 'Accepted')
    recent_apps   = all_apps[:5]

    return render_template('organization_dashboard.html',
                           org=org,
                           vacancies_count=len(vacancies),
                           active_count=active_count,
                           total_apps=total_apps,
                           pending_count=pending_count,
                           accepted_count=accepted_count,
                           recent_apps=recent_apps,
                           recent_vacancies=sorted(vacancies, key=lambda v: v.created_at, reverse=True)[:4])


@app.route('/org/profile', methods=['GET', 'POST'])
@login_required_org
def org_profile():
    org = Organization.query.get_or_404(session['org_id'])
    if request.method == 'POST':
        org.organization_name = request.form.get('organization_name', org.organization_name).strip()
        org.phone       = request.form.get('phone', '').strip()
        org.address     = request.form.get('address', '').strip()
        org.description = request.form.get('description', '').strip()
        # verification_status NOT changeable by org
        db.session.commit()
        session['name'] = org.organization_name
        flash('Profile updated!', 'success')
        return redirect(url_for('org_profile'))
    return render_template('organization_profile.html', org=org)


@app.route('/org/post-opportunity', methods=['GET', 'POST'])
@login_required_org
def post_opportunity():
    org = Organization.query.get_or_404(session['org_id'])
    if org.verification_status != 'Verified':
        flash('Only verified organizations can post vacancies.', 'error')
        return redirect(url_for('org_dashboard'))

    if request.method == 'POST':
        title          = request.form.get('title', '').strip()
        description    = request.form.get('description', '').strip()
        opp_type       = request.form.get('opportunity_type', '').strip()
        req_skills     = request.form.get('required_skills', '').strip()
        location       = request.form.get('location', '').strip()
        salary         = request.form.get('salary', '').strip()
        deadline_str   = request.form.get('deadline', '').strip()
        exp_req        = request.form.get('experience_required', '0').strip()

        errors = []
        if not title:       errors.append('Title is required.')
        if not description: errors.append('Description is required.')
        if not opp_type:    errors.append('Opportunity type is required.')
        if not location:    errors.append('Location is required.')
        if not deadline_str:errors.append('Deadline is required.')

        deadline = None
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                errors.append('Invalid deadline date.')

        try:
            exp_req = int(exp_req)
        except ValueError:
            exp_req = 0

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('post_opportunity.html',
                                   title=title, description=description,
                                   opportunity_type=opp_type,
                                   required_skills=req_skills,
                                   location=location, salary=salary,
                                   deadline=deadline_str,
                                   experience_required=exp_req)

        opp = Opportunity(
            organization_id=org.organization_id,
            title=title,
            description=description,
            opportunity_type=opp_type,
            required_skills=req_skills,
            location=location,
            salary=salary,
            deadline=deadline,
            experience_required=exp_req
        )
        db.session.add(opp)
        db.session.commit()
        flash('Vacancy posted successfully!', 'success')
        return redirect(url_for('manage_opportunities'))

    return render_template('post_opportunity.html')


@app.route('/org/manage-opportunities')
@login_required_org
def manage_opportunities():
    org = Organization.query.get_or_404(session['org_id'])
    vacancies = (Opportunity.query
                 .filter_by(organization_id=org.organization_id)
                 .order_by(Opportunity.created_at.desc())
                 .all())
    today = datetime.utcnow().date()
    return render_template('manage_opportunities.html',
                           vacancies=vacancies, org=org, today=today)


@app.route('/org/edit-opportunity/<int:opp_id>', methods=['GET', 'POST'])
@login_required_org
def edit_opportunity(opp_id):
    org = Organization.query.get_or_404(session['org_id'])
    opp = Opportunity.query.get_or_404(opp_id)
    if opp.organization_id != org.organization_id:
        flash('Unauthorized.', 'error')
        return redirect(url_for('manage_opportunities'))

    if request.method == 'POST':
        opp.title              = request.form.get('title', opp.title).strip()
        opp.description        = request.form.get('description', opp.description).strip()
        opp.opportunity_type   = request.form.get('opportunity_type', opp.opportunity_type).strip()
        opp.required_skills    = request.form.get('required_skills', opp.required_skills).strip()
        opp.location           = request.form.get('location', opp.location).strip()
        opp.salary             = request.form.get('salary', opp.salary or '').strip()
        deadline_str           = request.form.get('deadline', '').strip()
        exp_req                = request.form.get('experience_required', '0').strip()

        if deadline_str:
            try:
                opp.deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid deadline date.', 'error')
                return render_template('post_opportunity.html', opp=opp, edit=True)
        try:
            opp.experience_required = int(exp_req)
        except ValueError:
            opp.experience_required = 0

        db.session.commit()
        flash('Vacancy updated!', 'success')
        return redirect(url_for('manage_opportunities'))

    return render_template('post_opportunity.html', opp=opp, edit=True)


@app.route('/org/delete-opportunity/<int:opp_id>', methods=['POST'])
@login_required_org
def delete_opportunity(opp_id):
    org = Organization.query.get_or_404(session['org_id'])
    opp = Opportunity.query.get_or_404(opp_id)
    if opp.organization_id != org.organization_id:
        flash('Unauthorized.', 'error')
        return redirect(url_for('manage_opportunities'))
    db.session.delete(opp)
    db.session.commit()
    flash('Vacancy deleted.', 'success')
    return redirect(url_for('manage_opportunities'))


@app.route('/org/applicants')
@login_required_org
def org_applicants():
    org = Organization.query.get_or_404(session['org_id'])
    vacancies = Opportunity.query.filter_by(organization_id=org.organization_id).all()
    opp_id = request.args.get('opp_id', type=int)

    selected_opp = None
    if opp_id:
        selected_opp = Opportunity.query.get(opp_id)
        if selected_opp and selected_opp.organization_id != org.organization_id:
            selected_opp = None

    applicant_data = []
    for vac in vacancies:
        if selected_opp and vac.opportunity_id != selected_opp.opportunity_id:
            continue
        for application in vac.applications:
            student = application.student
            pct = match_percentage(student, vac)
            applicant_data.append({
                'application': application,
                'student': student,
                'opportunity': vac,
                'match_pct': pct
            })

    return render_template('applicants.html',
                           applicant_data=applicant_data,
                           vacancies=vacancies,
                           selected_opp=selected_opp,
                           org=org)


@app.route('/org/update-status/<int:application_id>', methods=['POST'])
@login_required_org
def update_application_status(application_id):
    org = Organization.query.get_or_404(session['org_id'])
    application = Application.query.get_or_404(application_id)
    # Verify ownership
    if application.opportunity.organization_id != org.organization_id:
        flash('Unauthorized.', 'error')
        return redirect(url_for('org_applicants'))

    new_status = request.form.get('status', 'Pending')
    valid_statuses = ['Pending', 'Shortlisted', 'Accepted', 'Rejected']
    if new_status in valid_statuses:
        application.status = new_status
        db.session.commit()
        flash('Application status updated.', 'success')
    else:
        flash('Invalid status.', 'error')

    opp_id = application.opportunity_id
    return redirect(url_for('org_applicants', opp_id=opp_id))


@app.route('/org/resume/<int:student_id>')
@login_required_org
def org_resume(student_id):
    org = Organization.query.get_or_404(session['org_id'])
    student = Student.query.get_or_404(student_id)

    # Authorization: org must own an opportunity this student applied to
    authorized = False
    for vac in org.opportunities:
        for application in vac.applications:
            if application.student_id == student_id:
                authorized = True
                break
        if authorized:
            break

    if not authorized:
        abort(403)

    if not student.resume:
        flash('No resume uploaded.', 'warning')
        return redirect(url_for('org_applicants'))

    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               student.resume,
                               as_attachment=True)


# ADMIN ROUTES

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if (email == app.config['ADMIN_EMAIL'].lower() and
                password == app.config['ADMIN_PASSWORD']):
            session.clear()
            session['role'] = 'admin'
            session['name'] = 'Admin'
            flash('Welcome, Admin!', 'success')
            return redirect(url_for('admin_dashboard'))

        flash('Invalid admin credentials.', 'error')
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))


@app.route('/admin/dashboard')
@login_required_admin
def admin_dashboard():
    pending  = Organization.query.filter_by(verification_status='Pending').all()
    verified = Organization.query.filter_by(verification_status='Verified').all()
    rejected = Organization.query.filter_by(verification_status='Rejected').all()
    students_count = Student.query.count()
    opps_count = Opportunity.query.count()
    apps_count = Application.query.count()
    return render_template('admin_dashboard.html',
                           pending=pending,
                           verified=verified,
                           rejected=rejected,
                           students_count=students_count,
                           opps_count=opps_count,
                           apps_count=apps_count)


@app.route('/admin/verification-doc/<int:org_id>')
@login_required_admin
def admin_verification_doc(org_id):
    org = Organization.query.get_or_404(org_id)
    if not org.verification_document:
        flash('No verification document uploaded.', 'warning')
        return redirect(url_for('admin_org_detail', org_id=org_id))
    return send_from_directory(app.config['UPLOAD_FOLDER'], org.verification_document)


@app.route('/admin/organizations')
@login_required_admin
def admin_organizations():
    orgs = Organization.query.order_by(Organization.created_at.desc()).all()
    return render_template('admin_organizations.html', orgs=orgs)


@app.route('/admin/organization/<int:org_id>')
@login_required_admin
def admin_org_detail(org_id):
    org = Organization.query.get_or_404(org_id)
    return render_template('admin_organizations.html', orgs=[org], detail_org=org)


@app.route('/admin/verify/<int:org_id>', methods=['POST'])
@login_required_admin
def admin_verify_org(org_id):
    org = Organization.query.get_or_404(org_id)
    note = request.form.get('note', '').strip()
    org.verification_status = 'Verified'
    org.verification_note   = note
    db.session.commit()
    flash(f'{org.organization_name} has been verified.', 'success')
    return redirect(url_for('admin_organizations'))


@app.route('/admin/reject/<int:org_id>', methods=['POST'])
@login_required_admin
def admin_reject_org(org_id):
    org = Organization.query.get_or_404(org_id)
    note = request.form.get('note', '').strip()
    org.verification_status = 'Rejected'
    org.verification_note   = note
    db.session.commit()
    flash(f'{org.organization_name} has been rejected.', 'success')
    return redirect(url_for('admin_organizations'))


# Error handlers

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403


@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500


# Run

if __name__ == '__main__':
    app.run(debug=True)


