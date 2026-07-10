# TouchDesigner Code Style Guide

> Claude style guide for TouchDesigner Python extension development at Volvox Labs.
> Based on patterns from the TD-GRANITE-RENDER codebase. Follow these conventions when writing or modifying any TouchDesigner extension code.

## Table of Contents

1. [Extension Class Structure](#1-extension-class-structure)
2. [Parameter Creation](#2-parameter-creation)
3. [Parameter Callbacks](#3-parameter-callbacks)
4. [Operator Interaction](#4-operator-interaction)
5. [Initialization Patterns](#5-initialization-patterns)
6. [Lifecycle Methods](#6-lifecycle-methods)
7. [Import Patterns](#7-import-patterns)
8. [Page Management](#8-page-management)
9. [Logging and Debugging](#9-logging-and-debugging)
10. [Error Handling](#10-error-handling)
11. [Operator Shortcuts](#11-operator-shortcuts)
12. [Preset Management](#12-preset-management)
13. [Replication Patterns](#13-replication-patterns)

---

## 1. Extension Class Structure

### Base Classes

Extensions inherit from base classes provided by `vvox_tdtools`:

- **`BaseEXT`**: Base class for all extensions
- **`PresetBaseEXT`**: Extends `BaseEXT` with preset management functionality
- **`ProjectEXT`**: Base class for project-level extensions

### Example: Basic Extension

```python
from vvox_tdtools.base import BaseEXT

class MyExtensionEXT(BaseEXT):
    def __init__(self, myop: OP) -> None:
        BaseEXT.__init__(self, myop, par_callback_on=True)
        # ... initialization code ...
        pass
```

**File Reference**: `td-modules/data_out/dataOutEXT.py:15-20`

### Example: Preset-Based Extension

```python
from vvox_tdtools.preset_base import PresetBaseEXT

class LayerEXT(PresetBaseEXT):
    def __init__(self, myop: OP) -> None:
        preset_path = op.project.Assets_path / f"presets/{myop.name}/presets.json"
        if not preset_path.parent.exists():
            preset_path.parent.mkdir(parents=True)
        PresetBaseEXT.__init__(
            self,
            myop,
            par_mode=ParMode,
            preset_file=preset_path,
            propagate_children=True
        )
        # ... initialization code ...
        pass
```

**File Reference**: `py_modules/layerEXT.py:17-22`

### Example: Multiple Inheritance

```python
class HeroLayerEXT(LayerEXT, StateMachineEXT):
    def __init__(self, myop: OP) -> None:
        LayerEXT.__init__(self, myop)
        StateMachineEXT.__init__(self, myop)
        StateMachineEXT._createControlsPage(self)
        # ... initialization code ...
        pass
```

**File Reference**: `td-modules/hero_layer/heroLayerEXT.py:22-29`

### Constructor Pattern

The constructor pattern follows this structure:

1. Call parent `__init__` with appropriate parameters
2. Set operator shortcut
3. Create control pages
4. Initialize instance variables
5. Access child operators
6. Set up callbacks/event handlers

### Example: Standard Constructor

```python
class CmsControllerEXT(BaseEXT):
    def __init__(self, myop: OP) -> None:
        BaseEXT.__init__(self, myop, par_callback_on=True)
        self._createControlsPage()
        self.Me.par.opshortcut = "cms"
        self.current_db_call = "heroes"
        self.database_ids = {
            "assets": "1a7a1f18f40f807fb98ccb2113807ac1",
            # ... more database IDs ...
        }
        self.IncomingContent = {}
        # ... more initialization ...
        pass
```

**File Reference**: `td-modules/cms_controller/cmsControllerEXT.py:25-103`

### BaseEXT Initialization Parameters

When calling `BaseEXT.__init__()`, common parameters include:

- `par_callback_on=True`: Enables parameter callbacks using `_onParameterName` pattern
- `global_shortcut=False`: Sets operator shortcut globally (default: False)
- `par_callback_unpublished=False`: Enable callbacks for unpublished parameters
- `par_callback_private=False`: Enable callbacks for private parameters
- `use_par_values_changed=False`: Use `OnValuesChanged` instead of `OnValueChange`

### Example: With Global Shortcut

```python
class OscOutEXT(BaseEXT):
    def __init__(self, myop: OP) -> None:
        BaseEXT.__init__(self, myop, par_callback_on=True, global_shortcut=True)
        # ... initialization ...
        pass
```

**File Reference**: `td-modules/osc_out/oscOutEXT.py:16-17`

---

## 2. Parameter Creation

### Using ParTemplate

The `ParTemplate` class is the preferred method for creating custom parameters. It provides a clean, declarative way to define parameters.

### Basic Usage

```python
from vvox_tdtools.parhelper import ParTemplate

def _createControlsPage(self) -> None:
    page = self.GetPage('Controls')
    pars = [
        ParTemplate('Testoutput', par_type='Toggle', label='Test Output'),
        ParTemplate('Hostname', par_type='Str', label='Hostname'),
        ParTemplate('Port', par_type='Str', label='Port'),
    ]
    for par in pars:
        par.createPar(page)
    pass
```

**File Reference**: `td-modules/osc_out/oscOutEXT.py:35-44`

### Parameter Types

Common parameter types used with `ParTemplate`:

- `'Toggle'`: Boolean toggle
- `'Str'`: String parameter
- `'Int'`: Integer parameter
- `'Float'`: Float parameter
- `'Pulse'`: Pulse button
- `'Menu'`: Menu/dropdown
- `'File'`: File path
- `'Folder'`: Folder path
- `'XY'`, `'UV'`, `'RGB'`, `'RGBA'`: Vector types
- `'OP'`, `'COMP'`, `'TOP'`, `'CHOP'`, `'DAT'`: Operator reference types

### Setting Parameter Properties

```python
def _createControlsPage(self) -> None:
    page = self.GetPage('Controls')

    # Read-only parameter
    refresh_status = ParTemplate('ContentStatus', par_type='Str', label='ContentStatus')
    refresh_status.readOnly = True

    # Parameter with expression
    perf_mode = ParTemplate('Performmode', par_type='Toggle', label='Perform Mode')
    perf_mode.expr = "op('./perform1')['perform_mode']"

    # Menu parameter with options
    positions_par = ParTemplate('Positions', par_type='Menu', label='Positions')
    positions_par.menuNames = ['top_left', 'top_right', 'bottom_left', 'bottom_right']
    positions_par.menuLabels = positions_par.menuNames

    pars = [refresh_status, perf_mode, positions_par]
    for par in pars:
        par.createPar(page)
    pass
```

**File Reference**: `py_modules/graniteProjectEXT.py:240-268`

### Parameter Ordering

```python
def _createAdminPage(self) -> None:
    super()._createAdminPage()
    version_par = ParTemplate('Version', 'Str', self._version)
    version_par.readOnly = True
    version_par.order = 0  # Set order to appear first
    version_par.createPar(self.Admin_page)
    pass
```

**File Reference**: `td-modules/feathers_client/feathersClientEXT.py:696-702`

### Direct Parameter Creation

While `ParTemplate` is preferred, you can also create parameters directly using page methods:

```python
def _createControlsPage(self) -> None:
    page = self.GetPage('Controls')
    # Direct creation (less common)
    new_par = page.appendToggle('MyToggle', label='My Toggle')[0]
    new_par.val = False
    pass
```

**Note**: Direct creation is less common in this codebase. Prefer `ParTemplate` for consistency.

### Parameter Expressions

Parameters can use expressions to reference other operators or values:

```python
# Setting expression after creation
self.Me.par.w.expr = 'parent().width'
self.Me.par.h.expr = 'parent().height'

# Setting expression via ParTemplate
perf_mode.expr = "op('./perform1')['perform_mode']"

# Frame parameter with expression
if role == 'follower':
    self.Me.par.Frame.expr = 'op.sync_in.GetOut()["frame"]'
else:
    self.Me.par.Frame.expr = 'absTime.frame % 2592000'
```

**File Reference**: `py_modules/layerEXT.py:99-100`, `py_modules/graniteProjectEXT.py:193-195`

---

## 3. Parameter Callbacks

### Naming Convention

Parameter callbacks follow a strict naming pattern: `_onParameterName` where `ParameterName` matches the parameter name (case-sensitive).

### Basic Callback Pattern

```python
def _onShowlayer(self, par: Par) -> None:
    if par.eval():
        self.ShowLayer()
    else:
        self.HideLayer()
    pass
```

**File Reference**: `td-modules/custom_layer/customLayerEXT.py:99-104`

### Callback Registration

Callbacks are automatically registered when:

1. `par_callback_on=True` is set in `BaseEXT.__init__()`
2. The method follows the `_onParameterName` naming convention
3. The parameter exists on the operator

### Example: Toggle Parameter Callback

```python
def _onEnablestatemachinedebug(self):
    self.Follower.op("composite_zones/state_machine_debug").allowCooking = \
        self.Me.par.Enablestatemachinedebug.eval()
    pass
```

**File Reference**: `td-modules/state_machine/stateMachineEXT.py:73-75`

### Example: Menu Parameter Callback

```python
def _onActiveeventsnames(self, par: Par) -> None:
    self.Logger.debug(f"_onActiveeventsnames - val:{par.eval()}")
    if not par.eval():
        return
    # Update the active event name based on the selected value
    self.Print(f"Active event names:{par.menuNames}")
    pass
```

**File Reference**: `td-modules/zones_model/zonesModelEXT.py:114-119`

### Example: Pulse Parameter Callback

```python
def _onRefreshcontentlib(self, par):
    self.RefreshAllContent()
    pass
```

**File Reference**: `td-modules/cms_controller/cmsControllerEXT.py:576-578`

**Note**: Pulse callbacks don't receive the `par` parameter in some cases, but the signature can still include it.

### Example: Parameter with Previous Value

```python
def OnAdsrChange(self, val: float, prev: float) -> None:
    if val == 1.0 and val != prev:
        self.Logger.debug("ADSR value changed to 1.0, starting timer")
        self.Leader.op('timer1').par.start.pulse()
        self.Leader.op('timer1').par.play.val = True
    if val == 0.0 and val != prev:
        self.Logger.debug("ADSR value changed to 0.0, stopping timer")
        self.Leader.op('timer1').par.play.val = True
    return
```

**File Reference**: `td-modules/custom_layer/customLayerEXT.py:137-149`

### Callback Examples in Template Files

Many extension files include commented examples:

```python
# Below is an example of a parameter callback. Simply create a method that
# starts with "_on" and then the name of the parameter.

# def _onExampletoggle(self, par):
#     self.Logger.debug(f"_onExampleToggle - val: {par.eval()}")
#     pass
```

**File Reference**: `td-modules/data_out/dataOutEXT.py:30-34`

### Case Sensitivity

Callback names are case-sensitive. Both patterns exist in the codebase:

```python
# CamelCase parameter name
def _onGetZonesData(self):
    self.GetZonesData()
    pass

# Lowercase parameter name
def _onGetzonesdata(self):
    self.GetZonesData()
    pass
```

**File Reference**: `td-modules/zones_model/zonesModelEXT.py:97-103`

**Best Practice**: Use consistent casing that matches your parameter names exactly.

---

## 4. Operator Interaction

### Accessing Operators

#### Using `Me.op()`

Access child operators relative to the extension's operator:

```python
self.Leader = self.Me.op('leader')
self.Follower = self.Me.op('follower')
self.osc_dat = self.Me.op('oscout1')
self.Merge_op = self.Me.op('merge1')
```

**File Reference**: `py_modules/layerEXT.py:26-27`, `td-modules/osc_out/oscOutEXT.py:19`

#### Using `op()` Global Function

Access operators from anywhere using shortcuts or paths:

```python
# Using operator shortcut
op.cms.RequestNotion('hero_layer')
op.feathers_client.On('zones patched', self.Me.OnZonesPatched)
op.project.par.Role.eval()

# Using path
op.layers.LoadPreset(scene)
op.transition_layer.Presets_data['presets'].keys()
```

**File Reference**: `td-modules/state_machine/stateMachineEXT.py:81`, `td-modules/zones_model/zonesModelEXT.py:44`

#### Using `root.op()`

Access operators from the root level:

```python
self.main_window = root.op('main')
self.status_view = root.op('window_status_view')
```

**File Reference**: `py_modules/graniteProjectEXT.py:22-23`

### Finding Children

#### `findChildren()` Method

Find child operators with various filters:

```python
# Find all children of a specific type
child_ops = self.Me.findChildren(type=COMP)
for child_op in child_ops:
    if 'annotate' in child_op.name:
        continue
    # ... process child ...
```

**File Reference**: `td-modules/layers/layersEXT.py:114`

```python
# Find children by name pattern
layer_ops = self.Me.findChildren(depth=1, name="*layer")
return layer_ops
```

**File Reference**: `td-modules/layers/layersEXT.py:82`

```python
# Find children of specific type
movie_ops = self.Me.findChildren(type=moviefileinTOP)
for movie_op in movie_ops:
    movie_op.par.frametimeout.val = 0
    movie_op.par.opentimeout.val = 0
```

**File Reference**: `py_modules/graniteProjectEXT.py:214-218`

#### Finding Components

```python
def initializeChildren(self):
    components = self.Me.findChildren(type=COMP, maxDepth=1)
    for component in components:
        if hasattr(component, 'Init'):
            init_method = getattr(component, "Init")
            if callable(init_method):
                init_method()
    pass
```

**File Reference**: `dep/python/vvox_tdtools/base.py:89-96`

### Creating Operators

While less common in extensions (usually done in .tox files), operators can be created programmatically:

```python
# Creating a DAT operator
parexec_dat = self.Me.op('parexec1')
if parexec_dat is None:
    parexec_dat = self.Me.create('parameterexecuteDAT', 'parexec1')
    parexec_dat.text = inspect.getsource(parexec)
    parexec_dat.par.pars.val = '*'
```

**File Reference**: `dep/python/vvox_tdtools/base.py:103-109`

### Operator Properties

#### Setting `allowCooking`

```python
# Enable/disable cooking based on role
role = op.project.par.Role.eval()
if role == 'follower':
    touchin_template.allowCooking = True
else:
    touchin_template.allowCooking = False

# Conditional cooking
self.Follower.op("composite_zones/state_machine_debug").allowCooking = \
    self.Me.par.Enablestatemachinedebug.eval()
```

**File Reference**: `td-modules/layer_top_in/layerTopInEXT.py:23-27`, `td-modules/state_machine/stateMachineEXT.py:74`

#### Setting Tags

```python
# Add tag
if 'status_view' not in self.Me.tags:
    self.Me.tags.add('status_view_menu')

# Remove tag
if 'status_view_menu' in leader_op.tags:
    leader_op.tags.remove('status_view_menu')
```

**File Reference**: `td-modules/layers/layersEXT.py:60-61`, `py_modules/graniteProjectEXT.py:143`

### Operator Paths and Navigation

#### Relative Paths

```python
# Access nested operators
zone_op.op('zone_control/playback_timer').par.start.pulse()
self.Follower.op("composite_zones/state_machine_debug").allowCooking = False
```

**File Reference**: `td-modules/state_machine/stateMachineEXT.py:67-69`

#### Parent Access

```python
parent = touchin_op.parent()
touchin_name = parent.name
```

**File Reference**: `td-modules/layer_top_in/layerTopInEXT.py:41-42`

#### Relative Path Calculation

```python
depth = child_op.relativePath(self.Me).count('/')
```

**File Reference**: `td-modules/layers/layersEXT.py:118`

---

## 5. Initialization Patterns

### OnInit() Method

The `OnInit()` method is called after the extension is constructed. It should return `True` on success or `False` to halt initialization.

### Standard Pattern

```python
def OnInit(self):
    # return False if initialization fails
    return True
```

**File Reference**: `td-modules/data_out/dataOutEXT.py:22-24`

### Initialization with Setup

```python
def OnInit(self):
    # return False if initialization fails
    self.OnProjectInit()
    return True
```

**File Reference**: `py_modules/graniteProjectEXT.py:35-38`

### Conditional Initialization

```python
def OnInit(self):
    ext_init = self.Me.par.Extinit.eval()
    if ext_init:
        self.Logger.warning('StateMachineEXT already initialized, skipping')
        return super().OnInit()
    self.Me.par.Extinit.val = True
    self.ConfigureActiveZones(is_init=True)
    return super().OnInit()
```

**File Reference**: `td-modules/state_machine/stateMachineEXT.py:53-63`

### Role-Based Initialization

```python
def OnInit(self):
    role = op.project.par.Role.eval()
    if role == 'follower':
        return True
    self.Initialize()
    return True
```

**File Reference**: `td-modules/feathers_client/feathersClientEXT.py:54-59`

### OnStart() Method

Called when the project starts playing:

```python
def OnStart(self):
    self.Me.par.Projectinit.val = False
    pass
```

**File Reference**: `py_modules/graniteProjectEXT.py:31-33`

```python
def OnStart(self):
    self.Me.par.Extinit.val = False
    pass
```

**File Reference**: `td-modules/state_machine/stateMachineEXT.py:49-51`

### OnCreate() Method

Called when the operator is created:

```python
def OnCreate(self):
    self.print('OnCreate')
    pass
```

**File Reference**: `scripts/sceneEXT.py:28-30`

### Initialization Order

The typical initialization order is:

1. `__init__()` - Constructor sets up basic structure
2. `OnInit()` - Performs initialization logic
3. `OnStart()` - Called when project starts
4. `OnCreate()` - Called when operator is created (if applicable)

### Delayed Initialization

Sometimes initialization needs to be delayed:

```python
def _getExtensionsReady(self):
    ready_expression = 'me.OnExtensionsReady()'
    run(ready_expression, delayFrames=1, fromOP=self.Me)
    pass

def OnExtensionsReady(self):
    print('OnExtensionsReady')
    self._init_feathers_callbacks()
    pass
```

**File Reference**: `td-modules/zones_model/zonesModelEXT.py:32-40`

### OnConfigLoad() Method

Called when configuration is loaded:

```python
def OnConfigLoad(self):
    self._setWindows()
    self._setProps()
    return super().OnConfigLoad()
```

**File Reference**: `py_modules/graniteProjectEXT.py:73-76`

```python
def OnConfigLoad(self):
    self._initRole()
    return super().OnConfigLoad()
```

**File Reference**: `py_modules/layerEXT.py:67-69`

---

## 6. Lifecycle Methods

### Frame Callbacks

#### OnFrameStart()

Called at the start of each frame:

```python
def OnFrameStart(self, frame: int) -> None:
    # run every second (at 30fps)
    if frame % 30 == 0:
        self.CheckFlourishTime()
        self._calculateSystemLoaded()
        self.CheckUpdateFollowerPresets()
    return super().OnFrameStart(frame)
```

**File Reference**: `td-modules/scene_controller/sceneControllerEXT.py:41-47`

#### OnFrameEnd()

Called at the end of each frame:

```python
def OnFrameEnd(self, frame):
    self.EventLoop()
    return super().OnFrameEnd(frame)
```

**File Reference**: `td-modules/feathers_client/feathersClientEXT.py:69-72`

### Play State Changes

#### OnPlayStateChange()

Called when play state changes:

```python
def OnPlayStateChange(self, state: bool):
    pass
```

**File Reference**: `dep/python/vvox_tdtools/base.py:154-155`

### Device Changes

#### OnDeviceChange()

Called when input devices change:

```python
def OnDeviceChange(self):
    pass
```

**File Reference**: `dep/python/vvox_tdtools/base.py:157-158`

### Project Save Callbacks

#### OnProjectPreSave()

Called before project is saved:

```python
def OnProjectPreSave(self):
    pass
```

**File Reference**: `dep/python/vvox_tdtools/base.py:160-161`

#### OnProjectPostSave()

Called after project is saved:

```python
def OnProjectPostSave(self):
    pass
```

**File Reference**: `dep/python/vvox_tdtools/base.py:163-164`

### Event Loop Pattern

A common pattern for periodic tasks:

```python
def OnFrameStart(self, frame: int):
    if frame % 60 == 0:  # Every second at 60fps
        self.OnEventLoop1()
    return

def OnEventLoop1(self):
    self.Print('every second')
    pass
```

**File Reference**: `td-modules/layer_sync_data/layerSyncDataEXT.py:38-47`

---

## 7. Import Patterns

### Standard Import Pattern

All extensions use a consistent import pattern with fallback to mock objects:

```python
try:
    # import td
    from td import OP, root, op, run  # type: ignore
    # TDJ = op.TDModules.mod.TDJSON
    # TDF = op.TDModules.mod.TDFunctions
except ModuleNotFoundError:
    from vvox_tdtools.td_mock import OP, parent, root, op, run  # pylint: disable=ungrouped-imports
    # from tdconfig import TDJSON as TDJ
    # from tdconfig import TDFunctions as TDF
```

**File Reference**: `td-modules/cms_controller/cmsControllerEXT.py:12-20`

### Common Imports

Frequently imported TouchDesigner types:

- `OP`: Operator type
- `Par`: Parameter type
- `COMP`: Component type
- `TOP`: Texture operator type
- `CHOP`: Channel operator type
- `DAT`: Data operator type
- `op`: Global operator access function
- `root`: Root operator
- `project`: Project object
- `run`: Function to run expressions with delay

### Type Ignore Comments

Use `# type: ignore` for TouchDesigner imports since type checkers don't recognize them:

```python
from td import OP, root, op, run  # type: ignore
```

### Pylint Disable Comments

Disable `ungrouped-imports` warning for fallback imports:

```python
except ModuleNotFoundError:
    from vvox_tdtools.td_mock import OP, op, run  # pylint: disable=ungrouped-imports
```

### Relative Imports for Local Modules

When importing from sibling modules:

```python
try:
    from layerEXT import LayerEXT  # type: ignore
except ModuleNotFoundError():
    from ...py_modules.layerEXT import LayerEXT  # pylint: disable=relative-beyond-top-level
```

**File Reference**: `td-modules/custom_layer/customLayerEXT.py:15-18`

### Import Organization

Standard import order:

1. Standard library imports
2. Third-party imports
3. Local vvox_tdtools imports
4. TouchDesigner imports (with fallback)
5. Local module imports (with fallback)

```python
# Standard library
import json
import datetime
from pathlib import Path

# Third-party
from jsonschema import validate, ValidationError

# Local tools
from vvox_tdtools.base import BaseEXT
from vvox_tdtools.parhelper import ParTemplate

# TouchDesigner (with fallback)
try:
    from td import OP, root, op, run  # type: ignore
except ModuleNotFoundError:
    from vvox_tdtools.td_mock import OP, root, op, run  # pylint: disable=ungrouped-imports
```

**File Reference**: `td-modules/cms_controller/cmsControllerEXT.py:1-20`

---

## 8. Page Management

### Getting Pages

#### GetPage() Method

Get or create a custom page:

```python
def _createControlsPage(self) -> None:
    page = self.GetPage('Controls')
    # ... create parameters ...
    pass
```

**File Reference**: `td-modules/data_out/dataOutEXT.py:48-57`

The `GetPage()` method:

- Returns existing page if found
- Creates new page if it doesn't exist (default behavior)
- Can be configured to not create if `create=False`

### Creating Custom Pages

#### Controls Page

Most extensions have a "Controls" page:

```python
def _createControlsPage(self) -> None:
    page = self.GetPage('Controls')
    pars = [
        ParTemplate('Testoutput', par_type='Toggle', label='Test Output'),
    ]
    for par in pars:
        par.createPar(page)
    pass
```

**File Reference**: `td-modules/osc_out/oscOutEXT.py:35-44`

#### Props Page

Many extensions have a "Props" page for read-only properties:

```python
def _createPropsPage(self) -> None:
    page = self.GetPage('Props')
    pars = [
        ParTemplate('Frame', par_type='Int', label='Frame'),
        ParTemplate('Role', par_type='Str', label='Role'),
        # ... more props ...
    ]
    for par in pars:
        par.readOnly = True
        par.createPar(page)
    pass
```

**File Reference**: `py_modules/graniteProjectEXT.py:240-269`

#### Admin Page

The Admin page is automatically created by `BaseEXT`:

```python
def _createAdminPage(self) -> None:
    super()._createAdminPage()  # Call parent to create base admin page
    version_par = ParTemplate('Version', 'Str', self._version)
    version_par.readOnly = True
    version_par.order = 0
    version_par.createPar(self.Admin_page)
    pass
```

**File Reference**: `td-modules/feathers_client/feathersClientEXT.py:696-702`

### Page Organization

Common page organization:

- **Controls**: User-controllable parameters
- **Props**: Read-only properties/status
- **Admin**: Administrative settings (auto-created by BaseEXT)
- **Custom pages**: Additional pages as needed (e.g., "Zone", "Fade", etc.)

### Example: Multiple Pages

```python
def __init__(self, myop: OP) -> None:
    LayerEXT.__init__(self, myop)
    self._createControlsPage()
    self._createFadeControlsPage()  # Additional custom page
    # ... initialization ...
    pass
```

**File Reference**: `td-modules/custom_layer/customLayerEXT.py:20-36`

### Accessing Page Parameters

Iterate over parameters in a page:

```python
def _autoUpdateProps(self, data, sub_keys: list = None) -> None:
    props_page = self.GetPage('Props')
    for props_par in props_page.pars:
        par_data = data.get(props_par.label, None)
        if par_data is None:
            continue
        props_par.val = par_data
    pass
```

**File Reference**: `td-modules/zones_model/zonesModelEXT.py:60-73`

---

## 9. Logging and Debugging

### Logger Usage

Extensions have a `Logger` attribute (Python `logging.Logger` instance) automatically created by `BaseEXT`:

```python
# Debug level
self.Logger.debug(f"Parsing data to content lib{layer_name}")

# Info level
self.Logger.info('Playing Flourish')

# Warning level
self.Logger.warning('StateMachineEXT already initialized, skipping')

# Error level
self.Logger.error(f"Error Ingesting{layer_name}{e}")
self.Logger.error(traceback.format_exc())
```

**File Reference**: Various files throughout codebase

### Setting Debug Mode

#### SetDebug()

Enable/disable debug mode:

```python
self.SetDebug(True)
self.SetLogtextport(True)
```

**File Reference**: `td-modules/layers/layersEXT.py:28-29`

Debug mode:

- Sets `self.Debug = True`
- Changes logger level to `logging.DEBUG`
- Enables `print()` statements via `self.print()`

#### SetLogtextport()

Enable logging to TouchDesigner textport:

```python
self.SetLogtextport(True)
```

**File Reference**: `td-modules/layers/layersEXT.py:29`

### Print vs Logger

#### Using `self.print()`

Conditional printing based on debug mode:

```python
def print(self, *args):
    if self.Debug:
        str_args = [str(x) for x in args]
        message = ' '.join(str_args)
        new_message = f'{self.name}:{message}'
        print(new_message)
        return new_message
    pass
```

**File Reference**: `dep/python/vvox_tdtools/base.py:382-389`

Usage:

```python
self.print('Initialize')
self.Print('OnStart')  # Alias for print()
```

**File Reference**: `td-modules/feathers_client/feathersClientEXT.py:62`

#### Using Logger

For structured logging:

```python
self.Logger.debug('OnInit')
self.Logger.info('OnAllExtensionsReady')
self.Logger.warning('Project already initialized, skipping')
self.Logger.error(f"Error setting file expr:{e}")
```

### Logging Levels

Standard Python logging levels are used:

- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical error messages

### Conditional Logging

```python
if level == 'error' or level == 'fatal':
    self.Logger.error(message)
elif level == 'warning' and self.Log_warnings:
    self.Logger.warning(message)
elif level == 'info' and self.Log_info:
    self.Logger.info(message)
```

**File Reference**: `py_modules/graniteProjectEXT.py:232-237`

### Error Logging with Traceback

```python
except Exception as e:
    self.Logger.error(f"Error Ingesting{layer_name}{e}")
    self.Logger.error(traceback.format_exc())
```

**File Reference**: `td-modules/cms_controller/cmscontrollerhttp.py:355`

---

## 10. Error Handling

### Try-Except Patterns

#### Basic Error Handling

```python
try:
    self.Content_lib = json.loads(self.Me.op("text1").text)
except Exception as e:
    self.Logger.debug(f"Problem loading content lib{e}")
    self.Content_lib = {}
```

**File Reference**: `td-modules/cms_controller/cmsControllerEXT.py:105-110`

#### Error Handling with Fallback

```python
try:
    assets_path = Path(root.var("assets_path")) / "content_lib"
    assets_path.mkdir(parents=True, exist_ok=True)
    schema_file_path = assets_path / "content_lib_schema.json"
    with schema_file_path.open("r") as schema_file:
        content_lib_schema = json.load(schema_file)
except Exception as e:
    self.Logger.error("Failed to load content lib schema")
    self.Logger.error(e)
    content_lib_schema = {}
```

**File Reference**: `td-modules/cms_controller/cmsControllerEXT.py:89-99`

#### Error Handling with Validation

```python
def ValidateContentLib(self):
    errors = []
    try:
        validate(self.IncomingContent, self.content_lib_schema)
        return True
    except ValidationError as e:
        errors.append(str(e))
        self.Logger.error("Content lib failed validation")
        self.Me.par.Contentstatus = "Schema Validation Failed"
        self.Me.par.Errors = str(e)
        self.Logger.error(e)
        return False
```

**File Reference**: `td-modules/cms_controller/cmsControllerEXT.py:137-149`

### Error Reporting to Parameters

Errors are often reported to parameters for UI display:

```python
self.Me.par.Contentstatus = "Schema Validation Failed"
self.Me.par.Errors = str(e)
self.Me.par.Failedassetid = "none "
```

**File Reference**: `td-modules/cms_controller/cmsControllerEXT.py:146-147`

### Graceful Degradation

Continue operation with default values on error:

```python
try:
    file_info = par.evalFile()
    is_file = file_info.exists
    if is_file:
        # ... process file ...
except Exception as e:
    self.Logger.error(f"Error setting file expr:{e}")
    # Continue without setting expression
    pass
```

**File Reference**: `td-modules/layers/layersEXT.py:91-110`

### Error Handling in Callbacks

```python
def OnZonesPatched(self, message):
    try:
        data = self._getMessageData(message)
        if not data:
            return
        self._autoUpdateProps(data)
    except Exception as e:  # pylint:disable=broad-except
        self.Logger.error(f"OnZonesPatched Exception:{e}")
    pass
```

**File Reference**: `td-modules/zones_model/zonesModelEXT.py:48-58`

### Pylint Exception Handling

Use `# pylint:disable=broad-except` when catching generic exceptions:

```python
except Exception as e:  # pylint:disable=broad-except
    self.Logger.error(f"Error:{e}")
```

---

## 11. Operator Shortcuts

### Setting Operator Shortcuts

#### Basic Shortcut

```python
self.Me.par.opshortcut = "cms"
```

**File Reference**: `td-modules/cms_controller/cmsControllerEXT.py:30`

#### Using Operator Name

```python
self.Me.par.opshortcut.val = self.Me.name
```

**File Reference**: `td-modules/layer_sync_data/layerSyncDataEXT.py:18`

#### Setting via BaseEXT

```python
BaseEXT.__init__(self, myop, global_shortcut=True)
```

When `global_shortcut=True`, the shortcut is set automatically to the operator name.

**File Reference**: `td-modules/osc_out/oscOutEXT.py:17`

### Using Shortcuts

Once set, shortcuts can be accessed via `op`:

```python
# Access via shortcut
op.cms.RequestNotion('hero_layer')
op.feathers_client.On('zones patched', self.Me.OnZonesPatched)
op.project.par.Role.eval()
op.layers.LoadPreset(scene)
```

**File Reference**: Various files

### Parent Shortcuts

Some extensions set parent shortcuts:

```python
self.Me.par.parentshortcut.val = 'layer'
```

**File Reference**: `py_modules/layerEXT.py:25`

### Shortcut Best Practices

1. Use descriptive, short names
2. Match operator name when possible
3. Use lowercase for consistency
4. Avoid conflicts with built-in operators

---

## 12. Preset Management

### PresetBaseEXT Usage

Extensions that manage presets inherit from `PresetBaseEXT`:

```python
from vvox_tdtools.preset_base import PresetBaseEXT

class LayerEXT(PresetBaseEXT):
    def __init__(self, myop: OP) -> None:
        preset_path = op.project.Assets_path / f"presets/{myop.name}/presets.json"
        if not preset_path.parent.exists():
            preset_path.parent.mkdir(parents=True)
        PresetBaseEXT.__init__(
            self,
            myop,
            par_mode=ParMode,
            preset_file=preset_path,
            propagate_children=True
        )
        # ... initialization ...
        pass
```

**File Reference**: `py_modules/layerEXT.py:17-22`

### Preset Callbacks

#### OnPresetLoad()

Called when a preset is loaded:

```python
def OnPresetLoad(self, preset_name):
    self.ResetTriggers()
    print(f"{self.Me.name} PresetLoad:{preset_name}")
    return super().OnPresetLoad(preset_name)
```

**File Reference**: `py_modules/layerEXT.py:71-74`

```python
def OnPresetLoad(self, preset_name):
    self.UpdateAssetFolder(preset_name)
    role = op.project.par.Role.eval()
    if role != 'follower':
        op.rcp_client.SendLoadPreset(self.Me.name, preset_name)
    self.Logger.debug(f"OnPresetLoad - preset_name:{preset_name}")
    run('op.loading_controller.LoadFiles()', delayFrames=10)
    return super().OnPresetLoad(preset_name)
```

**File Reference**: `td-modules/layers/layersEXT.py:135-147`

#### OnBeforePresetLoad()

Called before preset is loaded, allows modification of parameter data:

```python
def OnBeforePresetLoad(self, preset_name: str, par_data: list) -> list:
    print(f"{self.Me.name} OnBeforePresetLoad:{preset_name}")
    is_active = True
    active_par_obj = {}
    for par_obj in par_data:
        if par_obj.get('name') == 'Layeractive':
            is_active = par_obj.get('val')
            active_par_obj = par_obj
            break
    if not is_active:
        par_data = [active_par_obj]  # Only load active parameter
    return par_data
```

**File Reference**: `py_modules/layerEXT.py:76-92`

### Preset File Paths

Preset files are typically stored in:

```python
preset_path = op.project.Assets_path / f"presets/{myop.name}/presets.json"
```

**File Reference**: `py_modules/layerEXT.py:19`

### Preset Propagation

When `propagate_children=True`, presets are applied to child components:

```python
PresetBaseEXT.__init__(
    self,
    myop,
    par_mode=ParMode,
    preset_file=preset_path,
    propagate_children=True  # Apply to children
)
```

### Ignoring Children

Some children can be ignored during preset operations:

```python
self.Child_ignore_names = ['transition_layer', 'custom_layer']
```

**File Reference**: `td-modules/layers/layersEXT.py:31`

### Loading Presets

```python
def LoadPreset(self, preset_name: str) -> None:
    # Called via PresetBaseEXT
    pass

# Usage
op.layers.LoadPreset('scene-name')
op.transition_layer.LoadPreset('transition-name')
```

**File Reference**: `td-modules/scene_controller/sceneControllerEXT.py:93-97`

---

## 13. Replication Patterns

### OnReplicate Callbacks

When using replicators, extensions can implement `OnReplicate` callbacks:

```python
def OnReplicate1(self, allOps: list[OP]) -> None:
    for idx, rep_op in enumerate(allOps):
        rep_op.outputConnectors[0].connect(self.Merge_op.inputConnectors[idx + 1])
    pass
```

**File Reference**: `td-modules/layer_sync_data/layerSyncDataEXT.py:27-30`

### Replicator Setup

Replicators are typically configured in the .tox file, but extensions can interact with them:

```python
# Accessing replicator children
replicated_ops = self.Me.findChildren(name="replicated_op*")
for rep_op in replicated_ops:
    # ... configure replicated operators ...
    pass
```

### Connecting Replicated Operators

Common pattern for connecting replicated operators to merge or other operators:

```python
def OnReplicate1(self, allOps: list[OP]) -> None:
    for idx, rep_op in enumerate(allOps):
        # Connect output to merge input (offset by 1 for first input)
        rep_op.outputConnectors[0].connect(self.Merge_op.inputConnectors[idx + 1])
    pass
```

**File Reference**: `td-modules/layer_sync_data/layerSyncDataEXT.py:27-30`

---

## Quick Reference

### Common Patterns

| Pattern | Code Example |
|---|---|
| Basic Extension | `class MyEXT(BaseEXT): def __init__(self, myop): BaseEXT.__init__(self, myop, par_callback_on=True)` |
| Parameter Callback | `def _onParametername(self, par): ...` |
| Access Operator | `self.Me.op('child_name')` or `op.shortcut_name` |
| Find Children | `self.Me.findChildren(type=COMP)` |
| Create Parameter | `ParTemplate('Name', par_type='Toggle', label='Label').createPar(page)` |
| OnInit | `def OnInit(self): return True` |
| Logger | `self.Logger.debug('message')` |
| Set Shortcut | `self.Me.par.opshortcut = "name"` |

### Parameter Types

- `'Toggle'`, `'Str'`, `'Int'`, `'Float'`, `'Pulse'`
- `'Menu'`, `'File'`, `'Folder'`
- `'XY'`, `'UV'`, `'RGB'`, `'RGBA'`
- `'OP'`, `'COMP'`, `'TOP'`, `'CHOP'`, `'DAT'`

### Lifecycle Methods

- `OnInit()` - After construction
- `OnStart()` - When project starts
- `OnCreate()` - When operator created
- `OnFrameStart(frame)` - Start of each frame
- `OnFrameEnd(frame)` - End of each frame
- `OnConfigLoad()` - When config loaded
- `OnPresetLoad(preset_name)` - When preset loaded

### Common BaseEXT Parameters

- `par_callback_on=True` - Enable parameter callbacks
- `global_shortcut=False` - Set global operator shortcut
- `use_par_values_changed=False` - Use OnValuesChanged instead of OnValueChange

---

## Best Practices

### Do's

- ✅ **Do** use `ParTemplate` for creating parameters
- ✅ **Do** follow `_onParameterName` naming convention for callbacks
- ✅ **Do** use `self.Logger` for logging instead of `print()`
- ✅ **Do** handle errors gracefully with try-except blocks
- ✅ **Do** return `True` from `OnInit()` on success
- ✅ **Do** use operator shortcuts for cleaner code
- ✅ **Do** set `par_callback_on=True` when using parameter callbacks
- ✅ **Do** use type hints: `def method(self, par: Par) -> None:`
- ✅ **Do** add `# type: ignore` to TouchDesigner imports
- ✅ **Do** use `self.Me.op()` for relative operator access

### Don'ts

- ❌ **Don't** use direct `print()` - use `self.print()` or `self.Logger`
- ❌ **Don't** forget to call `super().OnInit()` when overriding
- ❌ **Don't** access operators without checking if they exist
- ❌ **Don't** hardcode paths - use `op.project.Assets_path`
- ❌ **Don't** forget error handling in callbacks
- ❌ **Don't** use inconsistent parameter naming
- ❌ **Don't** skip the `pass` statement at end of methods
- ❌ **Don't** forget to set `opshortcut` for easy access

---

## Additional Resources

- Base extension implementation: `dep/python/vvox_tdtools/base.py`
- Parameter helper: `dep/python/vvox_tdtools/parhelper.py`
- Preset base: `dep/python/vvox_tdtools/preset_base.py`
- TouchDesigner mock objects: `dep/python/vvox_tdtools/td_mock.py`

---

*This style guide is based on patterns found in the TD-GRANITE-RENDER codebase. For questions or additions, refer to existing extension files for examples.*
