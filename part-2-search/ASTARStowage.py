""" A STAR implementation for transporting containers """
import sys
import time

LOAD_COST = 10
UNLOAD_COST = 15
SAIL_COST = 3500
PORT_LIST = ["0", "1", "2"]


class Node:
    """ class of the node """
    def __init__(self, elem):
        self.elem = elem  # tuple representing state: ([(container),(container),...], ship_current_port, ship_map)
        self.parent = None
        self.action = None
        self.h = 0
        self.g = 0

    def __eq__(self, other):
        """Method to establish two node objects are equal when their elem attribute is equal"""
        if not isinstance(other, Node):
            return NotImplemented
        else:
            return self.elem == other.elem

    def cprint(self):
        """Auxiliary method to print a node (!!cannot be the parent node)"""
        print("Containers list: ", self.elem[0])
        print("Ship current location: ", self.elem[1])
        print("Ship map: ", self.elem[2])
        print("h: " + str(self.h) + ", g: " + str(self.g)+", f: "+str(self.f)+", action: "+self.action)
        print("\n")

    @property
    def f(self):
        """Method that sets the value of the evaluating function, f(n) = h(n) + g(n)"""
        return self.h + self.g


def generate_initial(list_initial_containers, ship_map):
    """Function that generates the initial state from parsed containers output. A state has the following format
    ([(container),(container),...], ship_current_port)"""
    # ship initial port is 0
    init_state = (list_initial_containers, 0, ship_map)
    return init_state


def parse_map(file_path, map_file):
    """Function that parses the map file returning a list where each element represents a cell in the ship following
    the next structure (x, y, electrified(bool), occupied(bool))"""
    file_complete_path = file_path+"/"+map_file+".txt"
    try:
        with open(file_complete_path, "r", encoding="utf-8", newline="") as file:
            data = file.readlines()
    except FileNotFoundError as ex:
        raise Exception("Wrong path or file path") from ex

    ship_map = []
    row = 0
    for line in data:
        col = 0
        for c in line:
            if c != " ":
                if c == "N":
                    ship_map.append((row, col, False, False))
                elif c == "E":
                    ship_map.append((row, col, True, False))
                elif c == "X":
                    ship_map.append((row, col, False, True))
                col += 1
        row += 1

    return ship_map


def parse_containers(file_path, containers_file):
    """Function that parses the map file returning a list where each element represents a cell in the ship following
    the next structure (id, x, y, refrigerated(bool), location, destination)"""
    file_complete_path = file_path + "/" + containers_file + ".txt"
    try:
        with open(file_complete_path, "r", encoding="utf-8", newline="") as file:
            data = file.readlines()
    except FileNotFoundError as ex:
        raise Exception("Wrong path or file path") from ex

    list_containers = []
    # as position in port is irrelevant, x and y are set to None
    for line in data:
        c = line.split()
        if c[1] == "R":
            list_containers.append((int(c[0]), None, None, True, 0, int(c[2])))
        else:
            list_containers.append((int(c[0]), None, None, False, 0, int(c[2])))

    return list_containers


def check_goal(node):
    """ Check that an node is a goal """

    # traverse the list of containers
    for c in node.elem[0]:
        # if one is misplaced then return false
        if c[4] != c[5]:
            return False

    # if all are in the right port then return true
    return True


def generate_successors(node, type_h):
    """Returns the list of successors of node by applying all operators in every possible combination"""
    # apply sail operators
    list_successors = [sail_port0_port1(node, type_h), sail_port1_port0(node, type_h), sail_port1_port2(node, type_h),
                       sail_port2_port1(node, type_h)]

    for cont in node.elem[0]:
        # apply unload operator on all containers
        list_successors.append(unload(node, cont, type_h))

        # for cell in state's ship map
        for cell in node.elem[2]:
            # apply load operator on all combinations of containers × cells
            list_successors.append(load(node, cont, cell, type_h))

    return list_successors


def sail_port0_port1(node, type_h):
    """Operator Sail from port 0 to port 1"""
    return _sail(node, 0, 1, type_h)


def sail_port1_port0(node, type_h):
    """Operator Sail from port 1 to port 0"""
    return _sail(node, 1, 0, type_h)


def sail_port1_port2(node, type_h):
    """Operator Sail from port 1 to port 2"""
    return _sail(node, 1, 2, type_h)


def sail_port2_port1(node, type_h):
    """Operator Sail from port 2 to port 1"""
    return _sail(node, 2, 1, type_h)


def _sail(node, origin_port, destination_port, type_h):
    """Private function that takes a node, an origin and a destination port and performs the sail operator.
    Return None if cannot apply on passed node. Otherwise, return child node"""
    # operator precondition: ship current location is the origin port passed
    if isinstance(node, Node) and node.elem[1] == origin_port:
        # operator effect: ship current location changed to destination port
        new_state = (node.elem[0], destination_port, node.elem[2])
        new_node = Node(new_state)

        # set h and g, parent and action of new node
        calculate_heuristic(new_node, type_h)
        new_node.g = node.g + SAIL_COST
        new_node.parent = node
        new_node.action = "sail(" + str(origin_port) + ", " + str(destination_port) + ")"
        return new_node
    return None


def load(node, container, cell, type_h):
    """Function that applies the load operator. Returns child node or None if operator cannot be applied on parent"""
    # operator preconditions: the ship is in the port where the container is, cell is not occupied,
    # cell is electrified if container is refrigerated (implemented as not refrigerated or electrified),
    # cell below is not empty, container is not already in its dest
    if (node.elem[1] == container[4]) and (not cell[3]) and (not container[3] or cell[2]) \
            and (not _cell_below_empty(cell, node.elem[2])) and container[4] != container[5]:
        # operator effects: change location of the container (new node), update ship map
        new_ship_map = _update_cell_avail(node.elem[2], cell[0], cell[1], True)
        new_state = _change_container_location(node, container, cell[0], cell[1], "S", new_ship_map)

        # set h and g, parent and action of new node
        new_node = Node(new_state)
        calculate_heuristic(new_node, type_h)
        new_node.parent = node
        new_node.g = node.g + LOAD_COST * cell[0]
        new_node.action = "load(container"+str(container[0])+", cell("+str(cell[0])+", "+str(cell[1])+"))"
        return new_node
    return None


def unload(node, container, type_h):
    """Function that implements unload operator. Returns child node or None if operator cannot be applied on parent"""
    # operator preconditions:
    # container is on the ship, cell above it is empty
    if container[4] == "S" and _cell_above_empty(container, node.elem[2]):
        # operator effects: change cell position on ship to not occupied
        new_ship_map = _update_cell_avail(node.elem[2], container[1], container[2], False)
        # when on port (x,y) positions are set to None because irrelevant
        new_state = _change_container_location(node, container, None, None, node.elem[1], new_ship_map)

        # set h and g, parent and action of new node
        new_node = Node(new_state)
        calculate_heuristic(new_node, type_h)
        new_node.parent = node
        new_node.g = node.g + UNLOAD_COST * container[1]
        new_node.action = "unload(container" + str(container[0]) + ")"
        return new_node
    return None


def _change_container_location(node, container, new_x, new_y, new_location, new_ship_map):
    """Returns the new state with the new positions and location for the indicated container"""
    new_list_container = []
    for c in node.elem[0]:
        if c[0] == container[0]:
            # new updated container
            new_container = (container[0], new_x, new_y, container[3], new_location, container[5])
            new_list_container.append(new_container)
        else:
            new_list_container.append(c)

    new_state = (new_list_container, node.elem[1], new_ship_map)
    return new_state


def _cell_above_empty(container, ship_map):
    """Given a loaded container, returns True if cell above is empty and False otherwise"""
    for cell in ship_map:
        if cell[0] == container[1] - 1 and cell[1] == container[2]:
            return not cell[3]
    # top layer, above always empty
    return True


def _cell_below_empty(cell, ship_map):
    """Given a cell, returns True if cell below is empty and False if it is occupied"""
    for c in ship_map:
        if c[0] == cell[0] + 1 and c[1] == cell[1]:
            return not c[3]
    # cell not found means it was already at lowest level, so there is no cell below (not empty)
    return False


def _update_cell_avail(ship_map, x, y, occupied):
    """Given parent's ship map, generates a new map updating the cell in (x,y) position to change its availability"""
    new_ship_map = []
    for i in range(len(ship_map)):
        if ship_map[i][0] == x and ship_map[i][1] == y:
            # append updated cell to new map
            new_ship_map.append((x, y, ship_map[i][2], occupied))
        else:
            new_ship_map.append(ship_map[i])
    return new_ship_map


def calculate_heuristic(node, type_h):
    """ Updates the heuristic attribute of node given an heuristic type """
    # get the state of the node
    state = node.elem
    heu_value = 0

    # get the current port of the ship
    current_port = state[1]

    # get the list of containers
    containers_list = state[0]

    if type_h == "heuristic_1":
        for c in containers_list:
            # if container is misplaced increment the heuristic
            if c[4] != c[5]:
                heu_value += 1

    elif type_h == "heuristic_2":
        # max number of travels the ship should do
        max_ship_travels = 0

        for c in containers_list:
            # if container is misplaced
            if c[4] != c[5]:
                if c[4] in PORT_LIST:
                    on_port = 1
                else:
                    on_port = 0

                # location & destination of container
                location = c[4]
                destination = c[5]

                # if the location is the ship, then change the location to the current port
                if c[4] == "S":
                    location = current_port

                # compute the travels the ship should do for this container and update the max_ship_travels
                container_ship_travels = abs(location - current_port) + abs(location - destination)

                if max_ship_travels < container_ship_travels:
                    max_ship_travels = container_ship_travels

                # update heuristic value
                heu_value = heu_value + on_port*LOAD_COST + UNLOAD_COST

        heu_value = heu_value + max_ship_travels*SAIL_COST

    # update the heuristic of the node
    node.h = heu_value


def lower_f(node, list_nodes):
    """ checks if node, that is also in list_nodes, has a lower value of f than the one in list """
    # traverse the list and return true on the appearance of a node in the list equal to input node with greater f
    for n in list_nodes:
        if n == node and n.f > node.f:
            return True
    return False


def sorted_append(node, list_nodes):
    """ Adds the node in the list in the proper place (h, g, f) """
    # if the list is empty append the node
    if len(list_nodes) == 0:
        list_nodes.append(node)

    # if the list has one element look for the right place
    elif len(list_nodes) == 1:
        # if the f value is greater append at the end
        if list_nodes[0].f < node.f:
            list_nodes.append(node)

        # if the f value is lower insert at the beginning
        elif list_nodes[0].f > node.f:
            list_nodes.insert(0, node)

        # if the f values are the same check the heuristic
        else:
            # if the heuristic is greater append at the end
            if list_nodes[0].h < node.h:
                list_nodes.append(node)

            # if the heuristic is lower insert at the beginning
            else:
                list_nodes.insert(0, node)

    # if the list has more elements
    else:
        # traverse the list
        i = 0
        control = False
        while i < len(list_nodes) and not control:

            # if the f value is lower
            if node.f < list_nodes[i].f:

                # if the index is the last one insert at the end
                if i == len(list_nodes) - 1:
                    list_nodes.insert(len(list_nodes), node)
                    control = True

                # else insert in the correct place
                else:
                    list_nodes.insert(i, node)
                    control = True

            # if the f values are the same check heuristic
            elif node.f == list_nodes[i].f:

                # if the heuristic is lower insert node in the list
                if node.h < list_nodes[i].h:
                    if i == len(list_nodes) - 1:
                        list_nodes.insert(len(list_nodes), node)
                        control = True

                    else:
                        list_nodes.insert(i, node)
                        control = True

            # if the f is always greater and the place to insert it has not been found append it at the end
            if i == len(list_nodes) - 1 and control is False:
                list_nodes.append(node)
                control = True

            # if the f is greater it will continue traversing the list
            i += 1

    return list_nodes


def a_star_search(init_state, type_h):
    """ A* implementation """
    # create the initial node and update its heuristic value
    init_node = Node(init_state)
    calculate_heuristic(init_node, type_h)

    # create the open and closed node lists
    open_nodes = [init_node]
    closed_nodes = []
    # expanded nodes counter
    expanded_nodes = 0

    # loop until the open list is zero
    while len(open_nodes) != 0:
        # take the first node in the list and remove it from the list
        current_node = open_nodes[0]
        open_nodes.pop(0)

        # if the goal is reached then generate the path
        if check_goal(current_node):
            path = []

            # path is generated in the following way; the first node is the goal and the final one is the initial state
            while current_node != init_node:
                path.append(current_node)
                current_node = current_node.parent
            path.append(init_node)

            tup = (path, expanded_nodes)
            return tup

        # if the current state is not a goal
        else:
            # generate the list of nodes that are the successors of current node
            successors = generate_successors(current_node, type_h)

            # update expanded_nodes
            expanded_nodes += 1

            # append current node to closed list
            closed_nodes.append(current_node)

            for n in successors:
                # if n is not None
                if n:
                    # if the successor is not in open and not in closed
                    if n not in open_nodes and n not in closed_nodes:
                        # append in sorted way the successor
                        open_nodes = sorted_append(n, open_nodes)

                    # if the successor is in open and has lower cost
                    elif n in open_nodes and lower_f(n, open_nodes):
                        # delete node in open_nodes that has more cost
                        discard_suc = open_nodes.index(n)
                        open_nodes.pop(discard_suc)

                        # append properly in the open list
                        open_nodes = sorted_append(n, open_nodes)
    return False


def statistics_output(overall_time, solution, file_path, map_name, containers_name, h_type):
    """Save the statistics on a txt file"""
    # create the file and write in it
    file = open(file_path + "/" + map_name + "-" + containers_name + "-" + h_type + ".stat", "w+")
    file.truncate()

    if isinstance(solution, tuple):
        file.write("Overall time: %d\n" % overall_time)
        file.write("Overall cost: %d\n" % solution[0][0].g)
        file.write("Plan length: %d\n" % len(solution[0]))
        file.write("Expanded nodes: %d\n" % solution[1])

    # if solution not found
    else:
        file.write("SOLUTION NOT FOUND")
    file.close()


def actions_output(solution, file_path, map_name, containers_name, heuristic_type):
    """Save the actions and the nodes into a file"""
    # open the output file
    file = open(file_path + "/" + map_name + "-" + containers_name + "-" + heuristic_type + ".output", "w+")
    file.truncate()

    if isinstance(solution, tuple):
        # traverse the list of the path from the end to the beginning
        # the last node in the list is the initial, it is not taken into account when printing the result
        current_index = len(solution[0]) - 2

        ind = 1
        while current_index >= 0:
            file.write(str(ind) + ". " + solution[0][current_index].action + "\n")
            current_index -= 1
            ind += 1

    # if solution not found
    else:
        file.write("SOLUTION NOT FOUND")

    file.close()


def main():
    # get the input arguments
    file_path = sys.argv[1]
    map_file = sys.argv[2]
    containers_file = sys.argv[3]
    heuristic_type = sys.argv[4]

    # parsed the map of the ship and the containers lists
    ship_map = parse_map(file_path, map_file)
    list_containers = parse_containers(file_path, containers_file)

    # generate the initial state
    init_state = generate_initial(list_containers, ship_map)

    # execute the A* algorithm
    start_t = time.time()
    solution_search = a_star_search(init_state, heuristic_type)
    end_t = time.time()

    # time in milliseconds
    overall_time = (end_t - start_t)*1000

    # save the outputs of the program
    actions_output(solution_search, file_path, map_file, containers_file, heuristic_type)
    statistics_output(overall_time, solution_search, file_path, map_file, containers_file, heuristic_type)


main()
