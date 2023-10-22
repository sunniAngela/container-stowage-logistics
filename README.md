# container-stowage-logistics
Giving a glimpse into the intricacies of maritime logistics and container stowage, this project was developed as part of a Heuristics and Optimization course, with the goal of learning to model and solve constraint satisfaction and heuristic search tasks.

Stowage is the strategic arrangement and placement of cargo within a ship's hold to optimize space utilization and ensure safe and efficient unloading at destination ports. For this project, we focus on vessels with a single loading bay, where each cell accommodates one container. We handle two container types: 
- Standard, which can occupy any available cell as long as it's at the bottom of the stack or is placed on top of an occupied cell.
- Refrigerated, reserved for perishable cargo and requires specific power-supplied cells, in addition to the restrictions of a standard container. 

Each container is identified with an ID, destination port, and refrigeration indicator upon arrival at the departure port.

## Authors
- sunniAngela
- Jdelpinov

## Part 1: Validation with Python constraint
Considering a single loading bay and two destination ports, the goal is to determine if it's possible to stow containers complying with the storage restrictions, and unload the cargo at port 1 and, then, at port 2 without repositioning any containers. The problem is modeled as a constraint satisfaction problem (CSP) in Python using the library *python-constraint*. 

Input data includes the loading bay map and the list of containers at the departure port, which will be provided in text files, following the next example. 

- Loading bay map:
```console
N N N N
N N N N
E N N E
X E E X
X X X X
```
- List of containers:
```console 
1 S 1
2 S 1
3 S 1
4 R 2
5 R 2 
```

Where the letters represent:
- N: Normal cell
- E: Cell with energy (power supply)
- X: No available position
- S: Standard container
- R: Refrigerated container

### Execution
The program must be run from a console or terminal with the following command:
```console
python CSPStowage.py <path> <map> <containers>
```
Where `path` defines the path where the files are located, and `map` and `containers` are the names of the corresponding input files.
The program generates an output file in the same directory. The first line in the output file indicates the number of solutions found, and then all the solutions to the problem, one per line. In each solution, the cell corresponding to each container will be expressed in the following format: *container-id*: (*stack*, *depth*). 

A possible example of the content of the output file would be the following:
```console
Number of solutions: 21
{3: (3, 2), 1: (3, 1), 4: (2, 3), 0: (3, 0), 2: (2, 2)}
...
```

Where, the first solution corresponds to the following distribution of containers:
```console
N N N 0
N N N 1
E N 2 3
X E 4 X
X X X X 
```

## Part 2: Heuristic Search
The second part builds the complete planning for loading and unloading the containers by establishing the sequence of actions that allows all containers to be moved to their destination port.  It is assumed that all containers start in the *home* port, and can be *loaded* in the loading bay in any order. Containers can be *unloaded* at their destination port or at any other port, if necessary for relocating them. In addition, it is necessary to consider the *trips* of the ship, as we want to optimize the total cost.

The movements of a container have a fixed cost and a variable cost (∆), which represents the number of cells in height that a container has to travel. The individual cost of the actions is calculated as follows:

| Action |   Cost   |
| ------ | ------   |
| load   | 10 + ∆   |
| unload | 15 + 2∆  |
| sail   | 3500     |

This problem is modeled as a search problem and uses the A\* algorithm and two different heuristic functions. 

### Misplaced containers heuristic
The first heuristic evaluates each state by the number of misplaced containers, so that each misplaced one increments the value by one. This heuristic is actually poorly informed as the numbers are far from the actual costs. The value for the goal state will be clearly 0 and for the initial state, the total number of containers. 
$$h1\left( n\right) = m$$

Where 𝑚 is the number of misplaced containers. 

### Furthest container heuristic
In the second heuristic, we wanted to make just a few relaxations on the real problem. We omitted the height increment used to calculate the load and unload costs, and assumed that, on the trip to get one of these containers to its port, we can leave all others containers in theirs, too. To choose exactly one of them, we deemed best the one that needed to sail the furthest (more informative). The heuristic will never overestimate the cost because, for each particular state, it will always need to sail at least that many times to reach the goal state. Thus, the heuristic is admissible.
$$h2\left( n\right) = \left( \sum_{i=1}^{m} on\_port \cdot 10 + 15 \right) + max(|location_i - current\_port+location_i - destination_i|) \cdot 3500$$

, where *on_port* is 1 if that container is in a port, and 0 if it is on the ship. *current_port* is the port where the container is or, otherwise, the port where the ship is.

### Execution
It must be run from a console or terminal with the following command:
```console
./ASTARStowage.sh <path> <map> <containers> <heuristic>
```

Where `path` defines the path where the files are located, `map` and `containers` are the names of the corresponding input files, and `heuristic` can be set to either *heuristic_1* oe *heuristic_2*. 

The program generates two output files, one containing the sequence of operations that constitutes the solution (```.output```) and the other one shows some statistics to analyze the performance (```.stat```), including time, cost, length, and expanded nodes.


## Files and Directory Structure
The project directory is organized as follows:
- **part-1-CSP/**: Contains the files for the first part of the project.
	- **CSPStowage.py**: Main program.
    - **CSP-calls.sh**: Script including the calls to the program to run the test cases.
    - **CSP-tests/**: Directory containing the example test files containing five bay maps and six container lists.
- **part-2-search/**:  Contains the files for the second part of the project.
	- **ASTARStowage.py**: Main program.
    - **ASTARStowage.sh**: Script to invoke the developed program.
	- **ASTARStcalls.sh**: Script including the calls to the program to run the test cases.
    - **ASTAR-tests/**: Directory containing the example test files containing five bay maps and six container lists.
