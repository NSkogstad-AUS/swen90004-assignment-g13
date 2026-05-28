# NetLogo Test Inputs

Place exported NetLogo BehaviorSpace table CSV files in this folder.

The comparison script looks here by default:

```bash
cd /Users/nicolaiskogstad/PROJECTS/swen90004-assignment-g13/hotelling-law
python3 compare_netlogo_outputs.py
```

Expected BehaviorSpace setup:

- `setup commands`: `setup`
- `go commands`: `go`
- stop after `100` steps
- repetitions: `30`
- `number-of-stores = 3`
- `rules = "normal"`
- `layout = "line"` for line baseline or `layout = "plane"` for plane baseline

The script filters exported rows to:

- `layout = line` or `layout = plane`
- `number-of-stores = 3`
- `rules = normal`
- `[step] = 100`

## Line BehaviorSpace Reporters

Paste these into BehaviorSpace's reporter list for the line baseline:

```netlogo
mean [pycor] of turtles
standard-deviation [pycor] of turtles
min [pycor] of turtles
max [pycor] of turtles
mean [abs pycor] of turtles
standard-deviation [abs pycor] of turtles
min [abs pycor] of turtles
max [abs pycor] of turtles
mean [mean [distance myself] of other turtles] of turtles
standard-deviation [mean [distance myself] of other turtles] of turtles
min [mean [distance myself] of other turtles] of turtles
max [mean [distance myself] of other turtles] of turtles
mean [price * area-count] of turtles
standard-deviation [price * area-count] of turtles
min [price * area-count] of turtles
max [price * area-count] of turtles
mean [area-count] of turtles
standard-deviation [area-count] of turtles
min [area-count] of turtles
max [area-count] of turtles
```

## Plane BehaviorSpace Reporters

Paste these into BehaviorSpace's reporter list for the plane baseline:

```netlogo
mean [pycor] of turtles
standard-deviation [pycor] of turtles
min [pycor] of turtles
max [pycor] of turtles
mean [abs pycor] of turtles
standard-deviation [abs pycor] of turtles
min [abs pycor] of turtles
max [abs pycor] of turtles
mean [mean [distance myself] of other turtles] of turtles
standard-deviation [mean [distance myself] of other turtles] of turtles
min [mean [distance myself] of other turtles] of turtles
max [mean [distance myself] of other turtles] of turtles
mean [price * area-count] of turtles
standard-deviation [price * area-count] of turtles
min [price * area-count] of turtles
max [price * area-count] of turtles
mean [area-count] of turtles
standard-deviation [area-count] of turtles
min [area-count] of turtles
max [area-count] of turtles
mean [pxcor] of turtles
standard-deviation [pxcor] of turtles
min [pxcor] of turtles
max [pxcor] of turtles
mean [abs pxcor] of turtles
standard-deviation [abs pxcor] of turtles
min [abs pxcor] of turtles
max [abs pxcor] of turtles
mean [distancexy 0 0] of turtles
standard-deviation [distancexy 0 0] of turtles
min [distancexy 0 0] of turtles
max [distancexy 0 0] of turtles
```

## Outputs

After running the comparison script, generated comparison CSVs are written to:

- `../outputs/netlogo_python_line_comparison.csv`
- `../outputs/netlogo_python_plane_comparison.csv`

