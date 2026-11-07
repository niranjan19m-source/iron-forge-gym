from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gym.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class WorkoutGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    exercises = db.relationship('Exercise', backref='group', lazy=True, cascade="all, delete-orphan")

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('workout_group.id'), nullable=False)
    logs = db.relationship('ProgressLog', backref='exercise', lazy=True, cascade="all, delete-orphan")

class ProgressLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercise.id'), nullable=False)

with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/groups', methods=['GET', 'POST'])
def handle_groups():
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        try:
            group = WorkoutGroup(name=name)
            db.session.add(group)
            db.session.commit()
            return jsonify({'id': group.id, 'name': group.name}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    groups = WorkoutGroup.query.all()
    return jsonify([{'id': g.id, 'name': g.name} for g in groups])

@app.route('/api/groups/<int:group_id>/exercises', methods=['GET', 'POST'])
def handle_exercises(group_id):
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        exercise = Exercise(name=name, group_id=group_id)
        db.session.add(exercise)
        db.session.commit()
        return jsonify({'id': exercise.id, 'name': exercise.name}), 201

    exercises = Exercise.query.filter_by(group_id=group_id).all()
    return jsonify([{'id': e.id, 'name': e.name} for e in exercises])

@app.route('/api/exercises/<int:exercise_id>/logs', methods=['GET', 'POST'])
def handle_logs(exercise_id):
    if request.method == 'POST':
        data = request.json
        weight = data.get('weight')
        reps = data.get('reps')
        if weight is None or reps is None:
            return jsonify({'error': 'Weight and reps are required'}), 400
        log = ProgressLog(weight=float(weight), reps=int(reps), exercise_id=exercise_id)
        db.session.add(log)
        db.session.commit()
        return jsonify({'id': log.id, 'weight': log.weight, 'reps': log.reps}), 201

    logs = ProgressLog.query.filter_by(exercise_id=exercise_id).order_by(ProgressLog.date.desc()).all()
    return jsonify([{'id': l.id, 'weight': l.weight, 'reps': l.reps, 'date': l.date.strftime('%Y-%m-%d %H:%M')} for l in logs])

@app.route('/api/groups/<int:group_id>', methods=['DELETE'])
def delete_group(group_id):
    group = WorkoutGroup.query.get_or_404(group_id)
    db.session.delete(group)
    db.session.commit()
    return jsonify({'result': 'deleted'})

@app.route('/api/exercises/<int:exercise_id>', methods=['DELETE'])
def delete_exercise(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    db.session.delete(exercise)
    db.session.commit()
    return jsonify({'result': 'deleted'})

if __name__ == '__main__':
    app.run(debug=True)
