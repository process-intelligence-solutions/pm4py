import os
import networkx as nx
import time
import requests
import importlib.util
from copy import deepcopy


REMOVE_DEPS_AT_END = True
UPDATE_DOCKERFILE = True
UPDATE_OTHER_FILES = True
INCLUDE_BETAS = False


def get_version(package):
    url = "https://pypi.org/project/" + package
    r = requests.get(url)
    res0 = r.text
    res = res0.split("<p class=\"release__version\">")[1:]
    version = ""
    i = 0
    while i < len(res):
        if "pre-release" not in res[i] or INCLUDE_BETAS:
            version = res[i].split("</p>")[0].strip().split(" ")[0].strip()
            break
        i = i + 1
    license0 = res0.split("<p><strong>License:</strong>")[1].split("</p>")[0].strip()
    license0 = license0.replace("(c)", "").split(" (")

    license = license0[0]
    for i in range(1, len(license0)):
        if "..." not in license0[i]:
            license += " (" + license0[i]

    time.sleep(0.1)
    return package, url, version, license


def elaborate_single_python_package(package_name, deps, include_self=False):
    os.system("pipdeptree -p "+package_name+" >deps.txt")

    F = open("deps.txt", "r")
    content = F.readlines()
    F.close()

    if REMOVE_DEPS_AT_END:
        os.remove("deps.txt")

    G = nx.DiGraph()
    i = 1
    dep_level = {}
    blocked = False
    blocked_level = -1
    while i < len(content):
        row = content[i].split("- ")
        level = round(len(row[0]) / 2)
        dep = row[1].split(" ")[0]
        if blocked and blocked_level == level:
            blocked = False
        if dep == "pm4pycvxopt":
            blocked = True
            blocked_level = level
        if not blocked:
            dep_level[level] = dep
            if level > 1:
                G.add_edge(dep_level[level - 1], dep_level[level])
            else:
                G.add_node(dep_level[level])
        i = i + 1
    edges = list(G.edges)
    while len(edges) > 0:
        left = set(x[0] for x in edges)
        right = set(x[1] for x in edges)
        diff = sorted([x for x in right if x not in left])
        for x in diff:
            if not x in deps:
                deps.append(x)
            G.remove_node(x)
        edges = list(G.edges)
    nodes = sorted(list(G.nodes))
    for x in nodes:
        if not x in deps:
            deps.append(x)

    if "cvxopt" in deps:
        del deps[deps.index("cvxopt")]

    if include_self:
        if package_name not in deps:
            deps.append(package_name)

    deps = sorted(deps, key=lambda x: x.lower())

    return deps


def get_all_third_party_dependencies(package_name, deps, packages_dictio, include_self=False):
    deps = elaborate_single_python_package(package_name, deps, include_self=include_self)
    packages = []
    for x in deps:
        if x not in packages_dictio:
            packages_dictio[x] = get_version(x)
        packages.append(packages_dictio[x])
    return deps, packages


deps = []
packages_dictio = {}
deps, packages = get_all_third_party_dependencies("pm4py", deps, packages_dictio, include_self=False)

if UPDATE_OTHER_FILES:
    F = open("../requirements_complete.txt", "w")
    for x in packages:
        """if x[0] == "numpy":
            F.write("%s<2\n" % (x[0]))
        elif x[0] == "pandas":
            F.write("%s<3\n" % (x[0]))
        else:
            F.write("%s\n" % (x[0]))"""
        F.write("%s\n" % (x[0]))
    F.close()
    F = open("../requirements_stable.txt", "w")
    for x in packages:
        F.write("%s==%s\n" % (x[0], x[2]))
    F.close()
    F = open("LICENSES_TRANSITIVE.md", "w")
    F.write("""# PM4Py Third Party Dependencies
    
    PM4Py depends on third party libraries to implement some functionality. This document describes which libraries
    PM4Py depends upon. This is a best effort attempt to describe the library's dependencies, it is subject to change as
    libraries are added/removed.
    
    | Name | URL | License | Version |
    | --------------------------- | ------------------------------------------------------------ | --------------------------- | ------------------- |
    """)
    for x in packages:
        F.write("| %s | %s | %s | %s |\n" % (x[0].strip(), x[1].strip(), x[3].strip(), x[2].strip()))
    F.close()

prev_deps = deepcopy(packages)

extra_packages = ["requests", "pyvis", "jsonschema", "workalendar", "scikit-learn", "openai"]
for ep in extra_packages:
    if importlib.util.find_spec(ep):
        deps, packages = get_all_third_party_dependencies(ep, deps, packages_dictio, include_self=True)

first_line_packages = ["deprecation", "packaging", "networkx", "graphviz", "six", "python-dateutil", "pytz", "tzdata", "intervaltree", "sortedcontainers", "wheel", "setuptools"]
second_line_packages = ["pydotplus", "pyparsing", "tqdm", "colorama", "cycler", "joblib", "threadpoolctl"]
third_line_packages = ["lxml", "numpy", "pandas", "scipy"]

first_packages_line = ""
second_packages_line = ""
third_packages_line = ""
fourth_package_line = ""
fifth_package_line = ""
sixth_package_line = ""

for x in packages:
    cont = x[0] + "==" + x[2] + " "
    if x[0] in first_line_packages:
        first_packages_line += cont
    elif x[0] in second_line_packages:
        second_packages_line += cont
    elif x[0] in third_line_packages:
        third_packages_line += cont
    elif x in prev_deps:
        fourth_package_line += cont
    elif x[0] in extra_packages:
        sixth_package_line += cont
    else:
        fifth_package_line += cont

F = open("../Dockerfile", "r")
dockerfile_contents = F.readlines()
F.close()

before_lines = []
after_lines = []
found_line = False

i = 0
while i < len(dockerfile_contents):
    if dockerfile_contents[i].startswith("RUN pip3 install") and not "-U" in dockerfile_contents[i]:
        found_line = True
    elif found_line:
        after_lines.append(dockerfile_contents[i])
    else:
        before_lines.append(dockerfile_contents[i])
    i = i + 1

stru = "".join(before_lines + ["RUN pip3 install " + x + "\n" for x in [first_packages_line, second_packages_line, third_packages_line, fourth_package_line, fifth_package_line, sixth_package_line]] + after_lines)
stru = stru.strip() + "\n"

if UPDATE_DOCKERFILE:
    F = open("../Dockerfile", "w")
    F.write(stru)
    F.close()
else:
    print(stru)
