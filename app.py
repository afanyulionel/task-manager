from flask import Flask, Blueprint, request
from flask_restx import Api, Resource, fields
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow 
from flask_jwt_extended import JWTManager
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)

# API v1
api_v1 = Blueprint('v1', __name__, url_prefix='/api/v1')
api = Api(api_v1, doc='/docs', title="Task Api", version="1.0.0", description="A task management api") 

user_model = api.model('Task', {
  'title': fields.String,
  'description': fields.String,
})
user_model_put = api.model('Task_put', {
  'title': fields.String,
  'description': fields.String(required=False),
})

user_model_get = api.model('Task_Get', {
  'id': fields.Integer,
  'title': fields.String,
  'description': fields.String,
  'date_created': fields.DateTime,
  'date_updated': fields.DateTime,
})


# Models
class Task(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(70), unique=True)
  description = db.Column(db.String(100)) 
  date_created = db.Column(db.DateTime)
  date_updated = db.Column(db.DateTime)

# Schemas
class TaskSchema(ma.Schema):
  class Meta:
    fields = ('id', 'title', 'description', 'date_created', 'date_updated')

task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)

with app.app_context():
  db.create_all()


# Resources 
@api.doc()
@api.route('/tasks')
class TaskList(Resource):

  @api.marshal_list_with(user_model_get)
  def get(self):
    '''List All Tasks'''
    tasks = Task.query.all()
    return tasks_schema.dump(tasks)

  @api.expect(user_model)
  def post(self):
    '''Create A Task'''
    task_json = request.get_json()
    title=task_json['title']
    date_created = datetime.now()
    try:
      description=task_json['description']
    except KeyError as e:
      description = "Default"
    # if description is None:
    #   description = "Default Description"
    new_task = Task(title=title, description=description, date_created=date_created, date_updated=date_created)
    db.session.add(new_task)
    db.session.commit()
    return task_schema.dump(new_task), 201

@api.doc(params={'id': 'Task Id'})  
@api.route('/tasks/<int:id>')
class TaskItem(Resource):

  @api.marshal_list_with(user_model_get)
  def get(self, id):
    '''Get A Task'''
    task = Task.query.get_or_404(id)
    return task_schema.dump(task)

  @api.expect(user_model_put)
  def put(self, id):
    '''Update A Task'''
    task = Task.query.get_or_404(id)
    task_json = request.get_json()
    try:
      task.title = task_json['title']
      try:
        task.description = task_json['description']
      except KeyError:
        pass
      task.date_updated = datetime.now()
    except KeyError as e:
      raise KeyError({"name": "Some keys were not parsed"})
    db.session.commit()
    return task_schema.dump(task)

  def delete(self, id):
    '''Delete A Task'''
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return '', 204

# Docs endpoint
@api_v1.route('/docs')
class Docs(Resource):

  def get(self):
    return api.__schema__

# Register blueprints
app.register_blueprint(api_v1)

if __name__ == '__main__':
  app.run(debug=True)
  api.init_app(app)