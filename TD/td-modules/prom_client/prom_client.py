# # pylint: disable=missing-docstring
# import pathlib
# import json
# import re
import time
import prometheus_client
from prometheus_client.core import CollectorRegistry
from prometheus_client import Counter, Gauge
from vvox_tdtools.base import BaseEXT
try:
    # import td
    from td import OP, parent, op, project  #pylint: disable=unused-import
    # TDJ = op.TDModules.mod.TDJSON
    # TDF = op.TDModules.mod.TDFunctions
except ModuleNotFoundError:
    from vvox_tdtools.td_mock import OP, parent, op, root, project  #pylint: disable=ungrouped-imports
    # from tdconfig import TDJSON as TDJ
    # from tdconfig import TDFunctions as TDF


class PromClientEXT(BaseEXT):
    def __init__(self, myop: OP) -> None:
        BaseEXT.__init__(self, myop)
        self.Registry = CollectorRegistry()
        self.Metrics = {}
        self.perform_metrics = {}
        self._required_project_metric_cols = [
            'name', 'type', 'description', 'value'
        ]
        self._project_name = self._getProjectName()
        self.InitCreateMetrics()
        self.CollectProjectMetrics()
        print('init')
        pass

    def _getProjectName(self):
        project_name = root.var('name')
        if project_name is None or project_name == '':
            project_name = project.name[:project.name.index('.')]
        return project_name

    def InitCreateMetrics(self):
        self.CreateMetric(
            'counter',
            'touchdesigner_test_counter_total',
            'test counter',
        )
        self.CreateMetric(
            'gauge', 'touchdesigner_perform_metric_collection_time_seconds',
            'The time it takes to collect the performance metrics.')
        self.createPerformMetrics()
        pass

    def createPerformMetrics(self):
        perform_op = self.Me.op('perform_metrics')
        description_table = self.Me.op('perform_metric_descriptions')

        for i in range(perform_op.numChans):
            chan = perform_op[i]
            name = chan.name
            description = 'None'
            try:
                description = description_table[name, 'description'].val
            except AttributeError:
                description = name
            perf_metric = self.CreateMetric('gauge', name, description)
            self.perform_metrics[name] = perf_metric
        # self.perform_metrics['msec'] = perf_metric
        pass

    def _checkProjectMetrics(self, project_metrics_dat):
        project_metric_cols = list(
            map(lambda c: c.val, project_metrics_dat.row(0)))
        dat_ok = False
        dat_ok = all(item in project_metric_cols
                     for item in self._required_project_metric_cols)
        self.print('dat_ok', dat_ok)
        return dat_ok

    def _createProjectMetric(self, metric_name, metrics_dat):
        self.print('_createProjectMetric', metric_name)
        metric_type = metrics_dat[metric_name, 'type'].val
        metric_description = metrics_dat[metric_name, 'description'].val
        dat_cols = list(map(lambda c: c.val, metrics_dat.row(0)))
        label_cols = [
            col_name for col_name in dat_cols
            if col_name not in self._required_project_metric_cols
        ]
        metric_labels = [
            label for label in label_cols
            if metrics_dat[metric_name, label].val != ''
        ]
        self.print('metric_labels', metric_labels)
        if len(metric_labels) == 0:
            labels_dict = None
        else:
            labels_dict = {
                label_name: metrics_dat[metric_name, label_name].val
                for label_name in metric_labels
            }
        self.print('labels_dict', labels_dict)
        self.CreateMetric(metric_type,
                          name=metric_name,
                          description=metric_description,
                          labels_dict=labels_dict)

        pass

    def _updateProjectMetric(self, metric_name, metrics_dat):
        self.print('_updateProjectMetric', metric_name)
        metric_name_cells = metrics_dat.findCells(metric_name, cols=['name'])
        metric_name_rows = [cell.row for cell in metric_name_cells]
        dat_cols = list(map(lambda c: c.val, metrics_dat.row(0)))
        label_cols = [
            col_name for col_name in dat_cols
            if col_name not in self._required_project_metric_cols
        ]
        for metric_row in metric_name_rows:
            # metric_type = metrics_dat[metric_row, 'type'].val
            metric_value = metrics_dat[metric_row, 'value'].val
            metric_labels = [
                label for label in label_cols
                if metrics_dat[metric_name, label].val != ''
            ]
            if len(metric_labels) == 0:
                labels_dict = None
            else:
                labels_dict = {
                    label_name: metrics_dat[metric_row, label_name].val
                    for label_name in metric_labels
                }
            self.print('metric_row', metric_row, 'metric_labels', labels_dict)
            self.SetMetric(name=metric_name,
                           value=metric_value,
                           labels_dict=labels_dict)

        pass

    def CollectProjectMetrics(self, dat=None): #pylint: disable=unused-argument
        self.print('CollectProjectMetrics')
        project_metrics_dat = self.Me.op('project_metrics')
        if project_metrics_dat.numRows <= 1:
            self.print('no project metrics dat')
            return
        dat_ok = self._checkProjectMetrics(project_metrics_dat)
        if not dat_ok:
            print(
                'project dat is missing required columns. required columns are name, type, description and value'
            )
            return
        project_metric_names = remove_list_dupes(
            list(map(lambda c: c.val,
                     project_metrics_dat.col('name')[1:])))
        self.print('project_metric_names', project_metric_names)
        for project_metric_name in project_metric_names:
            if project_metric_name == '':
                continue
            if not project_metric_name.startswith('touchdesigner_'):
                metric_name = f"touchdesigner_{project_metric_name}"
            else:
                metric_name = project_metric_name
            if metric_name not in self.Metrics:
                self._createProjectMetric(project_metric_name,
                                          project_metrics_dat)
            else:
                self._updateProjectMetric(project_metric_name,
                                          project_metrics_dat)

        pass

    def CollectPerformMetrics(self):
        start_time = time.time()
        perform_op = self.Me.op('perform_metrics')
        for i in range(perform_op.numChans):
            chan = perform_op[i]
            if chan.name in self.perform_metrics:
                self.perform_metrics[chan.name]
                self.SetMetric(name=chan.name, value=chan[0])

        delta_time = time.time() - start_time
        self.Metrics[
            'touchdesigner_perform_metric_collection_time_seconds'].labels(
                self._project_name).set(delta_time)
        pass

    def SetMetric(self, metric=None, name='', value=None, labels_dict=None):
        if metric is not None and (isinstance(metric, Gauge)
                                   or isinstance(metric, Counter)):
            target_metric = metric
        else:
            if not name.startswith('touchdesigner_'):
                name = f"touchdesigner_{name}"
            target_metric = self.Metrics.get(name, None)
            if target_metric is None:
                print('metric does not exist')
                return

            if isinstance(target_metric, Gauge):
                metric_type = 'gauge'
            elif isinstance(target_metric, Counter):
                metric_type = 'counter'
            else:
                print(f"metric: {name} is not a Gauge or Counter metric")
                return
        if labels_dict is None:
            labels_dict = {}

        labels_dict['project_instance'] = self._project_name
        if metric_type == 'gauge':
            target_metric.labels(**labels_dict).set(value)
        elif metric_type == 'counter':
            if value is None:
                target_metric.labels(**labels_dict).inc()
            else:
                target_metric.labels(**labels_dict).set(value)

        pass

    def CreateMetric(self,
                     metric_type,
                     name='',
                     description='',
                     callback=None,
                     labels_dict=None):
        # print(f"CreateMetric - metric_type{metric_type}, name: {name}, description: {description}")
        if name is None or name == '':
            print('metric must have a name')
            return
        if description is None or description == '':
            print(f"metric: {name} must have a description")
            description = 'Test description'
        if 'touchdesigner_' not in name:
            name = f"touchdesigner_{name}"

        labels = {'project_instance': self._project_name}
        label_names = ['project_instance']
        # print('label name', name, 'labels_dict', labels_dict)
        if labels_dict is not None:
            for label_name, label_val in labels_dict.items():
                label_names.append(label_name)
                labels[label_name] = label_val

        def setLabels(metric, label_names, labels_dict):
            metric_values = []
            for label_name in label_names:
                metric_values.append(labels_dict[label_name])
            # print('metric_values', metric_values)
            metric.labels(*metric_values)
            pass

        if metric_type == 'counter':
            self.Metrics[name] = Counter(name,
                                         description,
                                         label_names,
                                         registry=self.Registry)
            setLabels(self.Metrics[name], label_names, labels)
            return self.Metrics[name]
        elif metric_type == 'gauge':
            self.Metrics[name] = Gauge(name,
                                       description,
                                       label_names,
                                       registry=self.Registry)
            if callback is not None and callable(callback):
                self.Metrics[name].set_function(callback)
            setLabels(self.Metrics[name], label_names, labels)
            return self.Metrics[name]
        else:
            print(f"metric: {name} type must be 'counter' or 'gauge'")
            return
        pass

    def Inccounter(self):
        print('Inccounter')
        # self.Metrics['touchdesigner_test_counter_total'].inc()
        self.SetMetric(name='touchdesigner_test_counter_total')
        pass

    def GenerateResponse(self):
        res = []
        for v in self.Metrics.values():
            res.append(prometheus_client.generate_latest(v))
        text_response = ''
        for text in res:
            text_response = text_response + text.decode()
        return text_response

    def Printresponse(self):
        res = self.GenerateResponse()
        print('response', res)
        pass


def remove_list_dupes(dupe_list):
    return list(dict.fromkeys(dupe_list))
