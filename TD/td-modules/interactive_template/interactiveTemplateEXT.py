# pylint: disable=missing-docstring
import pathlib
import json
import re
from vvox_tdtools.base import BaseEXT
try:
    # import td
    from td import OP, parent, op, containerCOMP
    TDJ = op.TDModules.mod.TDJSON
    TDF = op.TDModules.mod.TDFunctions
except ModuleNotFoundError:
    from vvox_tdtools.td_mock import OP, parent, op, ParMode, root, containerCOMP, tdu  #pylint: disable=ungrouped-imports
    from tdconfig import TDJSON as TDJ
    from tdconfig import TDFunctions as TDF


class InteractiveSceneEXT(BaseEXT):
    def __init__(self, myop: OP) -> None:
        BaseEXT.__init__(self, myop)
        print('begin init')
        self.Scene_name = self.name
        self._tox_folder_load = False
        self._video_folder_load = False
        self._bind_par_load = False
        self.Num_scene_changes = self.Me.fetch('num_scene_changes', 0, storeDefault=True)
        self._initialized = False
        self.Scenes = []
        self._setSceneName()
        self._setSceneVariablePars()
        self.Me.par.Scene.menuSource = "op.TDModules.mod.TDFunctions.parMenu(op('./init_menu').col('name')[1:] if op('./init_menu') else [], menuLabels=op('./init_menu').col('label')[1:] if op('./init_menu') else [])"
        self.Current_scene = self.Me.par.Currentscene.val
        self.Next_scene = self.Me.par.Nextscene.val
        self.Selected_scene = self.Me.par.Selectedscene.val

        if self.Me.name != 'interactive_template':
            self.Me.tags.add('SCENEGROUP')
            self.Me.tags.add('WEBUI')

        self.SetFolder()
        self._setSceneVariablePars()

        self.UI_page = self._getUIPage(self.Me)
        self._setupParameters()
        self._initSceneStatePars()

        self.print(f'__init__ {self.Scene_name}')
        pass

    def _setSceneVariablePars(self):
        par_names = ['Currentscene', 'Nextscene', 'Selectedscene']
        prop_names = ['Current_scene', 'Next_scene', 'Selected_scene']

        scene_names = self._getSceneNames()
        self.print(f'_setSceneVariablePars - scene_names: {scene_names}')
        for idx, par_name in enumerate(par_names):
            par = self.Me.par[par_name]
            par.menuNames = scene_names
            par.menuLabels = scene_names

            prop_name = prop_names[idx]
            if getattr(self, prop_name).isdigit():
                setattr(self, prop_name, par.eval())

        pass

    def _getSceneNames(self):
        base_video_names = list(map(lambda c: format_name(c.val), self.Me.op('folder_video').col('basename')[1:]))
        base_tox_names = list(map(lambda c: format_name(c.val), self.Me.op('folder_tox').col('basename')[1:]))
        scene_names = base_video_names + base_tox_names
        self.print(f'_getSceneNames: {scene_names}')
        return scene_names


    def Setuppars(self):
        self._setupParameters()
        self.Current_scene = self.Me.par.Currentscene.val
        self.Next_scene = self.Me.par.Nextscene.val
        self.Selected_scene = self.Me.par.Selectedscene.val
        self._initSceneStatePars()
        pass

    def _initSceneStatePars(self):
        self.print(f'Next_scene {self.Next_scene}')
        try:
            self.Me.op(self.Next_scene).par.Selected.val = True
            self.Me.op(self.Next_scene).par.Visible.val = True
            self.Me.op(self.Next_scene).par.Cuein.val = False
            self.Me.op(self.Next_scene).par.Cueout.val = False
        except Exception as e:
            self.print(f'Next_scene not defined? Next_scene: {self.Next_scene}, Error: {e}')
        # scene_names = self.Me.par.Scene.menuNames.copy()
        scene_names = [scene_op.name for scene_op in self.Me.findChildren(tags=['SCENE'])]
        if self.Next_scene in scene_names:
            scene_names.remove(self.Next_scene)
        scene_ops = [self.Me.op(scene_name) for scene_name in scene_names]
        for scene_op in scene_ops:
            try:
                for par in TDF.getCustomPage(scene_op, 'State').pars:
                    par.val = False
            except AttributeError as e:
                parent.view.Logger.error(f'could not set state pars on scenes in: {self.Scene_name}. Error: {e}')
        pass

    def _setSceneName(self) -> str:
        par_scene_name = self.Me.name
        if self.Me.par['Scenename']:
            scene_name_par = self.Me.par['Scenename']
            if scene_name_par.eval() != '':
                par_scene_name = scene_name_par.eval()
                self.Scene_name = par_scene_name
        pass

    def _setupParameters(self) -> None:
        self.print('_setupParameters')
        self._addPars()
        self._bind_par_load = True
        self._init()
        pass

    def _addPars(self):
        self.print('_addPars')
        self._addDefaultPars()
        menu_names = "op('./init_menu').col('name')[1:] if op('./init_menu') else []"
        menu_labels = "op('./init_menu').col('label')[1:] if op('./init_menu') else []"
        self.Me.par.Scene.menuSource = f"op.TDModules.mod.TDFunctions.parMenu({menu_names}, menuLabels={menu_labels})"
        pass

    def _addDefaultPars(self):
        default_pars = TDJ.datToJSON(self.Me.op('defaultPars'))
        TDJ.addParametersFromJSONDict(self.Me, default_pars, replace=True)
        pass


    def _setToxFolder(self):
        self.print('_setToxFolder')
        root_path = pathlib.Path(root.var('assets_path'))
        scene_path = root_path / 'tox' / self.Scene_name
        try:
            folder_dat = self.Me.op('folder_tox')
            folder_dat.par.rootfolder.val = str(pathlib.PurePosixPath(scene_path))
            self._onToxFileChange(folder_dat)
        except AttributeError:
            print('could not find folder_tox dat in scene', self.Scene_name)
        pass

    def _setVideoFolder(self):
        self.print('_setVideoFolder')
        root_path = pathlib.Path(root.var('assets_path'))
        scene_path = root_path / 'video' / self.Scene_name
        try:
            folder_dat = self.Me.op('folder_video')
            folder_dat.par.rootfolder.val = str(pathlib.PurePosixPath(scene_path))
            self._onVideoFileChange(folder_dat)
        except AttributeError as e:
            print('could not find folder_video dat in scene', self.Scene_name, 'Error:', e)
        pass

    def SetFolder(self):
        self.print('SetFolder')
        self._setToxFolder()
        self._setVideoFolder()
        pass

    def _getUIPage(self, target_op: OP):
        return TDF.getCustomPage(target_op, 'UI')

    def _init(self):
        if not self._tox_folder_load:
            self.print('init attempt before folder load')
            return
        if not self._video_folder_load:
            self.print('init attempt before folder load')
            return
        if not self._bind_par_load:
            self.print('init attempt before Parameter load')
            return
        if self._initialized:
            self.print('already initialized')
            return
        scene_names = self._getSceneNames()
        if len(scene_names) == 0:
            self.print(f'canceling init because no scene names yet: {scene_names}')
            return
        self.print('_init')
        self._initSceneStatePars()
        self._initialized = True
        self.ChangeScene(self.Me.par.Scene)
        pass

    def Start(self) -> None:
        self.print(f'Start {self.Scene_name}')
        if self.Selected_scene.isdigit():
            self.__init__(self.Me)
        parent.scenes.ChangeGroup(self.Scene_name)
        pass

    def SetSelectedOutput(self):
        if not self._tox_folder_load:
            print('SetSelectedOutput attempt before folder load')
            return
        if not self._video_folder_load:
            print('SetSelectedOutput attempt before folder load')
            return
        if not self._video_folder_load:
            print('SetSelectedOutput attempt before folder load')
            return
        if not self._bind_par_load:
            print('SetSelectedOutput attempt before Parameter load')
            return
        if len(self._getSceneNames()) == 0:
            print('SetSelectedOutput stopped because no scenes')
            return
        if not self._initialized:
            print('SetSelectedOutput stopped because not initialized')
            return
        try:
            selected_scene_out = find_scene_output(self.Me.op(self.Selected_scene))
            selected_scene_path = selected_scene_out.path
            self.Me.op('selected_scene_out').par.Top = selected_scene_path

            self.Me.op(self.Next_scene).par.Cuein.val = True
            self.Me.op(self.Next_scene).par.Visible.val = True
            self.Me.op(self.Current_scene).par.Cueout.val = True

            next_scene_op = self.Me.op(self.Next_scene)
            if next_scene_op.IsVideo:
                deck_op = op.video.PlayNext(next_scene_op)
                next_scene_op.par.Deckoutput.val = deck_op.op('out1')
        except AttributeError as e:
            print('Next_scene or Current_scene not defined? Error:', e)
            print(f'Next_scene: {self.Next_scene}, Current_scene: {self.Current_scene}')
        pass

    def Shuffle(self):
        is_shuffle = self.Me.par.Shuffle.eval()
        self.print(f'Shuffle: {is_shuffle}')
        if op.playlist is not None:
            # op.playlist.par.Sceneplaylist.val = is_shuffle
            op.playlist.par.Shufflescenes.val = is_shuffle

        pass

    def ChangeScene(self, par) -> None:
        def reset_par(par):
            par.val = self.Selected_scene
            return

        if not self._tox_folder_load:
            self.print(f'{self.Scene_name}: scene change attempt before folder load')
            reset_par(par)
            return

        if not self._video_folder_load:
            self.print(f'{self.Scene_name}: scene change attempt before folder load')
            reset_par(par)
            return
        if not self._video_folder_load:
            self.print(f'{self.Scene_name}: scene change attempt before folder load')
            reset_par(par)
            return
        if not self._bind_par_load:
            self.print(f'{self.Scene_name}: scene change attempt before Parameter load')
            reset_par(par)
            return
        if len(self._getSceneNames()) == 0:
            self.print(f'{self.Scene_name}: ChangeScene stopped because no scenes')
            reset_par(par)
            return
        if not self._initialized:
            self.print(f'{self.Scene_name}: ChangeScene stopped because not initialized')
            reset_par(par)
            return
        if op.transition and op.transition.Transition_active:
            self.print(f'{self.Scene_name}: ChangeScene stopped because transition is active')
            reset_par(par)
            return
        self.print(f'{self.Scene_name}: Before Check: par.eval: {par.eval()}, par.val: {par.val}, Next_scene: {self.Next_scene}')
        if par.eval() == self.Next_scene:
            scene_change = False
            self.print(f'{self.Scene_name}: ChangeScene stopped because scenes are the same')
            self.print(f'{self.Scene_name}: par.eval: {par.eval()}, Next_scene: {self.Next_scene}')
            reset_par(par)
            return
        if op.scenes.Selected_group != self.Scene_name:
            self.print(f'{self.Scene_name}: ChangeScene stopped because not selected group. selected_group: {op.scenes.Selected_group}')
            reset_par(par)
            return

        self.Logger.info(f'{self.Scene_name}: Changing Scene from {self.Next_scene} to {par.eval()}. selected group: {op.scenes.Selected_group}')

        self.print('ChangeScene')
        self.Current_scene = self.Next_scene
        self.Next_scene = par.eval()
        scene_change = self.Next_scene != self.Current_scene

        self.print(f'scene vars at start ChangeScene. current: {self.Current_scene} next: {self.Next_scene} selected: {self.Selected_scene}')
        self.print(f'current scene type: {type(self.Current_scene)}')
        self.print(f'currentscene par eval: {self.Me.par.Currentscene.eval()}, currentscene par menuNames: {self.Me.par.Currentscene.menuNames}')
        if scene_change:
            try:
                self.Me.op(self.Next_scene).par.Cuein.val = True
                self.Me.op(self.Next_scene).par.Visible.val = True
                self.Me.op(self.Current_scene).par.Cueout.val = True

                next_scene_op = self.Me.op(self.Next_scene)
                if next_scene_op.IsVideo:
                    deck_op = op.video.PlayNext(next_scene_op)
                    next_scene_op.par.Deckoutput.val = deck_op.op('out1')
            except AttributeError as e:
                print('Next_scene or Current_scene not defined? Error:', e)
                print(f'Next_scene: {self.Next_scene}, Current_scene: {self.Current_scene}')
                return

        current_scene_out = find_scene_output(self.Me.op(self.Current_scene))
        next_scene_out = find_scene_output(self.Me.op(self.Next_scene))

        current_scene_path = current_scene_out.path
        next_scene_path = next_scene_out.path
        op.transition.par.Currentscene.val = current_scene_path
        op.transition.par.Nextscene.val = next_scene_path
        op.transition.par.Transitionchop.val = f'{self.Me.path}/trans'
        op.transition.InitTransition(self.Me)
        self.Me.op('selected_scene_out').par.Top = current_scene_path
        self.print(f'changing from {self.Current_scene} to {self.Next_scene}')
        self.Selected_scene = self.Current_scene
        selected_scene_out = find_scene_output(self.Me.op(self.Selected_scene))
        selected_scene_path = selected_scene_out.path
        op.transition.par.Selectedscene.val = selected_scene_path
        op('transition_timer/timer1').par.start.pulse()
        self.Num_scene_changes += 1
        self.Me.store('num_scene_changes', self.Num_scene_changes)
        pass

    def TimerSegmentChange(self, timerOp, segment, interrupt):  #pylint: disable=unused-argument
        if not self._tox_folder_load:
            print('timer callback attempt before folder load')
            return
        if not self._video_folder_load:
            print('timer callback attempt before folder load')
            return
        if not self._bind_par_load:
            print('timer callback attempt before Parameter load')
            return
        self.print(f'TimerSegmentChange. segment: {segment}')
        if segment == 1:
            self.Selected_scene = self.Next_scene
            selected_scene_out = find_scene_output(self.Me.op(self.Selected_scene))
            selected_scene_path = selected_scene_out.path
            op.transition.par.Selectedscene.val = selected_scene_path
            try:
                self.Me.op(self.Next_scene).par.Selected.val = True
                self.Me.op(self.Current_scene).par.Selected.val = False
            except AttributeError as e:
                print('could not set par value on scene. it may not exist', e)

            # next_scene_path = f'{self.Me.path}/{self.Next_scene}/out1'
            next_scene_out = find_scene_output(self.Me.op(self.Next_scene))
            next_scene_path = next_scene_out.path
            self.Me.op('selected_scene_out').par.Top = next_scene_path

        pass

    def TimerDone(self, timerOp, segment, interrupt):  #pylint: disable=unused-argument
        self.print('TimerDone')
        if not self._tox_folder_load:
            print('timer callback attempt before folder load')
            return
        if not self._video_folder_load:
            print('timer callback attempt before folder load')
            return
        if not self._bind_par_load:
            print('timer callback attempt before Parameter load')
            return
        self.Me.op(self.Current_scene).par.Visible.val = False
        self.Me.op(self.Current_scene).par.Cueout.val = False
        self.Me.op(self.Next_scene).par.Cuein.val = False

        pass

    def Updatescenes(self):
        print('updatescenes')
        self._onToxFileChange(self.Me.op('folder_tox'))
        self._onVideoFileChange(self.Me.op('folder_video'))
        pass

    def OnFileChange(self, dat, rows=None):
        if 'tox' in dat.name:
            self._onToxFileChange(dat, rows)
        elif 'video' in dat.name:
            self._onVideoFileChange(dat, rows)
        pass

    def _onVideoFileChange(self, dat, rows=None):
        self.print(f'video file change. rows: {rows}')
        created_scene_labels = []
        for row in range(1, dat.numRows):
            video_file_name = dat[row, 'basename'].val
            # name_key = self.Me.op('name_key')
            # video_name = name_key[video_file_name, 'name'].val
            video_name = format_name(video_file_name)

            video_path = pathlib.Path(dat[row, 'path'].val)
            video_modified = int(dat[row, 'datemodified'].val)
            video_is_duplicate = False
            scene_label = format_label(video_name)
            scene_labels = op.scenes.fetch('labels',
                                            {}).get(self.Scene_name, None)
            if scene_labels:
                scene_label = scene_labels.get(video_name, video_name)
            else:
                scene_label = video_name

            created_scene_labels.append(scene_label)

            # self.print(f'scene_label {scene_label}')
            scene_node = self.Me.op(scene_label)
            if scene_node is not None:
                # self.print(f'compare modified: {video_modified} {scene_node.fetch("datemodified", "None")}')
                if scene_node.IsVideo:
                    par_path = pathlib.Path(scene_node.Video_file)
                    scene_video_modified = int(scene_node.fetch("datemodified", 0))
                    # print('comppare paths', str(par_path), str(video_path))
                    video_paths_match = str(par_path) == str(video_path)
                    video_dates_match = scene_video_modified == video_modified
                if scene_node.IsVideo and video_paths_match and video_dates_match:
                    video_is_duplicate = True
                    # print('tox is dupe')

                else:
                    # print('no tox dupe, destroying', scene_label)
                    scene_node.destroy()
                    if video_name in self.Scenes:
                        self.Scenes.remove(video_name)

            if not video_is_duplicate:

                self.print(f'creating video scene: {video_name}')
                # scene_node = self.Me.loadTox(video_path)
                blank_op = self.Me.op('blank_video')
                scene_node = self.Me.copy(blank_op, name=video_name)
                scene_node.Video_file = video_path

                scene_node.name = video_name
                self.Scenes.append(video_name)

                # scene_node.par.externaltox.val = str(video_path)
                scene_node.store('datemodified', video_modified)
                scene_node.tags.add('SCENE')
                try:
                    scene_node.par.w.expr = 'op.output.width'
                    scene_node.par.h.expr = 'op.output.height'
                    scene_node.par.display.mode = ParMode.CONSTANT
                    scene_node.viewer = False

                except AttributeError:
                    print(
                        'could not set height and width parameter on scene',
                        video_name, 'in', self.Scene_name)

                self._addScenePars(scene_node)
        # self._createBlankScenes(created_scene_labels, is_video=True)
        self.print(f'created video labels {created_scene_labels}')
        self._setSceneVariablePars()
        self._arrangeSceneNodes()
        self._video_folder_load = True
        self._init()
        pass


    def _onToxFileChange(self, dat, rows=None):
        self.print(f'tox file change. rows: {rows}')
        created_scene_labels = []
        for row in range(1, dat.numRows):
            tox_file_name = dat[row, 'basename'].val
            # video_file_name = dat[row, 'basename'].val
            # name_key = self.Me.op('name_key')
            # tox_name = name_key[tox_file_name, 'name'].val
            tox_name = tox_file_name.strip().replace('_', '').replace('-', '').title()

            # self.print(f'tox_name {tox_name}')
            tox_path = pathlib.Path(dat[row, 'path'].val)
            tox_modified = int(dat[row, 'datemodified'].val)
            # print('tox_name', tox_name)
            tox_is_duplicate = False
            tox_label = tox_name
            scene_labels = op.scenes.fetch('labels',
                                            {}).get(self.Scene_name, None)
            if scene_labels:
                tox_label = scene_labels.get(tox_name, tox_name)
            else:
                tox_label = tox_name

            created_scene_labels.append(tox_label)

            self.print(f'tox_label {tox_label}')
            scene_tox = self.Me.op(tox_label)
            if scene_tox is not None:
                # self.print(f'compare modified: {tox_modified} {scene_tox.fetch("datemodified", "None")}')
                par_path = pathlib.Path(scene_tox.par.externaltox.eval())
                scene_tox_modified = int(scene_tox.fetch("datemodified", 0))
                # print('compare paths', str(par_path), str(tox_path))
                tox_paths_match = str(par_path) == str(tox_path)
                tox_dates_match = scene_tox_modified == tox_modified
                if tox_paths_match and tox_dates_match:
                    tox_is_duplicate = True
                    # print('tox is dupe')

                else:
                    # print('no tox dupe, destroying', tox_label)
                    scene_tox.destroy()
                    if tox_name in self.Scenes:
                        self.Scenes.remove(tox_name)

            if not tox_is_duplicate:
                scene_tox = self.Me.loadTox(tox_path)

                scene_tox.name = tox_name
                self.Scenes.append(tox_name)

                scene_tox.par.externaltox.val = str(tox_path)
                scene_tox.store('datemodified', tox_modified)
                scene_tox.tags.add('SCENE')
                try:
                    scene_tox.par.w.expr = 'op.output.width'
                    scene_tox.par.h.expr = 'op.output.height'
                    scene_tox.par.display.mode = ParMode.CONSTANT
                    scene_tox.viewer = False

                    scene_render_top = find_scene_render_top(scene_tox)
                    if scene_render_top:
                        parent_shortcut = TDF.getShortcutPath(scene_render_top, scene_tox)
                        scene_render_top.par.resolutionw.expr = f'{parent_shortcut}.width'
                        scene_render_top.par.resolutionh.expr = f'{parent_shortcut}.height'
                except AttributeError:
                    print(
                        'could not set height and width parameter on scene',
                        tox_name, 'in', self.Scene_name)
                if not scene_tox.par.extension1.eval():
                    scene_tox.par.extension1.val = "mod('blank_scene/SceneEXT').SceneEXT(me)"
                    scene_tox.par.promoteextension1.val = True
                self._addScenePars(scene_tox)
        self._tox_folder_load = True
        # self._createBlankScenes(created_scene_labels)
        self.print(f'created tox labels {created_scene_labels}')
        self._setSceneVariablePars()
        self._arrangeSceneNodes()
        self._init()
        pass

    def _addScenePars(self, scene_tox):
        default_pars = TDJ.datToJSON(self.Me.op('blank_scene/scene_pars'))
        TDJ.addParametersFromJSONDict(scene_tox,
                                      default_pars,
                                      replace=True,
                                      setValues=False)
        pass

    def _createBlankScenes(self, scene_labels, is_video=False):
        self.print(f'_createBlankScenes video: {is_video}')
        # print('scene_labels', scene_labels)
        blank_name = 'blank_video' if is_video else 'blank_scene'
        scene_names = self.Me.par.Scene.menuNames
        scene_op_names = [
            scene_op_name for scene_op_name in scene_names
            if self.Me.op(scene_op_name) is not None
        ]
        for scene_op_name in scene_op_names:
            if scene_op_name not in scene_names:
                self.Me.op(scene_op_name).destroy()

        scene_op_names = [
            scene_op_name for scene_op_name in scene_names
            if self.Me.op(scene_op_name) is not None
        ]
        if len(scene_op_names) < len(scene_names):
            for scene_name in scene_names:
                if self.Me.op(scene_name) is None:
                    blank_op = self.Me.op(blank_name)
                    self.Me.copy(blank_op, name=scene_name)

    pass

    def _arrangeSceneNodes(self):
        scene_nodes = self.Me.findChildren(type=containerCOMP,
                                           depth=1,
                                           parExpr='op.output.width')
        scene_nodes.remove(self.Me.op('blank_scene'))
        scene_nodes.remove(self.Me.op('blank_video'))
        ignore_list = self._getNonBlankSceneNodes()
        for scene_node in scene_nodes:
            arrangeNode(scene_node,
                        position='bottom',
                        ignore_nodes=ignore_list)
            ignore_list.remove(scene_node)
        pass

    def _getNonBlankSceneNodes(self):
        scene_nodes = [self.Me.op('blank_scene'), self.Me.op('blank_video')]
        non_scene_nodes = []
        for child in self.Me.children:
            if child not in scene_nodes:
                non_scene_nodes.append(child)
        return non_scene_nodes

    def OnValueChange(self, par):
        if par.name == "Scene":
            self.ChangeScene(par)
            return

        BaseEXT.OnValueChange(self, par)
        pass

    @property
    def Current_scene(self):
        try:
            return self._Current_scene
        except AttributeError:
            self.print('Current_scene not yet initialized')
            self._Current_scene = self.Me.par.Currentscene.eval()
            return self.Me.par.Currentscene.val

    @Current_scene.setter
    def Current_scene(self, val):
        self.print(f'setting Current_scene to {val}')
        if isinstance(val, str) and val.isdigit():
            self.print('changing Current_scene val from digit to par eval')
            val = self.Me.par.Currentscene.eval()
        self.Me.par.Currentscene.val = val
        self._Current_scene = val
        pass

    @property
    def Next_scene(self):
        try:
            return self._Next_scene
        except AttributeError:
            self.print('Next_scene not yet initialized')
            self._Next_scene = self.Me.par.Nextscene.val
            return self.Me.par.Nextscene.val

    @Next_scene.setter
    def Next_scene(self, val):
        self.print(f'setting Next_scene to {val}')
        if isinstance(val, str) and val.isdigit():
            self.print('changing Next_scene val from digit to par eval')
            val = self.Me.par.Nextscene.eval()
        self.Me.par.Nextscene.val = val
        self._Next_scene = val
        pass

    @property
    def Selected_scene(self):
        try:
            return self._Selected_scene
        except AttributeError:
            self.print('Selected_scene not yet initialized')
            self._Selected_scene = self.Me.par.Selectedscene.val
            return self.Me.par.Selectedscene.val

    @Selected_scene.setter
    def Selected_scene(self, val):
        if isinstance(val, str) and val.isdigit():
            self.print('changing Selected_scene val from digit to par eval')
            val = self.Me.par.Selectedscene.eval()
        self.Me.par.Selectedscene.val = val
        self._Selected_scene = val
        pass

    def Print(self, *args):
        str_args = [str(x) for x in args]
        message = ' '.join(str_args)
        return self.print(message)


def arrangeNode(node, position='bottom', spacing=20, ignore_nodes=None):
    """
	Arrange a node according to the other nodes in the network
	position: can be 'bottom', 'top', 'left' or 'right'
		left, right will be placed parallel with top nodes.
		top, bottom will be placed parallel with left nodes.
	"""
    if ignore_nodes is None:
        ignore_nodes = [node]
    else:
        ignore_nodes = ignore_nodes + [node]

    edges = TDF.findNetworkEdges(node.parent(), ignore_nodes)
    if edges is None:
        node.nodeX = node.nodeY = 0
        return
    extremes = edges['positions']
    if position == 'bottom':
        node.nodeX = extremes['left']
        node.nodeY = extremes['bottom'] - node.nodeHeight - spacing
    elif position == 'top':
        node.nodeX = extremes['left']
        node.nodeY = extremes['top'] + spacing
    elif position == 'right':
        node.nodeX = extremes['right'] + spacing
        node.nodeY = extremes['top'] - node.nodeHeight
    elif position == 'left':
        node.nodeX = extremes['left'] - node.nodeWidth - spacing
        node.nodeY = extremes['top'] - node.nodeHeight
    else:
        raise ValueError('Invalid arrangeNode position', position)

def find_scene_output(scene_op):
    # print('find_scene_output', scene_op)
    if scene_op is None:
        return
    outputs = [outputConnector.outOP for outputConnector in scene_op.outputConnectors]

    outputs_list = outputs.copy()
    if len(outputs) > 1:
        for output in outputs:
            if output.OPType != 'outTOP':
                outputs_list.remove(output)

    if len(outputs_list) >= 1:
        return outputs_list[0]
    elif len(outputs_list) == 0:
        # print('no outputs found for', scene_op)
        return scene_op.op('out1')

def find_render_top(start_op):
    if start_op is None:
        print('find_render_top must not be None')
        return

    render_tops = []
    def find_end_op(next_op):
        for op_input in next_op.inputs:
            if len(op_input.inputs) != 0:
                find_end_op(op_input)
            else:
                if op_input.OPType == 'renderTOP':
                    # print('no more inputs', op_input)
                    render_tops.append(op_input)

    find_end_op(start_op)
    if len(render_tops) == 1:
        return render_tops[0]
    elif len(render_tops) == 0:
        # print('no render tops found')
        return start_op.parent().op('render1')
    else:
        # return render_tops
        main_render_top = render_tops[0]
        op_parent = start_op.parent()
        for render_top in render_tops:
            if TDF.parentLevel(op_parent, render_top) < main_render_top:
                main_render_top = render_top
        return main_render_top


def find_scene_render_top(scene_op):
    scene_out = find_scene_output(scene_op)
    return find_render_top(scene_out)

def getFirstLetterIndex(name):
    for i in range(len(name)):
        if not name[i].isdigit():
            return i
    return None

def format_name(name):
    new_name = name
    new_name = tdu.legalName(new_name).strip().replace('_', '').replace('-', '').lower()
    new_name = new_name.replace('4k', '')
    if new_name[0].isdigit():
        new_name = new_name[getFirstLetterIndex(new_name):]
    new_name = "%s%s" % (new_name[0].upper(), new_name[1:].lower())
    return new_name

def format_label(name):
    max_words = 5

    emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                            "]+", flags=re.UNICODE)
    name = emoji_pattern.sub(r'', name) # no emoji

    label = ' '.join(name.split()[:max_words])
    return label
