#!/usr/bin/python
import unittest
from flask import Flask
from flask.ext.testing import TestCase
from flask import render_template



class MyTest(TestCase):

  def create_app(self):
     app = Flask(__name__)

     app.config['TESTING'] = True
     @app.route('/')
     def hello_world():
       return render_template('index.html')       
     return app

  def test_root_route(self):
    self.client.get('/')
    self.assert_template_used('index.html')

if __name__ == '__main__':
    unittest.main()
