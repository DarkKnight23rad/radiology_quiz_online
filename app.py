from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
import eventlet

eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

HOST_PASSWORD = "radiologyadmin"
TIME_LIMIT = 15  # секунд

questions = [
    {"text": "Какое излучение используется при КТ?", "options": ["Рентгеновское", "Инфракрасное", "Ультрафиолетовое"], "correct": 0},
    {"text": "Что изучает маммография?", "options": ["Молочные железы", "Предстательную железу", "Щитовидную железу"], "correct": 0},
    {"text": "Какая эхогенность у структур высокой плотности?", "options": ["Гипоэхогенная", "Изоэхогенная", "Гиперэхогенная"], "correct": 2},
    {"text": "В каком сегменте легкого частая локализация туберкулеза?", "options": ["S7", "S9", "S6"], "correct": 2},
    {"text": "Как называется заращение перелома соединительной тканью после травмы?", "options": ["мозоль", "костная мозоль", "зарастание"], "correct": 1}
]

players = {}
current_question = -1

@app.route('/')
def index():
    return redirect('/join')

@app.route('/join')
def join():
    return render_template('join.html')

@app.route('/quiz/<username>')
def quiz(username):
    return render_template('quiz.html', username=username)

@app.route('/host')
def host():
    return render_template('host.html')

@app.route('/results')
def results():
    sorted_players = sorted(players.items(), key=lambda x: x[1]["score"], reverse=True)
    return render_template('results.html', results=sorted_players)

@socketio.on('join')
def handle_join(data):
    name = data['username']
    if name not in players:
        players[name] = {"score": 0, "answers": []}
    emit('joined', {"success": True})

@socketio.on('get_question')
def send_question(data):
    global current_question
    if 0 <= current_question < len(questions):
        q = questions[current_question]
        emit('question', {
            "index": current_question + 1,
            "total": len(questions),
            "text": q["text"],
            "options": q["options"],
            "time": TIME_LIMIT
        })
    else:
        emit('end', {"message": "Викторина завершена!"})

@socketio.on('answer')
def handle_answer(data):
    user = data['username']
    selected = data['answer']
    q = questions[current_question]
    if user in players:
        if selected == q['correct']:
            players[user]['score'] += 1
            players[user]['answers'].append((q['text'], True))
        else:
            players[user]['answers'].append((q['text'], False))

@socketio.on('next_question')
def handle_next():
    global current_question
    current_question += 1
    if current_question < len(questions):
        emit('new_question', broadcast=True)
    else:
        emit('show_results', broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
