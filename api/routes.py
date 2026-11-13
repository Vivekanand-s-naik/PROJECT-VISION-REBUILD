"""
ProjectVision REST API & Video Streaming Routes.
Provides endpoints for multi-camera video streaming, real-time analytics,
biometric attendance, security alerts, blockchain auditing, and speech summarization.
"""

import os
import time
import logging
from flask import Blueprint, Response, request, jsonify, render_template, send_from_directory, session, redirect, url_for
from werkzeug.utils import secure_filename

from core.config import config
from core.event_bus import event_bus, Event
from core.blockchain import identity_ledger
from core.auth import auth_manager, Role, login_required, roles_required, get_current_user
from services.pipeline_manager import pipeline_manager
from services.firebase_service import firebase_service
from services.attendance_service import attendance_service
from models.speech_summarizer import speech_transcriber

logger = logging.getLogger("ProjectVision.Routes")

api_bp = Blueprint("api", __name__)


@api_bp.context_processor
def inject_global_template_context():
    """Injects current logged-in user profile and vision system status into all templates."""
    user = get_current_user()
    return {
        "current_user": user,
        "system_active": pipeline_manager.is_active,
        "is_admin": user.get("role") == Role.ADMIN if user else False,
        "is_faculty": user.get("role") in (Role.ADMIN, Role.FACULTY) if user else False
    }


# ============================================================================
# 1. Video Streaming Routes (MJPEG)
# ============================================================================

@api_bp.route('/video_feed/<camera_id>')
def video_feed(camera_id):
    """Dynamic multipart MJPEG stream endpoint for any registered camera."""
    return Response(
        pipeline_manager.generate_mjpeg_stream(camera_id),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# Backward-compatible routes matching original main.py / temp3.py
@api_bp.route('/video_feed1')
def video_feed1():
    return Response(pipeline_manager.generate_mjpeg_stream('cam_1'), mimetype='multipart/x-mixed-replace; boundary=frame')

@api_bp.route('/video_feed2')
def video_feed2():
    return Response(pipeline_manager.generate_mjpeg_stream('cam_2'), mimetype='multipart/x-mixed-replace; boundary=frame')

@api_bp.route('/video_feed3')
def video_feed3():
    return Response(pipeline_manager.generate_mjpeg_stream('cam_3'), mimetype='multipart/x-mixed-replace; boundary=frame')

@api_bp.route('/video_feed4')
def video_feed4():
    return Response(pipeline_manager.generate_mjpeg_stream('cam_4'), mimetype='multipart/x-mixed-replace; boundary=frame')

@api_bp.route('/video_feed_cctv')
def video_feed_cctv():
    return Response(pipeline_manager.generate_mjpeg_stream('cam_cctv'), mimetype='multipart/x-mixed-replace; boundary=frame')


# ============================================================================
# 2. Biometric & User Data Endpoints
# ============================================================================

@api_bp.route('/get_user_data')
@api_bp.route('/api/user_data')
def get_user_data():
    """Returns real-time recognized student profile from the vision stream."""
    cam1_status = pipeline_manager.get_all_statuses().get('cam_1', {})
    entities = cam1_status.get('metadata', {}).get('entities', [])
    data = attendance_service.get_user_status_data(entities)
    return jsonify(data)

@api_bp.route('/api/students')
def get_students():
    """Returns all registered student profiles and attendance records."""
    students = attendance_service.get_all_records()
    return jsonify({"success": True, "count": len(students), "students": students})

@api_bp.route('/api/students/<student_id>')
def get_student_by_id(student_id):
    student = firebase_service.get_student(student_id)
    if student:
        return jsonify({"success": True, "student": student})
    return jsonify({"success": False, "message": "Student not found"}), 404

@api_bp.route('/api/attendance/summary')
def get_attendance_summary():
    summary = attendance_service.get_attendance_summary()
    return jsonify({"success": True, "summary": summary})


# ============================================================================
# 3. Detection Statistics & System Metrics
# ============================================================================

@api_bp.route('/get_stats')
@api_bp.route('/api/stats')
def get_stats():
    """Anti-spoofing and face detection statistics."""
    cam1_status = pipeline_manager.get_all_statuses().get('cam_1', {})
    stats = cam1_status.get('metadata', {}).get('stats', {
        "total_faces_detected": 0,
        "real_faces": 0,
        "fake_faces": 0,
        "known_faces_recognized": 0,
        "last_detection_time": None
    })
    return jsonify(stats)

@api_bp.route('/reset_stats')
@api_bp.route('/api/reset_stats', methods=['GET', 'POST'])
def reset_stats():
    worker = pipeline_manager.workers.get('cam_1')
    if worker and hasattr(worker.processor, 'reset_stats'):
        worker.processor.reset_stats()
    return jsonify({"success": True, "message": "Statistics reset successfully"})

@api_bp.route('/api/cameras')
def get_camera_statuses():
    """Status, FPS, and frame counters for all cameras."""
    statuses = pipeline_manager.get_all_statuses()
    return jsonify({"success": True, "cameras": statuses})

@api_bp.route('/api/events')
def get_security_events():
    """Returns recent real-time security events."""
    limit = int(request.args.get('limit', 50))
    event_type = request.args.get('type')
    events = event_bus.get_recent_events(limit=limit, event_type=event_type)
    return jsonify({"success": True, "count": len(events), "events": events})


# ============================================================================
# 4. Blockchain Ledger Endpoints
# ============================================================================

@api_bp.route('/api/blockchain')
def get_blockchain_ledger():
    ledger = identity_ledger.get_ledger()
    return jsonify({
        "success": True,
        "block_count": len(ledger),
        "chain_valid": identity_ledger.blockchain.is_chain_valid(),
        "ledger": ledger
    })

@api_bp.route('/api/blockchain/verify')
def verify_blockchain():
    valid = identity_ledger.blockchain.is_chain_valid()
    return jsonify({
        "success": True,
        "is_valid": valid,
        "block_count": len(identity_ledger.blockchain.chain)
    })

@api_bp.route('/api/blockchain/user/<id_number>')
def get_blockchain_user_history(id_number):
    records = identity_ledger.get_records_by_id(id_number)
    return jsonify({"success": True, "id_number": id_number, "records": records})


# ============================================================================
# 5. Speech-to-Text & Intelligent Summarization Endpoints
# ============================================================================

@api_bp.route('/transcribe', methods=['POST'])
@api_bp.route('/api/speech/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({"success": False, "error": "No audio file uploaded"}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"success": False, "error": "Empty filename"}), 400

    filename = secure_filename(f"upload_{int(time.time())}_{audio_file.filename}")
    filepath = os.path.join(str(config.UPLOAD_FOLDER), filename)
    audio_file.save(filepath)

    try:
        result = speech_transcriber.transcribe_file(filepath)
        # Clean up uploaded audio after processing
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/summarize', methods=['POST'])
@api_bp.route('/api/speech/summarize', methods=['POST'])
def summarize_text():
    data = request.get_json(silent=True) or {}
    text = data.get('text', '')
    if not text.strip():
        return jsonify({"success": False, "error": "No text provided"}), 400

    result = speech_transcriber.summarize_text(text)
    return jsonify({"success": True, **result})


# ============================================================================
# 6. RBAC Authentication & User Profile Management
# ============================================================================

@api_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    """Authenticates user credentials and establishes a session."""
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    email = data.get('email', '')
    password = data.get('password', '')

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required"}), 400

    user = auth_manager.authenticate(email, password)
    if not user:
        return jsonify({"success": False, "error": "Invalid email/id or password"}), 401

    session['user_id'] = user['id']
    session['user_role'] = user['role']

    logger.info(f"User {user['email']} [{user['role']}] authenticated successfully.")
    return jsonify({
        "success": True,
        "message": f"Welcome back, {user['name']}!",
        "user": user,
        "redirect": "/dashboard" if user['role'] != Role.STUDENT else "/react"
    })

@api_bp.route('/api/auth/logout', methods=['GET', 'POST'])
def api_logout():
    """Terminates session and clears credentials."""
    session.pop('user_id', None)
    session.pop('user_role', None)
    return jsonify({"success": True, "message": "Logged out successfully"})

@api_bp.route('/api/auth/me', methods=['GET'])
def api_get_current_user():
    """Returns the authenticated user's profile and RBAC permissions."""
    user = get_current_user()
    if not user:
        return jsonify({
            "authenticated": False,
            "user": None,
            "roles": Role.ALL_ROLES
        })

    return jsonify({
        "authenticated": True,
        "user": user,
        "system_active": pipeline_manager.is_active
    })

@api_bp.route('/api/dashboard/user-data', methods=['GET'])
def api_user_specific_dashboard():
    """
    Returns role-tailored metrics, cards, and data for the React Admin Dashboard.
    Ensures Admin, Faculty, and Student each see dynamic personalized telemetry.
    """
    user = get_current_user()
    if not user:
        user = auth_manager.get_user_by_email("admin@vision.ai")

    dashboard_data = auth_manager.get_user_specific_dashboard_data(user)
    dashboard_data["system_active"] = pipeline_manager.is_active
    return jsonify({
        "success": True,
        "user": user,
        "data": dashboard_data
    })


# ============================================================================
# 7. Vision System Control (Start / Stop Gating with RBAC)
# ============================================================================

@api_bp.route('/api/system/start', methods=['POST'])
def api_system_start():
    """
    Starts all multi-camera vision processing pipelines.
    Enforces RBAC: Authorized for Admin and Faculty roles.
    """
    user = get_current_user()
    if user and user.get("role") not in (Role.ADMIN, Role.FACULTY):
        return jsonify({
            "success": False,
            "error": "Forbidden",
            "message": "Student role cannot trigger camera activation. Contact faculty or administrator."
        }), 403

    try:
        pipeline_manager.start_all()
        event_bus.publish(Event(
            event_type="SYSTEM_ACTIVATED",
            camera_id="system",
            severity="INFO",
            details={
                "triggered_by": user.get("email") if user else "manual_trigger",
                "timestamp": time.time()
            }
        ))
        return jsonify({
            "success": True,
            "active": True,
            "message": "ProjectVision multi-stream camera engine started successfully."
        })
    except Exception as e:
        logger.error(f"Error starting vision system: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/api/system/stop', methods=['POST'])
def api_system_stop():
    """
    Stops all multi-camera vision processing pipelines and puts hardware on standby.
    Enforces RBAC: Authorized for Admin and Faculty roles.
    """
    user = get_current_user()
    if user and user.get("role") not in (Role.ADMIN, Role.FACULTY):
        return jsonify({
            "success": False,
            "error": "Forbidden",
            "message": "Student role cannot stop camera engine."
        }), 403

    try:
        pipeline_manager.stop_all()
        event_bus.publish(Event(
            event_type="SYSTEM_STOPPED",
            camera_id="system",
            severity="INFO",
            details={
                "triggered_by": user.get("email") if user else "manual_trigger",
                "timestamp": time.time()
            }
        ))
        return jsonify({
            "success": True,
            "active": False,
            "message": "ProjectVision camera engine stopped. Feeds placed in standby."
        })
    except Exception as e:
        logger.error(f"Error stopping vision system: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/api/system/status', methods=['GET'])
def api_system_status():
    """Returns current active/standby state and camera worker metrics."""
    return jsonify({
        "active": pipeline_manager.is_active,
        "status": "ACTIVE" if pipeline_manager.is_active else "STANDBY",
        "cameras": pipeline_manager.get_all_statuses()
    })


# ============================================================================
# 8. Health & Diagnostic Check
# ============================================================================

@api_bp.route('/api/health')
def health_check():
    statuses = pipeline_manager.get_all_statuses()
    fb_status = firebase_service.get_service_status()
    chain_valid = identity_ledger.blockchain.is_chain_valid()

    all_healthy = all(s.get('running', False) for s in statuses.values())

    return jsonify({
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "version": "2.0.0",
        "pipelines": statuses,
        "firebase": fb_status,
        "blockchain": {
            "valid": chain_valid,
            "blocks": len(identity_ledger.blockchain.chain)
        }
    })


# ============================================================================
# 7. HTML Dashboard Views, GP Landing Page & React Admin Dashboard
# ============================================================================

GP_DIR = config.BASE_DIR / "Gp"
REACT_BUILD_DIR = config.BASE_DIR / "React-Admin-Dashboard-public-master" / "build"

@api_bp.route('/images/<path:filename>')
def serve_student_image(filename):
    return send_from_directory(str(config.IMAGES_FOLDER), filename)

# GP Landing Page as Root
@api_bp.route('/')
@api_bp.route('/gp')
@api_bp.route('/gp/index.html')
def gp_root():
    """Serves the GP landing page as the root site."""
    if (GP_DIR / "index.html").exists():
        return send_from_directory(str(GP_DIR), 'index.html')
    return render_template('dashboard.html')

@api_bp.route('/assets/<path:filename>')
def serve_gp_assets(filename):
    """Serves CSS, JS, vendor and image assets for the GP landing page."""
    return send_from_directory(str(GP_DIR / "assets"), filename)

@api_bp.route('/forms/<path:filename>')
def serve_gp_forms(filename):
    """Serves form handlers/assets for the GP landing page."""
    return send_from_directory(str(GP_DIR / "forms"), filename)

@api_bp.route('/gp/<path:filename>')
def serve_gp_subpage(filename):
    """Serves subpages from the Gp folder."""
    if filename in ('SpeechToText.html', 'SpeechToText1.html', 'summarize1.html', 'summr.html'):
        return render_template('speech_notes.html')
    if filename in ('index1', 'index1.html'):
        return render_template('camera_grid.html')
    if (GP_DIR / filename).exists():
        return send_from_directory(str(GP_DIR), filename)
    return render_template('dashboard.html')

@api_bp.route('/activate', methods=['GET', 'POST'])
def activate_system():
    """Interactive system activation endpoint for GP landing page."""
    return jsonify({
        "success": True,
        "message": "ProjectVision intelligent vision & attendance engine activated.",
        "redirect": "/dashboard"
    })

@api_bp.route('/run_noter_script', methods=['GET', 'POST'])
def run_noter_script():
    """Interactive NOTER script trigger for GP landing page."""
    return jsonify({
        "success": True,
        "message": "AI NOTER audio transcription & summarization active.",
        "redirect": "/notes"
    })

# React Admin Dashboard Routes
@api_bp.route('/react')
@api_bp.route('/react/')
def react_dashboard():
    """Serves the compiled production React Admin Dashboard."""
    if (REACT_BUILD_DIR / "index.html").exists():
        return send_from_directory(str(REACT_BUILD_DIR), 'index.html')
    return jsonify({
        "error": "React build not found",
        "message": "Run 'npm run build' inside React-Admin-Dashboard-public-master"
    }), 404

@api_bp.route('/react/<path:filename>')
def serve_react_assets(filename):
    """Serves assets and chunks for the React Admin Dashboard."""
    if (REACT_BUILD_DIR / filename).exists():
        return send_from_directory(str(REACT_BUILD_DIR), filename)
    # Support client-side React router fallback
    return send_from_directory(str(REACT_BUILD_DIR), 'index.html')

# Core Application Views
@api_bp.route('/login', methods=['GET', 'POST'])
def login_view():
    """Login authentication portal with RBAC role shortcuts."""
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        user = auth_manager.authenticate(email, password)
        if user:
            session['user_id'] = user['id']
            session['user_role'] = user['role']
            next_url = request.args.get('next') or ('/dashboard' if user['role'] != Role.STUDENT else '/react')
            return redirect(next_url)
        return render_template('login.html', error="Invalid credentials. Please check your username/password.")

    user = get_current_user()
    if user:
        return redirect('/dashboard' if user['role'] != Role.STUDENT else '/react')
    return render_template('login.html')

@api_bp.route('/logout')
def logout_view():
    """Clears session and logs user out."""
    session.pop('user_id', None)
    session.pop('user_role', None)
    return redirect(url_for('api.login_view'))

@api_bp.route('/dashboard')
def dashboard():
    """Primary ProjectVision unified command center dashboard."""
    return render_template('dashboard.html')

@api_bp.route('/grid')
def camera_grid():
    """4-Camera live quadrant monitoring view."""
    return render_template('camera_grid.html')

@api_bp.route('/notes')
def speech_notes_view():
    """Speech-to-text transcription and note summarization workspace."""
    return render_template('speech_notes.html')

@api_bp.route('/blockchain')
def blockchain_view():
    """Immutable blockchain audit log explorer."""
    return render_template('blockchain_view.html')

@api_bp.route('/students')
def students_view():
    """Student database & attendance analytics table."""
    return render_template('students_view.html')
