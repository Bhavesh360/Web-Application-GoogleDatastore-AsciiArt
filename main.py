#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import webapp2
import jinja2 
import urllib2
from xml.dom import minidom
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True) 

GMAPS_URL = "http://maps.googleapis.com/maps/api/staticmap?size=380x263&sensor=false&"

def gmaps_img(points):
    ###Your code here
    makers= "&".join( "markers=%s,%s" % (point.lat, point.lon) for point in points)
    return GMAPS_URL+makers+"&key=AIzaSyAlaqc-GsZCdyLT5RH2CekTB7ImTjkyg_Y"  




IP_URL = "http://freegeoip.net/xml/"
def getcoords(ip):
    # ip = "4.2.2.2"
    # ip = "192.30.253.113"
    url = IP_URL+ip
    content = None
    try:
        content = urllib2.urlopen(url)
        content = content.read()
    except URLError:
        return

    if content:
        d = minidom.parseString(content)
        if d.getElementsByTagName("Latitude") and d.getElementsByTagName("Latitude")[0].childNodes[0].nodeValue and d.getElementsByTagName("Longitude")[0].childNodes[0].nodeValue:
            lat= d.getElementsByTagName("Latitude")[0].childNodes[0].nodeValue
            lon= d.getElementsByTagName("Longitude")[0].childNodes[0].nodeValue
            return db.GeoPt(lat, lon) 

        #parse the xml and find the coordinates. 

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class Art(db.Model): #creating an entity(columns of table) by creating a class Art that inherits from db.Model-app enigne datastore
    title = db.StringProperty(required = True)#Property = particular type. And then add constraint required = True that means if we try to make an instance of art without title we would get an exception. 
    art = db.TextProperty(required= True)
    created = db.DateTimeProperty(auto_now_add = True) # auto_now_add basically adds the date automatically when you create the instance. 
    coords = db.GeoPtProperty() #again app engine documentation. not required cause we would have it for future posts since we do not want the app to break. 

class MainHandler(Handler):
    def render_front(self, title = "", art= "", error = ""):
        arts= db.GqlQuery("SELECT * FROM Art ORDER BY created DESC")
        



        #prevent the running of query multiple times:
        arts = list(arts)
    # We want to render the map with the location of the art on the front page
    # find which arts have coords:
    #display image url
    # points =[]
    # for a in arts:
    #     if arts.coords:
    #         points.append(a.coords)

        points = filter(None, (a.coords for a in arts)) ## this is a slightly shorter version of the code above. if not none in then return. 
        # self.write(repr(points))

        #if we have any arts coords, make image url
        img_url = None
        if points:
            img_url = gmaps_img(points)

        print img_url
        #display the image url
        self.render("front.html", title = title, art = art , error = error, arts = arts, img_url = img_url)



    def get(self):
        # self.render_front()
        # self.write(repr(getcoords(self.request.remote_addr))) # repr is used to print python object so that the angle brackets are handled properly. request.remote_addr is used to fetch the IP address, more info on remote_addr can be found in google app engines docs. 
        return self.render_front()

    def post(self):
        title= self.request.get("title")
        art = self.request.get("art")

        if title and art:
            a = Art(title = title, art = art) # create a new instance of art
            #lookup the user's coordinates from their IP
            coords = getcoords(self.request.remote_addr)
            #if we have coordinated, add them to the art
            if coords:
                a.coords = coords


            a.put() #store the instance in the database.
            self.redirect('/')

        else:
            error = "we need both a title and some artwork!"
            self.render_front(title, art, error)

app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)
