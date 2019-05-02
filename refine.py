import urllib.error, urllib.parse, urllib.parse
import os.path
import time
import json
import requests

class Refine:
  def __init__(self, server='http://127.0.0.1:3333'):
    self.server = server
  
  def create_new_project(self, file_path, project_name):

    file_name = os.path.split(file_path)[-1]
    data = {'project-name' : project_name}
    files = {'project-file' : (file_name, open(file_path, 'rb'))}
      

    response = requests.post(self.server + '/command/core/create-project-from-upload', data=data, files=files)
    url_params = urllib.parse.parse_qs(urllib.parse.urlparse(response.request.url).query)

    if 'project' in url_params:
      id = url_params['project'][0]
      print('Project Created')
      return RefineProject(self.server, id, project_name)
    else:
      raise Exception('Project could not be created')
    return None

class RefineProject:
  def __init__(self, server, id, project_name):

    self.server = server
    self.id = id
    self.project_name = project_name
  
  def wait_until_idle(self, polling_delay=0.5):

    while True:
      response = requests.post(self.server + '/command/core/get-processes?project=' + self.id)
      response_json = json.loads(response.content)
      if 'processes' in response_json and len(response_json['processes']) > 0:
        time.sleep(polling_delay)
      else:
        return
  
  def apply_operations(self, file_path, wait=True):

    json_file = open(file_path)
    json_operations = json_file.read()
    
    data = {'operations' : json_operations}
    response = requests.post(self.server + '/command/core/apply-operations?project=' + self.id, data)
    response_json = json.loads(response.content)

    if response_json['code'] == 'error':
      raise Exception(response_json['message'])
    elif response_json['code'] == 'pending':
      if wait:
        self.wait_until_idle()
        return 'ok'
    
    return response_json['code'] 
  
  def export_rows(self, format='csv'):

    data = {
      'engine' : '{"facets":[],"mode":"row-based"}',
      'project' : self.id,
      'format' : format
    }
    response = requests.post(self.server + '/command/core/export-rows/' + self.project_name + '.' + format, data)
    return response.content
    
  def delete_project(self):

    data = {'project' : self.id}

    response = requests.post(self.server + '/command/core/delete-project', data)
    response_json = json.loads(response.content)
    if 'code' in response_json and response_json['code'] == 'ok':
      return 'Project Deleted'
    else:
      raise Exception('Project could not be deleted')

    return None




