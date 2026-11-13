"""
ProjectVision REST API & Video Streaming Routes.
Provides endpoints for multi-camera video streaming, real-time analytics,
biometric attendance, security alerts, blockchain auditing, and speech summarization.
"""

import os
import time
import logging
from flask import Blueprint, Response, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename

from core.config import config
from core.event_bus import event_bus
from core.blockchain import identity_ledger
from services.pipeline_manager import pipeline_manager
from services.firebase_service import firebase_service
from services.attendance_service import attendance_service
from models.speech_summarizer import speech_transcriber

logger = logging.getLogger("ProjectVision.Routes")

api_bp = Blueprint("api", __name__)


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
# 6. Health & Diagnostic Check
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
# 7. HTML Dashboard Views & Static Assets
# ============================================================================

@api_bp.route('/images/<path:filename>')
def serve_student_image(filename):
    return send_from_directory(str(config.IMAGES_FOLDER), filename)

@api_bp.route('/')
def dashboard():
    """Primary ProjectVision unified command center dashboard."""
    return render_template('dashboard.html')

@api_bp.route('/grid')
@api_bp.route('/gp/index1')
def camera_grid():
    """4-Camera live quadrant monitoring view."""
    return render_template('camera_grid.html')

@api_bp.route('/notes')
@api_bp.route('/gp/SpeechToText.html')
@api_bp.route('/run_noter_script')
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
