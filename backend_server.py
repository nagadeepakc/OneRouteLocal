#!/usr/local/bin/python2.7

# Use to get port # from Heroku environment
from os import environ

# DB STUFF
from flask.ext.sqlalchemy import SQLAlchemy

# JSON import
import json
from bson import json_util


# Flask import
from flask import Flask, flash, Response, jsonify, request, render_template


app = Flask(__name__)
app.secret_key = 'bc730ade0c837ba6c39e' # Random secret key

# DB STUFF

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://edmeeidsoanzkg:8oijr_O8B8_RjIk-fg46lEcBuu@ec2-23-21-55-25.compute-1.amazonaws.com:5432/d2h70ose55s4h0'


db = SQLAlchemy(app)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True)

    def __init__(self, name, email):
        self.name = name
        self.email = email

    def __repr__(self):
        return '<Name %r>' % self.name

db.create_all()







# Mongo import and connection to OneRoute database

# from pymongo import MongoClient

# The following is the MongoDB URI that we obtain from mLab
# mLab is our Heroku MongoDB provider

# mongo_user = "one_route_dev"
# mongo_pass = "oneroutedev"
# mongo_client = MongoClient('mongodb://' + mongo_user + ':' + mongo_pass + '@ds027145.mlab.com:27145/one_route')
# db = mongo_client.one_route

# Twilio import
from twilio.rest import TwilioTaskRouterClient, TwilioRestClient
from twilio.rest.exceptions import TwilioRestException

# Twilio account details
account_sid = "ACc9111e5c0efc0644b4e754bf2183c1c2"
auth_token  = "86f3177a99d46d4cb6237b106be7bd9c"
workspace_sid = "WSa521ebd8b208fe727465ceb9c92bfc52"
workflow_sid = "WW23312adca9ce4cf87cc3488c1b6dde5d"

# Get our TaskRouter object
task_router = TwilioTaskRouterClient(account_sid, auth_token)

#Twilio Voice Client
twilio_client = TwilioRestClient(account_sid, auth_token)

# DB STUFF

# Create our database model

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True)

    def __init__(self, name, email):
        self.name = name
        self.email = email

    def __repr__(self):
        return '<Name %r>' % self.name


# Define Flask routes
# =========== HTML Routes ===========
@app.route("/")
def root():
    return render_template('worker_login.html')


@app.route("/worker_dashboard.html")
def show_worker_dashboard():
    friendly_name = request.args.get('worker_name')
    if (friendly_name):
        return render_template('worker_dashboard.html')
    else:
        print "NOT A GOOD WORKER DASHBOARD REQUEST\n\n\n\n\n\n"
        flash('Permission denied: cannot access worker dashboard without logging in')
        return render_template('worker_login.html')


@app.route("/flash_invalid_login")
def flash_worker_login():
        flash('Permission denied: invalid username and password combination')
        return render_template('worker_login.html')


@app.route("/get_worker_details", methods=['GET', 'POST'])
def get_worker_details():
    username = request.args.get('user')
    password = request.args.get('pass')

    cursor_count = db.workers.find({'username':username,'password':password}).count()
    print "Worker query returned " + str(cursor_count) + " results.\n\n\n\n\n"

    responseDict = {}

    if cursor_count > 0:
        cursor = db.workers.find({'username':username,'password':password})
        for doc in cursor:
            json_doc = json.dumps(doc, default=json_util.default)
            json_dict = responseDict = json.loads(json_doc)
    else:
        responseDict["worker_sid"] = ""
        responseDict["worker_token"] = ""

    return jsonify(responseDict);


@app.route("/get_worker_tasks", methods=['GET', 'POST']) 
def get_worker_task_queues(): 
    worker_sid = request.args.get('worker_sid')
    worker = task_router.workers(workspace_sid).get(worker_sid)
    print worker.activity_sid
    print worker.activity_name
    responseDict = {}


    return jsonify(responseDict);


@app.route("/change_worker_state", methods=['GET', 'POST'])
def change_worker_state():
    activity_sid_map = {
        "Idle":"WA4a5d6980400c3748cc46d1e22493672c",
        "Busy":"WAac64dc68111c82fcaf8b78ec815afde8",
        "Reserved":"WA736c2c738b74abb7783e56de6c81ca2f",
        "Offline":"WA78c2554801eddb4b8c19aa0fb6279364"
    }
    json_dict = request.json

    if((json_dict["state"] in activity_sid_map) and (len(json_dict["WorkerSid"]) > 0)):
        activity_sid = activity_sid_map[json_dict["state"]]
        worker_sid = json_dict["WorkerSid"]
        print "Worker State: %s, WorkerSid = %s, activitySid = %s" % (json_dict["state"], worker_sid, activity_sid)
        worker = task_router.workers(workspace_sid).get(worker_sid)
        worker.update(ActivitySid=activity_sid)
        return Response("{Changed Worker State to  %s}", status=200, mimetype='application/json') % (json_dict["state"])
    else:
        print "Activity State was not found in the system, or WorkerSid does not exist in Taskrouter check Request Again"


@app.route("/get_taskqueue_list", methods=['GET', 'POST'])
def get_worker_reservation_list():
    json_dict = request.json
    task_assignment_map = {}
    if(len(json_dict["TaskQueueName"]) > 0):
        taskqueue_name = json_dict["TaskQueueName"]
        task_list = task_router.tasks(workspace_sid).list(TaskQueueName=taskqueue_name)
        for i in range(len(task_list)):
            print task_list[i].attributes
            task_assignment_map[i] = task_list[i].attributes

        return jsonify(task_assignment_map)

    else:
        print "TaskQueue Name is invalid"


@app.route("/make_call", methods=['POST'])
def make_call():
    json_dict = request.json
    to_number = json_dict["to"]
    from_number = json_dict["from"]
    call = client.calls.create(url="http://demo.twilio.com/docs/voice.xml",to=to_number,from_=from_number)
    print(call.sid)


# =========== Twilio Routes ===========
@app.route("/event_callback", methods=['GET','POST'])
def event_callback():
    """Respond to events"""
    form_dict = request.form

    #TODO-Make Outgoing call to twilio number that mimics our flow

    #Switch on EventType for Task Events
    if(form_dict["EventType"] == "task.created"):
        task_dict = {"task_sid":form_dict["TaskSid"], "task_attributes":form_dict["TaskAttributes"], "task_age":form_dict["TaskAge"], "task_assigment_status":form_dict["TaskAssignmentStatus"], "task_reason":"None" }
        db.tasks.insert(task_dict)
        log_message = "Task Sid: %s, Task Attributes: %s, Task Age: %s, Task Status: %s" %(form_dict["TaskSid"],form_dict["TaskAttributes"],form_dict["TaskAge"],form_dict["TaskAssignmentStatus"])
        print "" %(form_dict["TaskSid"])
        print "Task Attributes: %s" % (form_dict["TaskAttributes"])
        print "Task Age: %s" %(form_dict["TaskAge"])
        print "Task Status: %s" %(form_dict["TaskAssignmentStatus"])
        print "Task Creation"
        logger.info()

    elif(form_dict["EventType"] == "task.cancelled"):
        #TODO-Find the task and update it to cancelled and give the reason why it was cancelled
        task_cursor = db.tasks.update_on({"task_sid": form_dict["TaskSid"]}, {"task_assignment_status": form_dict["TaskAssignmentStatus"], "task_reason": form_dict["TaskCancelledReason"]})
        print "Task Sid: %s" %(form_dict["TaskSid"])
        print "Task Attributes: %s" % (form_dict["TaskAttributes"])
        print "Task Age: %s" %(form_dict["TaskAge"])
        print "Task Status: %s" %(form_dict["TaskAssignmentStatus"])
        print "Task Cancelled"

    elif(form_dict["EventType"] == "task.completed"):
        #TODO-Find the task in Mongo and update to Completed
        task_cursor = db.tasks.update_on({"task_sid": form_dict["TaskSid"]}, {"task_assignment_status": form_dict["TaskAssignmentStatus"], "task_reason": form_dict["TaskCompletedReason"]})
        print "Task Sid: %s" %(form_dict["TaskSid"])
        print "Task Attributes: %s" % (form_dict["TaskAttributes"])
        print "Task Age: %s" %(form_dict["TaskAge"])
        print "Task Status: %s" %(form_dict["TaskAssignmentStatus"])
        print "Task Completed"

    elif(form_dict["EventType"] == "task.updated"):
        #task_cursor = db.tasks.update_on({"task_sid": form_dict["TaskSid"]}, {"task_assignment_status": form_dict["TaskAssignmentStatus"], "task_reason": "None")
        return
    elif(form_dict["EventType"] == "task.deleted"):
        #TODO-Find task and update the deletion
        db.tasks.update_on({"task_sid": form_dict["TaskSid"]}, {"task_assignment_status": form_dict["TaskAssignmentStatus"], "task_reason": form_dict["TaskDeletedReason"]})
        print "Task Sid: %s" %(form_dict["TaskSid"])
        print "Task Attributes: %s" % (form_dict["TaskAttributes"])
        print "Task Age: %s" %(form_dict["TaskAge"])
        print "Task Status: %s" %(form_dict["TaskAssignmentStatus"])
        print "Task Deleted"

    #Switch on EventType for Worker Event
    elif(form_dict["EventType"] == "worker.activity.update"):
        print "Worker activity Update"
    elif(form_dict["EventType"] == "worker.attributes.update"):
        print "Worker Attributes Update"

    #Switch on EventType for Reservation Events
    elif(form_dict["EventType"] == "reservation.created"):
        print "Reservation is Created"

    elif(form_dict["EventType"] == "reservation.accepted"):
        #TODO-Push accepted reservation to the corresponding worker with the TaskSID
        print "Making a call to a phone number"
        print "\nReservation is accepted"
        task_sid = form_dict["TaskSid"]
        task = task_router.tasks(workspace_sid).get(task_sid)
        print task.attributes
        #call = voice_client.calls.create(url="http://demo.twilio.com/docs/voice.xml", to=task.attributes["phone_number"], from_="+14082146768")
        #print(call.sid)

    elif(form_dict["EventType"] == "reservation.rejected"):
        print "Reservation is Rejected"
    elif(form_dict["EventType"] == "reservation.timeout"):
        print "Reservation is timed out"
    elif(form_dict["EventType"] == "reservation.cancelled"):
        print "Reservation is Cancelled"
    elif(form_dict["EventType"] == "reservation.rescinded"):
        print "Reservation is Rescinded"

    #Switch on EventType for TaskQueue Events
    elif(form_dict["EventType"] == "task-queue.entered"):
        print "Task entered TaskQueue"
        taskqueue_sid = form_dict["TaskQueueSid"]
        #TODO-Update Corresponding worker dashboard with the TaskQueue
        #statistics = task_router.task_queues(workspace_sid).get(taskqueue_sid).statistics.get()
        print form_dict

    elif(form_dict["EventType"] == "task-queue.timeout"):
        print "Task timed out in this TaskQueue"
        taskqueue_sid = form_dict["TaskQueueSid"]
        print form_dict

    elif(form_dict["EventType"] == "task-queue.moved"):
        #TODO-Update Corresponding Workers Dashboards based on the Movement
        print "Task moved into a different TaskQueue"
        taskqueue_sid = form_dict["TaskQueueSid"]
        print form_dict

    #Switch on EventType for Workflow Events
    elif(form_dict["EventType"] == "workflow.timeout"):
        print "Task has timed out in this workflow"
    elif(form_dict["EventType"] == "workflow.entered"):
        print "Task has entered into this workflow"


    return Response("{}", status=200, mimetype='application/json')


@app.route("/assignment_callback", methods=['GET','POST'])
def assignment_callback():
    """Respond to assignment callbacks with empty 200 response"""
    print "Accepted task...\n\n"
    print request.form
    return jsonify({"instruction":"accept"})


@app.route("/create_task", methods=['GET', 'POST'])
def create_task():
    """Create a task with a given list of attributes"""

    task = task_router.tasks(workspace_sid).create(
        workflow_sid=workflow_sid,
        attributes=request.data
        )

    return jsonify({"task_sid":task.sid})


if __name__ == "__main__":
    port = int(environ.get('PORT', 5000)) # Get port number from Heroku environment (assigned automatically)
    app.run(debug=True, host='0.0.0.0', port=port)
