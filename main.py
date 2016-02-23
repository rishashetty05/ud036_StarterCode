import webapp2
import jinja2
import os

import re
import cgi

import urllib

from google.appengine.ext import db
from google.appengine.api import users


template_dir = os.path.join(os.path.dirname(__file__), "templates")
#template librabry is used to build complicated strings. In web applications
# most of the times these strings are HTML.Jinja is one such library bult into 
# Google app engine.
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                                extensions=['jinja2.ext.autoescape'],
                                autoescape=True)

class Greeting(db.Model):
    """Models an individual Guestbook entry with an author, content, and date."""
    author = db.StringProperty()
    topic_selected = db.StringProperty()

    content = db.StringProperty(multiline=True, indexed=False)
    date = db.DateTimeProperty(auto_now_add=True)

def _GuestbookKey(guestbook_name=None):
  """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
  return db.Key.from_path('Guestbook', guestbook_name or 'default_guestbook')

def escape_html(s):
    return cgi.escape(s, quote = True)

def valid_name(name):
    if  len(name)<20:
        p = r"[~\!@#\$%\^&\*\(\)_\+{}\":;'\[\]]"
        if re.search(p, name):
            return "invalid"
        else:
            return "valid"
    else:

        return "invalid"

def valid_id(email):
    if  len(email)<35:
        p = r"[@.]"
        if re.search(p, email):
            return "valid"
        else:
            return "invalid"
    else:
        return "invalid"

class Handler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
#this function in the Parent class Handler only outputs what ever data
#is being sent to it. Additional parameters *a & **kw is mentioned in case
# there are extra parameters to be passed on.
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class MainPage(Handler):
# Inherited class MainPage is derived to have properties of parent class
# Handler such as its write function is used to render the form as shown 
# belowtemplate_values ={}
    def write_form(self, nameerror="", emailerror="",name="",email=""):
        topics = ["1. Introduction to networks", "2. Servers", "3. Templates", "4.Databases"]
        
        template_values = {"nameerror":nameerror, 
                            "emailerror":emailerror,
                            "name": escape_html(name),
                            "email": escape_html(email),
                            "topics": topics,}
        self.render("form.html",**(template_values))


    def get(self):
        self.write_form()

    def post(self):
        user_name = self.request.get('name')
        user_id =self.request.get('email')

        name = valid_name(user_name)
        email= valid_id(user_id)

        if (name and email == "invalid"):
            self.write_form("Invalid name","Invalid email",user_name,user_id)
        elif (name == "invalid") :
            self.write_form("Invalid name","",user_name,user_id)
        elif (email == "invalid"):
            self.write_form("","Invalid email",user_name,user_id)
        else: 
            self.redirect("/thanks?name="+name+"&email="+email)       

class ThanksHandler(Handler):
    def get(self):
        guestbook_name = self.request.get('name')

        greetings_query = Greeting.all().ancestor(_GuestbookKey(guestbook_name)).order('-date')
        greetings = greetings_query.fetch(10)

        template_values = {'greetings': greetings,}
        self.render('content.html', **(template_values))           
    
    def post(self):
        guestbook_name = self.request.get('name')
        greeting = Greeting(parent=_GuestbookKey(guestbook_name))
        
        if users.get_current_user():
            greeting.author = users.get_current_user().email()
        
        greeting.topic_selected = self.request.get('topic')
        greeting.content = self.request.get('content')
        greeting.put()

        self.redirect('/thanks?'+ urllib.urlencode({'guestbook_name': guestbook_name}))

#trial is what you have launched on Google app engine an it works so far
app = webapp2.WSGIApplication([('/', MainPage),("/thanks", ThanksHandler),
                            ], debug=True)
