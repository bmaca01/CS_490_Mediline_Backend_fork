from datetime import datetime, timedelta
from sqlalchemy import func

from celery.result import AsyncResult

from flaskr.models import Prescription, Patient, Pharmacy
from flaskr.extensions import db
from flaskr.tasks import send_rx


def get_all_pharmacy_patients(pharmacy_id, new_request_time=datetime.now() - timedelta(hours=24)):
    rows = (
        db.session.query(
            Patient.user_id,
            Patient.first_name,
            Patient.last_name,
            func.max(Prescription.created_at).label("last_prescribed")
        ).join(Prescription, Prescription.patient_id == Patient.user_id)
        .filter(Prescription.pharmacy_id == pharmacy_id)
        .group_by(Patient.user_id, Patient.first_name, Patient.last_name)
        .all()
    )

    new_patients = []
    other_patients = []
    for id, first_name, last_name, created_at in rows:
        obj = {
            'patient_id':   id,
            'patient_name': f"{first_name} {last_name}"
        }
        if created_at >= new_request_time:
            new_patients.append(obj)
        else:
            other_patients.append(obj)

    return {
        'new_patients':   new_patients,
        'other_patients': other_patients
    }

def add_pt_rx(pharmacy_id, patient_id, doctor_id, medications):
    # TODO: detect duplicates
    try:
        res: AsyncResult = send_rx.apply_async(args=[pharmacy_id, patient_id, doctor_id, medications])
    except Exception as e:
        raise e
    return res.status

def get_pharmacy_info(pharmacy_id):
    pharmacy = Pharmacy.query.filter_by(user_id=pharmacy_id).first()
    if not pharmacy:
        return None

    return pharmacy.to_dict()
