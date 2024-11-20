from typing import Set
from pm4py.objects.dcr.obj import DcrGraph


class DistributedDcrGraph(DcrGraph):
    """
    A class representing a Role-based DCR graph.

    This class wraps around a DCR graph structure, extending it with role-based features such as principals,
    distributed, role assignments, and principals assignments. It provides an interface to integrate distributed into the
    DCR model and to compute role-based constraints as part of the graph.
    Attributes derived according to dcr graphs with distributed in [1]_.

    References
    ----------
    .. [1] Thomas T. Hildebrandt and Raghava Rao Mukkamala, "Declarative Event-BasedWorkflow as Distributed Dynamic Condition Response Graphs",
      Electronic Proceedings in Theoretical Computer Science — 2011, Volume 69, 59–73. `DOI <10.4204/EPTCS.69.5>`_.

    Parameters
    ----------
    g : DCRGraph
        The underlying DCR graph structure.
    template : dict, optional
        A template dictionary to initialize the distributed and assignments from, if provided.

    Attributes
    ----------

    self.__g : DCRGraph
        The underlying DCR graph structure.
    self.__principals : Set[str]
        A set of principal identifiers within the graph.
    self.__roles : Set[str]
        A set of role identifiers within the graph.
    self.__roleAssignments : Dict[str, Set[str]]
        A dictionary where keys are activity identifiers and values are sets of distributed assigned to those activities.
    self.__principalsAssignment : Dict[str, Set[str]]
        A dictionary where keys are activity identifiers and values are sets of principals assigned to those activities.

    Methods
    -------
    getConstraints() -> int:
        Computes the total number of constraints in the DCR graph, including those derived from role assignments.

    Examples
    --------
    dcr_graph = DCRGraph(...)\n
    role_graph = RoleDCR_Graph(dcr_graph, template={\n
        "principals": {"principal1", "principal2"},\n
        "roles": {"role1", "role2"},\n
        "roleAssignments": {"activity1": {"role1"}},\n
        "principalsAssignments": {"activity1": {"principal1"}}\n
    })\n

    \nAccess role-based attributes\n
    principals = role_graph.principals\n
    roles = role_graph.distributed\n
    role_assignments = role_graph.roleAssignments\n
    principals_assignment = role_graph.principalsAssignment\n

    \nCompute the number of constraints\n
    total_constraints = role_graph.getConstraints()\n

    """
    def __init__(self, template=None):
        super().__init__(template)
        self.__principals = set() if template is None else template.pop("principals", set())
        self.__roles = set() if template is None else template.pop("roles", set())
        self.__roleAssignments = {} if template is None else template.pop("roleAssignments", set())
        self.__principalsAssignments = {} if template is None else template.pop("principalsAssignments", set())

    def obj_to_template(self):
        res = super().obj_to_template()
        res['principals'] = self.__principals
        res['roles'] = self.__roles
        res['roleAssignments'] = self.__roleAssignments
        res['principalsAssignment'] = self.__principalsAssignments
        return res

    @property
    def principals(self) -> Set[str]:
        return self.__principals

    @property
    def roles(self):
        return self.__roles

    @property
    def role_assignments(self):
        return self.__roleAssignments

    @property
    def principals_assignments(self):
        return self.__principalsAssignments

    def get_constraints(self):
        """
        compute role assignments as constraints in DCR Graph
        and the constraints in the underlying graph

        Returns
        -------
        int
            number of constraints in dcr graph
        """
        no = super().get_constraints()
        for i in self.__roleAssignments.values():
            no += len(i)
        return no

    def __repr__(self):
        string = str(super())
        for key, value in vars(self).items():
            if value is super():
                continue
            string += str(key.split("_")[-1])+": "+str(value)+"\n"
        return string

    def __getattr__(self, name):
        return getattr(super(), name)

    def __getitem__(self, item):
        if hasattr(super(), item):
            return super().__getitem__(item)
        for key, value in vars(self).items():
            if item == key.split("_")[-1]:
                return value
        return set()
