from flaskr.extensions import db
from flaskr.struct import PrescriptionStatus

class MedicalRecord(db.Model):
    __tablename__ = 'medical_record'

    medical_record_id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.appointment_id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    appointment = db.relationship('Appointment', backref=db.backref('medical_records', lazy=True))
    
    def to_dict(self):
        result = {
            'medical_record_id': self.medical_record_id,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if self.appointment:
            appt = self.appointment
            appt_dict = {
                'appointment_id': appt.appointment_id,
                'doctor_id': appt.doctor_id,
                'patient_id': appt.patient_id,
                'doctor_name': f"{appt.doctor.first_name} {appt.doctor.last_name}" if appt.doctor else None,
                'patient_name': f"{appt.patient.first_name} {appt.patient.last_name}" if appt.patient else None,
            }
            result['appointment'] = appt_dict
        else:
            result['appointment'] = None
        return result

class Prescription(db.Model):
    __tablename__ = 'prescription'

    prescription_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.user_id', ondelete='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.user_id', ondelete='CASCADE'), nullable=False)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacy.user_id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(PrescriptionStatus), nullable=False, default=PrescriptionStatus.UNPAID)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    patient = db.relationship('Patient', backref=db.backref('prescriptions', lazy=True))
    doctor = db.relationship('Doctor', backref=db.backref('prescriptions', lazy=True))
    pharmacy = db.relationship('Pharmacy', backref=db.backref('prescriptions', lazy=True))

    def to_dict(self):
        result = {
            'prescription_id': self.prescription_id,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'amount': self.amount,
            'status': self.status.name,
            'pharmacy_id': self.pharmacy_id,
            'patient_name': None,
            'doctor_name': None,
            'pharmacy_name': None,
            'created_at': self.created_at.isoformat(),
        }
        if self.patient:
            result['patient_name'] = f"{self.patient.first_name} {self.patient.last_name}"
        if self.doctor:
            result['doctor_name'] = f"{self.doctor.first_name} {self.doctor.last_name}"
        if self.pharmacy:
            result['pharmacy_name'] = self.pharmacy.pharmacy_name

        return result

class PrescriptionMedication(db.Model):
    __tablename__ = 'prescription_medication'

    prescription_medication_id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescription.prescription_id'), nullable=False)
    medication_id = db.Column(db.Integer, db.ForeignKey('medication.medication_id'), nullable=False)
    dosage = db.Column(db.Integer, nullable=False)
    medical_instructions = db.Column(db.Text, nullable=False)
    taken_date = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False) # In days

    prescription = db.relationship('Prescription', backref=db.backref('prescription_medications', lazy=True))
    medication = db.relationship('Medication', backref=db.backref('prescription_medications', lazy=True))
    
    def to_dict(self):
        return {
            'prescription_medication_id': self.prescription_medication_id,
            'prescription_id': self.prescription_id,
            'medication_id': self.medication_id,
            'dosage': self.dosage,
            'medical_instructions': self.medical_instructions,
            'taken_date': self.taken_date.isoformat() if self.taken_date else None,
            'medication_name': self.medication.name if self.medication else None,
            'duration': self.duration
        }

class Medication(db.Model):
    __tablename__ = 'medication'

    medication_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            'medication_id': self.medication_id,
            'name': self.name,
            'description': self.description
        }

class Inventory(db.Model):
    __tablename__ = 'inventory'

    inventory_id = db.Column(db.Integer, primary_key=True)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacy.user_id'), nullable=False)
    medication_id = db.Column(db.Integer, db.ForeignKey('medication.medication_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    expiration_date = db.Column(db.DateTime, nullable=False)

    pharmacy = db.relationship('Pharmacy', backref=db.backref('inventories', lazy=True))
    medication = db.relationship('Medication', backref=db.backref('inventories', lazy=True))

    def to_dict(self):
        return {
            'inventory_id': self.inventory_id,
            'medication_id': self.medication_id,
            'quantity': self.quantity,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'medication_name': self.medication.name if self.medication else None
        }