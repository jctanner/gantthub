#!/usr/bin/env python

"""
# DATAFILE FORMAT
{
    task_id: <str>              # unique ID for the task
    task_name: <str>            # what will display in the UX
    start_date: <str>           # YYYY-MM-DD
    end_date: <str>             # YYYY-MM-DD
    duration: <int>             # number of days to complete
    percent_complete: <int>     # whole number 0-100
    dependencies: <str>         # a csv of taskids
    project: <bool>             # is this a project or not?
}
"""

import datetime
import glob
import json
import os
import tarfile


class GanttApi:

    tasks = None
    datadir = 'data'

    def __init__(self, datadir=None):
        if datadir:
            self.datadir = datadir
        self.load_data()

    def load_data(self):
        if not os.path.exists(self.datadir):
            os.makedirs(self.datadir)
        self.tasks = []
        dfs = glob.glob('%s/*.json' % self.datadir)
        for df in dfs:
            print('read %s' % df)
            with open(df, 'r') as f:
                self.tasks.append(json.loads(f.read()))
        print(self.tasks)

    def get_backup(self):
        ''' tar up the datadir and return a filepath '''
        bdir = '/tmp/backups'
        if not os.path.exists(bdir):
            os.makedirs(bdir)
        bfile = os.path.join(
            bdir,
            'gantt-backup-%s.tar.gz'% \
                datetime.datetime.now().isoformat()
        )
        bfile = bfile.replace(':', '-')

        jfiles = glob.glob('%s/*.json' % self.datadir)
        with tarfile.open(bfile, 'w:gz') as tar:
            for jfile in jfiles:
                tar.add(jfile)
        return bfile

    def get_project_name(self, projectid):
        project = self.get_project(projectid=projectid)
        return project['task_name']

    def get_projects(self):
        if not isinstance(self.tasks, list):
            return []
        projects = [x for x in self.tasks if x.get('project') == True]
        projects = sorted(projects, key=lambda x: x['task_name'])
        return projects

    def get_tasks(self, projectid=None, taskid=None):
        if not isinstance(self.tasks, list):
            return []

        if projectid and taskid:
            for task in self.tasks:
                if task.get('project_id') == projectid and task.get('task_id') == taskid:
                    return task

        if projectid:
            return [x for x in self.tasks if x.get('projectid') == projectid]

        if taskid:
            for task in self.tasks:
                if task['task_id'] == taskid:
                    return task

        if isinstance(self.tasks, list):
            return self.tasks[:]

        return []

    def get_task(self, taskid=None):
        for task in self.tasks:
            if task['task_id'] == taskid:
                return task
        return None

    def get_project(self, projectid=None):
        for task in self.tasks:
            if task.get('project') and task['task_id'] == projectid:
                return task

    def add_project(self, projectid=None, current_projectid=None, projectname=None, resource=None, trackerurl=None, startdate=None, enddate=None, duration=None, percentcomplete=None, dependencies=None, info=None):

        print('#############################')
        print('current_projectid: %s' % current_projectid)
        print('new_projectid: %s' % projectid)
        print('#############################')

        if current_projectid:
            # kill the old file
            fn = os.path.join(self.datadir, 'project_%s.json' % current_projectid)
            os.remove(fn)

            # fix all the other files
            tofix = glob.glob('%s/*.json' % self.datadir)
            for tf in tofix:
                with open(tf, 'r') as f:
                    jdata = json.loads(f.read())
                changed = False
                if jdata.get('projectid') == current_projectid:
                    jdata['projectid'] = projectid
                    changed = True
                _dependencies = jdata.get('dependencies', '').split(',')
                if current_projectid in _dependencies:
                    _dependencies.remove(current_projectid)
                    _dependencies.append(projectid)
                    jdata['dependencies'] = ','.join(_dependencies)
                    changed = True
                if changed:
                    os.remove(tf)
                    if jdata.get('project') == True:
                        nf = os.path.join(self.datadir, 'project_%s.json' % jdata['task_id'])
                    else:
                        nf = os.path.join(self.datadir, 'project_%s_task_%s.json' % (jdata['projectid'], jdata['task_id']))
                    with open(nf, 'w') as f:
                        f.write(json.dumps(jdata, indent=2, sort_keys=True))

        fn = os.path.join(self.datadir, 'project_%s.json' % projectid)
        with open(fn, 'w') as f:
            f.write(json.dumps({
                'project': True,
                'task_id': projectid,
                'task_name': projectname,
                'resource_group': resource or '',
                'tracker_url': trackerurl,
                'start_date': startdate,
                'end_date': enddate,
                'duration': duration,
                'percent_complete': percentcomplete or 0,
                'dependencies': dependencies,
                'info': info
            }))
        self.load_data()

    def delete_project(self, projectid=None):
        pfiles = glob.glob('%s/project_%s*' % (self.datadir, projectid))
        for pfile in pfiles:
            print('deleting %s' % pfile)
            os.remove(pfile)
        self.load_data()

    def add_task(self, projectid=None, taskid=None, current_taskid=None, taskname=None, resource=None, trackerurl=None, startdate=None, enddate=None, duration=None, percentcomplete=None, dependencies=None, info=None):

        # re-id a task ...
        if current_taskid:
            fn = os.path.join(self.datadir, 'project_%s_task_%s.json' % (projectid, current_taskid))
            os.remove(fn)

            # fix all the other files
            tofix = glob.glob('%s/project_*_task_*.json' % self.datadir)
            for tf in tofix:
                with open(tf, 'r') as f:
                    jdata = json.loads(f.read())
                if jdata.get('project') == True:
                    continue
                changed = False
                if jdata.get('task_id') == current_taskid:
                    jdata['task_id'] = taskid
                    changed = True
                _dependencies = jdata.get('dependencies', '').split(',')
                if current_taskid in _dependencies:
                    _dependencies.remove(current_taskid)
                    _dependencies.append(taskid)
                    jdata['dependencies'] = ','.join(_dependencies)
                    changed = True
                if changed:
                    os.remove(tf)
                    nf = os.path.join(self.datadir, 'project_%s_task_%s.json' % (jdata['projectid'], jdata['task_id']))
                    with open(nf, 'w') as f:
                        f.write(json.dumps(jdata, indent=2, sort_keys=True))

        fn = os.path.join(self.datadir, 'project_%s_task_%s.json' % (projectid, taskid))
        with open(fn, 'w') as f:
            f.write(json.dumps({
                'project': False,
                'projectid': projectid,
                'task_id': taskid,
                'task_name': taskname,
                'resource_group': resource or '',
                'tracker_url': trackerurl,
                'start_date': startdate,
                'end_date': enddate,
                'duration': duration,
                'percent_complete': percentcomplete or 0,
                'dependencies': dependencies,
                'info': info
            }))
        self.load_data()

    def delete_task(self, taskid=None):
        task = self.get_task(taskid=taskid)
        projectid = task['projectid']
        tfile = os.path.join(self.datadir, 'project_%s_task_%s.json' % (projectid, taskid))
        os.remove(tfile)
        self.load_data()
