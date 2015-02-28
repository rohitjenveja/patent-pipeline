#!/usr/bin/python

"""Object used for parsing US patent xml."""

import logging

import xml.etree.ElementTree as ET


class USPatent(object):
  
  def __init__(self, s3_location):
    # figure out how to make the s3 location accessible
    self.data = {}
    self.xml = ET.parse(s3_location)
  
    self.GatherData()
    self.AddData()

  def GatherData(self):
    root = self.xml.getroot()
    bd = root.find('us-bibliographic-data-grant')

    pr = bd.find('publication-reference')
    for node in pr.iter():
      self.data[node.tag] = node.text

    ar = bd.find('application-reference')
    for node in ar.iter():
      self.data[node.tag] = node.text

  def AddData(self):
    # perfom the SQL inserts     
    print self.data
