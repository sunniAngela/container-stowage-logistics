""" Python file to solve the csp stowage problem given a map and a list of containers"""
# CSPStowage.py \CSP-tests map1.txt containers1.txt
import sys
from constraint import *


def parser_map(map_path):
    """ Function parsers map txt file """
    try:
        with open(map_path, "r", encoding="utf-8", newline="") as file:
            data = file.readlines()
    except FileNotFoundError as ex:
        raise Exception("Wrong path or file path") from ex

    domain_standard = []
    domain_refrigerator = []
    domain_x = []

    counter_row = 0
    for line in data:
        counter_column = 0
        for c in line:
            if c == "N":
                domain_standard.append((counter_row, counter_column))
                counter_column += 1
            elif c == "E":
                domain_refrigerator.append((counter_row, counter_column))
                domain_standard.append((counter_row, counter_column))
                counter_column += 1
            elif c == "X":
                domain_x.append((counter_row, counter_column))
                counter_column += 1
        counter_row += 1

    return domain_standard, domain_refrigerator, domain_x, counter_row


def parse_containers(containers_path):
    """ Function to parse the containers file """
    try:
        with open(containers_path, "r", encoding="utf-8", newline="") as file:
            data = file.readlines()
    except FileNotFoundError as ex:
        raise Exception("Wrong path or file path") from ex

    containers_standard = []
    containers_refrigerated = []
    containers = []
    containers_destination = []

    for line in data:
        c = line.split()
        if c[1] == "S":
            containers_standard.append(c[0])
        else:
            containers_refrigerated.append(c[0])
        containers.append(c[0])
        containers_destination.append(c[2])

    return containers, containers_destination, containers_standard, containers_refrigerated


def save_output(solution, path, map_name, container_map):
    """Save the output on a txt file"""
    file = open(path + "/" + map_name + "-" + container_map + ".output", "w+")
    file.truncate()
    file.write("Number of solutions: %d\n" % len(solution))

    for s in solution:
        file.write(str(s) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise Exception("Invalid number of arguments")

    test_path = sys.argv[1]
    map_file = sys.argv[2]
    containers_file = sys.argv[3]

    domain_standard, domain_refrigerator, domain_x, depth = parser_map(test_path + "/" + map_file + ".txt")

    containers, containers_destination, containers_standard, containers_refrigerated = parse_containers(test_path + "/" + containers_file + ".txt")

    problem = Problem()

    problem.addVariables(containers_standard, domain_standard)
    problem.addVariables(containers_refrigerated, domain_refrigerator)

    # all variables have distinct values
    problem.addConstraint(AllDifferentConstraint(), containers)

    # check the container is above an X or above another container
    def on_top(*args):
        for cell in args:
            cell_below = (cell[0] + 1, cell[1])

            if cell_below not in domain_x and cell_below not in args and cell[0] != depth - 1:
                return False
        return True

    problem.addConstraint(on_top, containers)

    def port(*args):
        for i in range(len(args)):
            cell = args[i]
            dest_port_above = containers_destination[i]
            cell_below = (cell[0] + 1, cell[1])

            # if cell below is empty continue
            if cell_below not in domain_x and cell_below in args:
                dest_port_below = containers_destination[args.index(cell_below)]
                if int(dest_port_below) < int(dest_port_above):
                    return False
        return True

    problem.addConstraint(port, containers)

    save_output(problem.getSolutions(), test_path, map_file, containers_file)

