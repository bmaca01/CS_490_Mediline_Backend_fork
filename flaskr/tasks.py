from datetime import datetime
from celery import shared_task
from flaskr.extensions import db
from flaskr.models import Prescription, PrescriptionMedication
from flaskr.struct import PrescriptionStatus

@shared_task(bind=True, ignore_result=False)
def send_rx(self,
            pharmacy_id: int|None=None, 
            patient_id: int|None=None, 
            doctor_id: int|None=None, 
            medications: list|None=None):
    # 1) create entry in prescription table
    #print(self.request.id)
    new_rx = Prescription(
        patient_id=patient_id,
        doctor_id=doctor_id,
        pharmacy_id=pharmacy_id,
        amount=0,
        status=PrescriptionStatus.UNPAID
    )
    db.session.add(new_rx)
    # Flush to get new prescription id
    try:
        db.session.flush()
    except Exception as e:
        raise e
    # 2) for each medication, create entry in rx-med table
    for med in medications:
        new_pt_rx_request = PrescriptionMedication(
            prescription_id=new_rx.prescription_id,
            medication_id=med['medication_id'],
            dosage=med['dosage'],
            medical_instructions=med['instructions'],
            taken_date=datetime.now(),
            duration=20
        )
        db.session.add(new_pt_rx_request)
        try:
            db.session.flush()
        except Exception as e:
            raise e
    try:
        db.session.commit()
    except Exception as e:
        raise e
    return self.request.id, {
        'prescription_id': new_rx.prescription_id,
        'patient_id': patient_id,
        'doctor_id': doctor_id,
        'pharmacy_id': pharmacy_id,
        'medications': medications
    }