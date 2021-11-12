#!/usr/bin/env python

"""
Columbia's COMS W4111.003 Introduction to Databases
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
import re

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

l = ['Band', 'Company', 'Singer', 'Song', 'ThemeSong', 'Movie', 'Album']
dict_r = {}
for t1 in l:
    dict_r[t1] = {}
    for t2 in l:
        if t2==t1:
            continue
        else:
            dict_r[t1][t2] = None
dict_r['Band']['Company'] = 'BelongTo'
dict_r['Band']['Singer'] = 'PartOf'
dict_r['Band']['Song'] = 'SingAsBand'
dict_r['Company']['Band'] = 'BelongTo'
dict_r['Company']['Singer'] = 'EmployeeOf'
dict_r['Company']['Song'] = 'Own'
dict_r['Singer']['Band'] = 'PartOf'
dict_r['Singer']['Company'] = 'EmployeeOf'
dict_r['Singer']['Album'] = 'Release'
dict_r['Singer']['Song'] = 'Sings'
dict_r['Song']['Band'] = 'SingAsBand'
dict_r['Song']['Company'] = 'Own'
dict_r['Song']['Singer'] = 'Sings'
dict_r['Song']['Album'] = 'Contains'
dict_r['Song']['ThemeSong'] = 'ISA'
dict_r['ThemeSong']['Song'] = 'ISA'
dict_r['ThemeSong']['Movie'] = 'Use'
dict_r['Movie']['ThemeSong'] = 'Use'
dict_r['Album']['Song'] = 'Contains'
dict_r['Album']['Singer'] = 'Release'

dict_name = {}
for t in l:
    if t == 'Song':
        dict_name[t] = 'name'
    else:
        dict_name[t] = t[0].lower() + 'name'

dict_id = {}
for t in l:
    if t == 'Song':
        dict_id[t] = 'id'
    else:
        dict_id[t] = t[0].lower() + 'id'
        



DATABASEURI = "postgresql://zg2409:mg_2021@35.196.73.133/proj1part2"


engine = create_engine(DATABASEURI)


@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  try:
    g.conn.close()
  except Exception as e:
    pass


@app.route('/')
def index():
  cursor = g.conn.execute("SELECT sname FROM Singer")
  names = []
  for result in cursor:
    names.append(result['sname'])  # can also be accessed using result[0]
  cursor.close()
  context = dict(data = names)

  return render_template("index_new.html", **context)


@app.route('/another')
def another():
  return render_template("another.html")
  
@app.route('/invalid')
def invalid():
  return render_template("invalid.html")

    
@app.route('/results', methods=['POST'])
def search():
    text = request.form['input']
    input_type = request.form['input_type']
    search_type = request.form['search_type']
    
    if "," in text or "\"" in text or "=" in text or "+" in text or "-" in text:
        return redirect('/invalid')
    
    if len(input_type) == 0 or len(search_type) == 0:
        return redirect('/another')
    elif len(text) == 0:
        com = "SELECT * FROM {input_type}".format(input_type=input_type)
    elif input_type == search_type:
        com = "SELECT * FROM {input_type} WHERE {input_type}.{name}='{st}'".format(input_type=input_type, name=dict_name[input_type], st=text)
    else:
        if dict_r[input_type][search_type] is None:
            return redirect('/another')
        relationship_table = dict_r[input_type][search_type]
        if relationship_table != 'ISA':
            com = "SELECT {search_type}.{search_type_name} FROM {search_type} where {search_type}.{search_type_id} in (SELECT {table}.{search_type_id} FROM {input_type}, {table} WHERE {input_type}.{name} = '{st}' AND {input_type}.{id} = {table}.{id})".format(table=relationship_table,input_type=input_type,
                                                                                            name=dict_name[input_type], 
                                                                                            search_type_name = dict_name[search_type],
                                                                                            id=dict_id[input_type],
                                                                                            search_type_id = dict_id[search_type],
                                                                                            st=text,
                                                                                            search_type=search_type)
        else:
            com = "SELECT {search_type}.{search_type_name} FROM {search_type},{input_type} WHERE {search_type}.{search_type_id} = {input_type}.{input_type_id}".format(search_type = search_type, search_type_name = dict_name[search_type], search_type_id = dict_id[search_type], input_type = input_type, input_type_id = dict_id[input_type])
        

    cursor = g.conn.execute(com)
    r = []
    for result in cursor:
        r.append(result) 
    cursor.close()
    
    if len(r) == 0:
        context = dict(data = ["Nothing to be found!"])
    else:
        context = dict(data = r)
    return render_template("results.html", **context)


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
