def find_connected_components(nodes, adj_list):
    """Finds all connected components in a graph using a basic traversal."""
    visited = set()
    components = []
    for node in nodes:
        if node not in visited:
            component = []
            q = [node]
            visited.add(node)
            head = 0
            while head < len(q):
                u = q[head]
                head += 1
                component.append(u)
                if u in adj_list:
                    for v in adj_list[u]:
                        if v not in visited:
                            visited.add(v)
                            q.append(v)
            components.append(component)
    return components
