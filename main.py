#!/usr/bin/env python
import os
import jinja2
import webapp2
from models import Message


template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=False)


class BaseHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        return self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        return self.write(self.render_str(template, **kw))

    def render_template(self, view_filename, params=None):
        if not params:
            params = {}
        template = jinja_env.get_template(view_filename)
        return self.response.out.write(template.render(params))


class MainHandler(BaseHandler):
    def get(self):
        return self.render_template("main.html")

class AdminHandler(BaseHandler):
    def get(self):
        messages = Message.query(Message.deleted == True).fetch()
        params = {"messages": messages}

        return self.render_template("admin.html", params=params)

class RestoreHandler(BaseHandler):
    def get(self, message_id):
        message = Message.get_by_id(int(message_id))
        params = {"message": message}

        return self.render_template("restore.html", params=params)

    def post(self, message_id):
        message = Message.get_by_id(int(message_id))
        message.deleted = False
        message.put()

        return self.redirect_to("admin-menu")

class DeletePermanentlyHandler(BaseHandler):
    def get(self, message_id):
        message = Message.get_by_id(int(message_id))
        params = {"message": message}

        return self.render_template("real_delete.html", params=params)

    def post(self, message_id):
        message = Message.get_by_id(int(message_id))
        message.key.delete()

        return self.redirect_to("admin-menu")

class GuestbookHandler(BaseHandler):
    def get(self):
        messages = Message.query(Message.deleted == False).fetch()
        params = {"messages": messages}

        return self.render_template("guestbook.html", params=params)

    def post(self):
        author = self.request.get("name")
        email = self.request.get("email")
        message = self.request.get("message")

        if not author:
            author = "Anonymous"

        if "<script>" in message:
            return self.write("Your activities will be reported to the authorities")

        msg_object = Message(author_name=author, email=email, message=message)
        msg_object.put()

        return self.redirect_to("guestbook-site")

class MessageHandler(BaseHandler):
    def get(self, id):
        temp_message = Message.get_by_id(int(id))
        params = {"message": temp_message}

        return self.render_template("message.html", params=params)

class EditMessageHandler(BaseHandler):
    def get(self, id):
        temp_message = Message.get_by_id(int(id))
        params = {"message": temp_message}

        return self.render_template("edit_message.html", params=params)
    def post(self, id):
        edit_message = self.request.get("new_message")
        temp_message = Message.get_by_id(int(id))
        temp_message.message = edit_message
        temp_message.put()

        return self.redirect_to("guestbook-site")

class DeleteMessageHandler(BaseHandler):
    def get(self, id):
        params = {"message_id": id}

        return self.render_template("delete.html", params=params)
    def post(self, id):
        temp_message = Message.get_by_id(int(id))
        temp_message.deleted = True
        temp_message.put()

        return self.redirect_to("guestbook-site")


app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler),
    webapp2.Route('/guestbook', GuestbookHandler, name="guestbook-site"),
    webapp2.Route('/message/<id:\d+>', MessageHandler),
    webapp2.Route('/message/<id:\d+>/edit', EditMessageHandler),
    webapp2.Route('/message/<id:\d+>/delete', DeleteMessageHandler),
    webapp2.Route('/deleted', AdminHandler, name="admin-menu"),
    webapp2.Route('/message/<message_id:\d+>/restore', RestoreHandler),
    webapp2.Route('/message/<message_id:\d+>/delete-permanently', DeletePermanentlyHandler),
], debug=True)
