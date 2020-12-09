from queue import PriorityQueue

class Variable:
    def __init__(self, name, domain, value=None):
        self.name = name
        self.domain = domain
        self.value = value
    
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        if v is not None and v not in self.domain:
            raise Exception(f"assigned value {v} is not in domain {self.domain}")
        self._value = v

    def __repr__(self):
        return self.name

class DecisionVariable(Variable):
    def __init__(self, name, value=None):
        super().__init__(name, {'G', 'U'}, value)


class ANDVariable(DecisionVariable):
    def __init__(self, name, value=None, success_probability=0.98):
        super().__init__(name, value)
        self.success_probability = success_probability

class XORVariable(DecisionVariable):
    def __init__(self, name, value=None, success_probability=0.97):
        super().__init__(name, value)
        self.success_probability = success_probability


class Model:
    def __init__(self, *variables):
        self.variables = list(variables)
        self.constraints = []


    def add_components(self, var, inputs, output):
        if isinstance(var, ANDVariable):
            return self._add_ANDVariable(var, inputs, output)
        elif isinstance(var, XORVariable):
            return self._add_XORVariable(var, inputs, output)
        # TODO: add support for other gates


    def _add_ANDVariable(self, var, inputs, output):
        # NOTE: currently this is written so that it's possible
        # to have more than just two inputs to the AND gate
        #
        # could easily write this to be hard coded
        # so that it's more consistent with the XOR func
        constraints = []
        constraint_all = {var:'U', output:1}
        constraint_pair = {var:'U', output:0}
        for inp in inputs:
            constraint_all[inp] = 0
            pair = constraint_pair.copy()
            pair[inp] = 1
            constraints.append(pair)
        constraints.append(constraint_all)
        
        self.constraints.extend(constraints)
        return constraints


    def _add_XORVariable(self, var, inputs, output):
        in1, in2 = inputs[0], inputs[1]
        assert len(inputs)==2
        constraints = [
            {var:'U', output:1, in1:1, in2:0},
            {var:'U', output:1, in1:0, in2:1},
            {var:'U', output:0, in1:1, in2:1},
            {var:'U', output:0, in1:0, in2:0}
        ]
        self.constraints.extend(constraints)
        return constraints
    

    def propagate_assignments(self, assignments, constraints):
        updated_constraints = []
        for clause in constraints:
            # print(f"Checking clause {clause}")
            clause_satisfied = False
            updated_clause = dict()
            for literal, val in clause.items():
                # print(f"\tChecking literal {literal}={val}")
                if literal in assignments:
                    if assignments[literal] == val:
                        # print(f"\t\tLiteral True- Clause Satisfied")
                        # clause satisfied, don't add clause
                        clause_satisfied = True
                        break
                    else:
                        # print("\t\tLiteral False, next literal")
                        # literal is false, check next literals
                        continue
                else:
                    # print(f"\t\tLiteral not in assignments, add to clause")
                    updated_clause[literal] = val
            
            if not clause_satisfied:
                if len(updated_clause) != 0:
                    # print(f"Updated clause adding to constraints: {updated_clause}")
                    updated_constraints.append(updated_clause)
                    # print(f"Updated constraints: {updated_constraints}\n")
                else:
                    return None

        return updated_constraints


    def DPLL(self, assignments):
        # get assigned vars together
        a = assignments.copy()
        for v in self.variables:
            if v.value is not None:
                a[v] = v.value

        return self.DPLL_recurs(a, self.constraints)


    def DPLL_recurs(self, assignments, constraints, conflicts=dict()):
        updated_constraints = self.propagate_assignments(assignments, constraints)
        conflicts.update(assignments)
        if updated_constraints is None:
            # conflicts.update(assignments)
            return False, conflicts
        if len(updated_constraints) == 0:
            return True, None
        # to find pure literals, do (literals_0 union literals_1) minus (literals_0 intersect literals_1)
        # is there a cleaner way to do this?
        literals_0 = set()
        literals_1 = set() 
        # look for unit clauses while also gathering info to check for pure literals
        for clause in updated_constraints:
            if len(clause) == 1:
                # unit clause, recurse
                v = list(clause.keys())[0]

                return self.DPLL_recurs({v:clause[v]}, updated_constraints, conflicts)
            for l in clause.keys():
                if clause[l] == 0:
                    literals_0.add(l)
                else:
                    literals_1.add(l)
        # Are there any pure literals? if so, choose one and recurse
        pure_literal_set = literals_0.union(literals_1) - literals_0.intersection(literals_1)
        if len(pure_literal_set) != 0:
            # choose one of the pure literals to propagate
            pure_literal = pure_literal_set.pop()
            if pure_literal in literals_0:
                return self.DPLL_recurs({pure_literal:0}, updated_constraints, conflicts)
            else:
                return self.DPLL_recurs({pure_literal:1}, updated_constraints, conflicts)

        # No unit clauses and no pure literals to propagate
        # Choose random (first) literal, propagate both both 1 and 0
        literal = list(updated_constraints[0].keys())[0]
        return self.DPLL_recurs({literal:0}, updated_constraints) or self.DPLL_recurs({literal:1}, updated_constraints)
    

    def supported_propagation(self, assignments, constraints, support=[]):
        # might not need to return assignments and constraints here
        # (useful for debugging tho)
        constraints = self.propagate_assignments(assignments, constraints)
        if constraints is None:
            return False, assignments, constraints, support
        for clause in constraints:
            if len(clause) == 1:
                # TODO: FIX! This is not correct
                support.append(assignments)
                updated_constraints = self.propagate_assignments(clause, constraints)
                if updated_constraints is None:
                    return False, assignments, constraints, support
                return self.supported_propagation(clause, updated_constraints, support)

        return True, assignments, constraints, support


class OCSP:
    def __init__(self, decision_variables, rankings, model):
        self.decision_variables = decision_variables
        self.rankings = rankings
        self.model = model
        

    def calculate_heuristic_value(self, assignments):
        g = 1
        h = 1
        for var in self.decision_variables:
            if var in assignments.keys():
                prob = var.success_probability if assignments[var] == 'G' else 1 - var.success_probability
                g *= prob
            else:
                # assuming P(var = 'G') is always greater than P(var = 'U'), we could just set this to P(var = 'G') 
                prob = max([var.success_probability, 1-var.success_probability])
                h *= prob

        '''
        lecture slides show these being added, but other notes show it being multiplied:
        If we take the log of this equation, which is a monotonic function and wouldn’t
        change the ordering of nodes picked off the Queue, it is in the form of g + h
        but multiplying is more convinient since they are probabilities
        '''
        # TODO: look more into this^^
        return g*h


    def ConstraintBasedAstar(self):
        decision_vars = self.decision_variables
        # PriorityQueue giving weird error, doing naive list for now
        Q = PriorityQueue(order=max, f= lambda x: self.calculate_heuristic_value(x))
        Q.append(dict())
        # Q = []
        # Q.append((0, dict()))
        expanded = []
        while len(Q) != 0:
            assignment = Q.pop()  #[1]
            expanded.append(assignment)
            if all(var in assignment.keys() for var in decision_vars):
                # Complete assignment, check consistency with all variables
                if self.model.DPLL(assignment)[0]:
                    return assignment
            else:
                # Partial assignment, expand and add to queue
                # find a better way to do this (also want to check for expansion order)
                for var in self.rankings:
                    if var not in assignment.keys():
                        x_i = var
                        break

                # if z = {**x, **y}, z is a shallow copy of x updated with the values of y
                good_expansion = {**assignment, **{x_i:'G'}}
                unknown_expansion = {**assignment, **{x_i:'U'}}
                if good_expansion not in expanded:
                    # heur = self.calculate_heuristic_value(good_expansion)
                    # Q.append(good_expansion)
                    # if len(Q) == 0:
                    #     Q.append((heur, good_expansion))
                    # else:
                    #     for i, (h, _) in enumerate(Q.copy()):
                    #         if heur < h:
                    #             Q.insert(i, (heur, good_expansion))
                    #             break
                    #         elif i == len(Q) - 1:
                    #             Q.append((heur, good_expansion))
                    Q.append(good_expansion)
                if unknown_expansion not in expanded:
                    # heur = self.calculate_heuristic_value(unknown_expansion)
                    # if len(Q) == 0:
                    #     Q.append((heur, unknown_expansion))
                    # else:
                    #     for i, (h, _) in enumerate(Q.copy()):
                    #         if heur < h:
                    #             Q.insert(i, (heur, unknown_expansion))
                    #             break
                    #         elif i == len(Q) - 1:
                    #             Q.append((heur, unknown_expansion))
                    Q.append(unknown_expansion)
        return None
    

    def ConflictDirectedAstar(self):
        decision_vars = self.decision_variables
        # PriorityQueue giving weird error, doing naive list for now
        Q = PriorityQueue(order=max, f= lambda x: self.calculate_heuristic_value(x))
        Q.append(dict())
        # Q = []
        # Q.append((0, dict()))
        expanded = []
        constituents = []

        a = dict()
        for v in self.model.variables:
            if v.value is not None:
                a[v] = v.value
        constraints = self.model.propagate_assignments(a, self.model.constraints)
        if constraints is None:
            # This shouldn't ever get here
            return None

        while len(Q) != 0:
            assignment = Q.pop()  #[1]
            expanded.append(assignment)
            if all(var in assignment.keys() for var in decision_vars):
                # Complete assignment, check consistency with all variables
                consistent, _, _, conflict = self.model.supported_propagation(assignment, constraints)
                if consistent:
                    return assignment
                
                # TODO: FIX! This isn't really right
                conflict = conflict[0]
                constituent = conflict.copy()
                for var, assign in constituent.items():
                    constituent[var] = 'G' if assign == 'U' else 'U'
                constituents.append(constituent)
                
            else:
                # Partial assignment, expand and add to queue
                # see if assignment resolves all constituents
                constituents = self.model.propagate_assignments(assignment, constituents)
                if constituents is not None and len(constituents) == 0:
                    # find a better way to do this (also want to check for expansion order)
                    for var in self.rankings:
                        if var not in assignment.keys():
                            x_i = var
                            break

                    # if z = {**x, **y}, z is a shallow copy of x updated with the values of y
                    good_expansion = {**assignment, **{x_i:'G'}}
                    unknown_expansion = {**assignment, **{x_i:'U'}}
                    if good_expansion not in expanded:
                        # heur = self.calculate_heuristic_value(good_expansion)
                        # # Eventually move this to its own function, and
                        # # back to using a binary heap to speed up
                        # if len(Q) == 0:
                        #     Q.append((heur, good_expansion))
                        # else:
                        #     for i, (h, _) in enumerate(Q.copy()):
                        #         if heur < h:
                        #             Q.insert(i, (heur, good_expansion))
                        #             break
                        #         elif i == len(Q) - 1:
                        #             Q.append((heur, good_expansion))
                        Q.append(good_expansion)
                    if unknown_expansion not in expanded:
                        # heur = self.calculate_heuristic_value(unknown_expansion)
                        # if len(Q) == 0:
                        #     Q.append((heur, unknown_expansion))
                        # else:
                        #     for i, (h, _) in enumerate(Q.copy()):
                        #         if heur < h:
                        #             Q.insert(i, (heur, unknown_expansion))
                        #             break
                        #         elif i == len(Q) - 1:
                        #             Q.append((heur, unknown_expansion))
                        Q.append(unknown_expansion)
                else:
                    # TODO: I don't think this is right either
                    for constituent in constituents:
                        for var, assign in constituent.items():
                            if var not in assignment:
                                expansion = {**assignment, **{var:assign}}
                                # heur = self.calculate_heuristic_value(expansion)
                                # if len(Q) == 0:
                                #     Q.append((heur, expansion))
                                # else:
                                #     for i, (h, _) in enumerate(Q.copy()):
                                #         if heur < h:
                                #             Q.insert(i, (heur, expansion))
                                #             break
                                #         elif i == len(Q) - 1:
                                #             Q.append((heur, expansion))
                                Q.append(expansion)
        return None


if __name__ == '__main__':
    # Boolean Polycell
    A = Variable('A', {0, 1}, 1)
    B = Variable('B', {0, 1}, 1)
    C = Variable('C', {0, 1}, 1)
    D = Variable('D', {0, 1}, 0)
    E = Variable('E', {0, 1}, 1)

    X = Variable('X', {0, 1})
    Y = Variable('Y', {0, 1})
    Z = Variable('Z', {0, 1})

    F = Variable('F', {0, 1}, 0)
    G = Variable('G', {0, 1}, 1)

    A1 = ANDVariable('A1', success_probability=0.96)
    A2 = ANDVariable('A2', success_probability=0.95)
    A3 = ANDVariable('A3', success_probability=0.97)

    X1 = XORVariable('X1', success_probability=0.98)
    X2 = XORVariable('X2', success_probability=0.99)

    m = Model(A1, A2, A3, X1, X2, A, B, C, D, E, F, G, X, Y, Z)
    m.add_components(A1, [A, C], X)
    m.add_components(A2, [B, D], Y)
    m.add_components(A3, [C, E], Z)
    m.add_components(X1, [X, Y], F)
    m.add_components(X2, [Y, Z], G)

    ocsp = OCSP([A1, A2, A3, X1, X2], [A1, A2, A3, X1, X2], m)

    print(ocsp.ConstraintBasedAstar())
    print(ocsp.ConflictDirectedAstar())
