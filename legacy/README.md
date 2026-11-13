# Legacy Prototype Scripts & Artifacts Archive

This folder archives the original legacy monolithic prototype scripts, experimental notebooks, test scripts, and historical wheel binaries from the initial prototyping phase of ProjectVision.

All active functionalities from these scripts have been refactored and modularized into the production architecture:

| Legacy Script | Modular Production Replacement | Description |
|---|---|---|
| `main.py` / `temp3.py` | `api/` + `services/` + `core/` | Unified web server, routes, and multi-camera orchestration. |
| `cctv.py` | `models/motion_detector.py` | Frame differencing, background subtraction, and auto-recording. |
| `BlockChainMP.py` | `core/blockchain.py` | SHA-256 cryptographic chain, mining, and tamper-proof audit ledger. |
| `SpeechToText.py` | `models/speech_summarizer.py` | Audio recording, speech recognition, and heuristic text summarization. |
| `summarize.py` | `models/speech_summarizer.py` | NLP token ranking and lecture note generation. |
| `Email.py` | `core/notifications.py` | Asynchronous SMTP alert dispatcher with threat snapshots. |
| `sound.py` | `core/notifications.py` | Background audio siren alert trigger. |
| `encode_generator.py` | `models/face_recognizer.py` | 128-d face embedding generation and verification. |
| `addDatatoDatabase.py` | `services/firebase_service.py` | Firebase Realtime Database synchronization and offline fallback. |
| `weaponTest.py` / `WeaponTrain.py` | `models/weapon_detector.py` | YOLO threat detection and bounding box telemetry. |

