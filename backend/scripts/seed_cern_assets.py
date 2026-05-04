from __future__ import annotations

from app.core.database import SessionLocal
from app.models.asset import Asset, AssetStatus, AssetVisibility


SEED_ASSETS: list[dict] = [
    {
        "title": "LHC Run Coordination Briefing - Q2 2026",
        "description": "Weekly run coordination update covering machine status, beam schedule, and experiment handover notes.",
        "file_name": "lhc_run_coordination_q2_2026.mp4",
        "mime_type": "video/mp4",
        "duration_seconds": 3120,
        "speaker": "Elena Rossi",
        "event_name": "LHC Operations Weekly",
        "status": AssetStatus.READY,
        "visibility": AssetVisibility.PRIVATE,
    },
    {
        "title": "ATLAS Trigger and Data Acquisition Seminar",
        "description": "Internal seminar on trigger menu evolution and DAQ throughput tuning for high-luminosity scenarios.",
        "file_name": "atlas_tdaq_seminar_2026_04_18.mp4",
        "mime_type": "video/mp4",
        "duration_seconds": 4285,
        "speaker": "Dr. Marco Klein",
        "event_name": "ATLAS Technical Seminar Series",
        "status": AssetStatus.READY,
        "visibility": AssetVisibility.PRIVATE,
    },
    {
        "title": "CMS Detector Maintenance Window Walkthrough",
        "description": "Recorded walkthrough of maintenance procedures, safety checklist, and subsystem sign-off sequence.",
        "file_name": "cms_maintenance_walkthrough_2026_03_30.mp4",
        "mime_type": "video/mp4",
        "duration_seconds": 2890,
        "speaker": "Aisha Rahman",
        "event_name": "CMS Operations",
        "status": AssetStatus.READY,
        "visibility": AssetVisibility.PRIVATE,
    },
    {
        "title": "ALICE Data Quality Monitoring Review",
        "description": "Review meeting focusing on data quality flags and calibration drift findings for the last proton fill.",
        "file_name": "alice_dqm_review_fill_9876.mp4",
        "mime_type": "video/mp4",
        "duration_seconds": 2540,
        "speaker": "Nicolas Favre",
        "event_name": "ALICE DQM Review",
        "status": AssetStatus.READY,
        "visibility": AssetVisibility.PRIVATE,
    },
    {
        "title": "LHCb Reconstruction Pipeline Deep Dive",
        "description": "Architecture deep dive into reconstruction stages, latency budget, and failure recovery strategy.",
        "file_name": "lhcb_reco_pipeline_deep_dive.mp4",
        "mime_type": "video/mp4",
        "duration_seconds": 3660,
        "speaker": "Priya Menon",
        "event_name": "LHCb Software Forum",
        "status": AssetStatus.READY,
        "visibility": AssetVisibility.PRIVATE,
    },
    {
        "title": "CERN Open Data Outreach Interview",
        "description": "Interview recording about open-data publication practices and reproducibility guidelines.",
        "file_name": "cern_open_data_outreach_interview_2026.wav",
        "mime_type": "audio/wav",
        "duration_seconds": 1980,
        "speaker": "Jonas Mueller",
        "event_name": "Open Data Initiative",
        "status": AssetStatus.READY,
        "visibility": AssetVisibility.PUBLIC,
    },
    {
        "title": "Cryogenics System Incident Postmortem",
        "description": "Postmortem session covering timeline, root cause analysis, and preventive actions for cryo interruption.",
        "file_name": "cryo_incident_postmortem_2026_02_11.mp4",
        "mime_type": "video/mp4",
        "duration_seconds": 3415,
        "speaker": "Sven Johansson",
        "event_name": "Engineering Reliability Review",
        "status": AssetStatus.READY,
        "visibility": AssetVisibility.PRIVATE,
    },
    {
        "title": "Beam Instrumentation Calibration Workshop",
        "description": "Workshop module on calibration tooling, automation scripts, and quality control checks.",
        "file_name": "beam_instrumentation_calibration_workshop.mp4",
        "mime_type": "video/mp4",
        "duration_seconds": 3925,
        "speaker": "Camille Bernard",
        "event_name": "Instrumentation Workshop 2026",
        "status": AssetStatus.READY,
        "visibility": AssetVisibility.PRIVATE,
    },
    {
        "title": "Radiation Protection Annual Refresher",
        "description": "Annual refresher for on-site teams covering radiation zones, access policy, and incident protocol.",
        "file_name": "radiation_protection_refresher_2026.mp4",
        "mime_type": "video/mp4",
        "duration_seconds": 2755,
        "speaker": "Laura Bianchi",
        "event_name": "Safety Training Program",
        "status": AssetStatus.READY,
        "visibility": AssetVisibility.PRIVATE,
    },
    {
        "title": "Future Circular Collider Design Study Town Hall",
        "description": "Town hall recording discussing design milestones, stakeholder Q&A, and next planning cycle.",
        "file_name": "fcc_design_study_townhall_2026_01.mp4",
        "mime_type": "video/mp4",
        "duration_seconds": 4470,
        "speaker": "Prof. Daniel Weiss",
        "event_name": "FCC Design Study",
        "status": AssetStatus.READY,
        "visibility": AssetVisibility.PUBLIC,
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        existing_titles = {row[0] for row in db.query(Asset.title).all()}
        to_create = [Asset(**payload) for payload in SEED_ASSETS if payload["title"] not in existing_titles]

        if to_create:
            db.add_all(to_create)
            db.commit()

        print(f"Inserted {len(to_create)} assets. Total seed set: {len(SEED_ASSETS)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
