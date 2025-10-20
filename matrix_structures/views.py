from django.shortcuts import render
from django import forms
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, base64, re

# ============================
# === FORMULAIRE ARBRE SIMPLE
# ============================

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, base64, re
import networkx as nx
from django import forms
from django.shortcuts import render


# ================================
# === FORMULAIRE POUR L’ABR =====
# ================================

class BSTForm(forms.Form):
    values = forms.CharField(
        label="Valeurs initiales de l’arbre binaire (ex: 8,3,10,1,6,14,4,7,13)",
        widget=forms.TextInput(attrs={'placeholder': 'Ex : 8,3,10,1,6,14,4,7,13'})
    )
    add_value = forms.IntegerField(
        label="Ajouter un nœud", required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Valeur à insérer'})
    )
    search_value = forms.IntegerField(
        label="Rechercher une valeur", required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Valeur à rechercher'})
    )
    delete_value = forms.IntegerField(
        label="Supprimer une valeur", required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Valeur à supprimer'})
    )


# ====================================
# === STRUCTURE : ARBRE BINAIRE ======
# ====================================

class Node:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None


def insert(root, key):
    if root is None:
        return Node(key)
    if key < root.key:
        root.left = insert(root.left, key)
    elif key > root.key:
        root.right = insert(root.right, key)
    return root


def delete(root, key):
    if root is None:
        return root
    if key < root.key:
        root.left = delete(root.left, key)
    elif key > root.key:
        root.right = delete(root.right, key)
    else:
        # cas trouvé
        if root.left is None:
            return root.right
        elif root.right is None:
            return root.left
        min_node = minValueNode(root.right)
        root.key = min_node.key
        root.right = delete(root.right, min_node.key)
    return root


def minValueNode(node):
    current = node
    while current.left:
        current = current.left
    return current


def inorder(root):
    return inorder(root.left) + [root.key] + inorder(root.right) if root else []


def bst_to_edges(root):
    edges = []
    if root:
        if root.left:
            edges.append((root.key, root.left.key))
            edges += bst_to_edges(root.left)
        if root.right:
            edges.append((root.key, root.right.key))
            edges += bst_to_edges(root.right)
    return edges


def height(root):
    if not root:
        return 0
    return 1 + max(height(root.left), height(root.right))


# ====================================
# === VUE PRINCIPALE DE L’ABR ========
# ====================================

def tree_view(request):
    form = BSTForm(request.POST or None)
    graph_img = None
    message = ""
    props = {}

    if request.method == "POST" and form.is_valid():
        values = [int(v.strip()) for v in re.split('[,; ]+', form.cleaned_data['values']) if v.strip().isdigit()]
        root = None
        for v in values:
            root = insert(root, v)

        action = request.POST.get("action")

        if action == "add":
            val = form.cleaned_data['add_value']
            if val is not None:
                if val in inorder(root):
                    message = f"⚠️ La valeur {val} existe déjà."
                else:
                    root = insert(root, val)
                    message = f"✅ Valeur {val} ajoutée à l’arbre."
            color_map = lambda n: "lightgreen" if n == val else "skyblue"

        elif action == "search":
            val = form.cleaned_data['search_value']
            found = val in inorder(root)
            message = f"✅ La valeur {val} existe dans l’arbre." if found else f"❌ La valeur {val} n’existe pas."
            color_map = lambda n: "lightgreen" if n == val else "skyblue"

        elif action == "delete":
            val = form.cleaned_data['delete_value']
            if val in inorder(root):
                root = delete(root, val)
                message = f"🗑️ Valeur {val} supprimée."
            else:
                message = f"⚠️ Valeur {val} introuvable."
            color_map = lambda n: "skyblue"

        else:
            color_map = lambda n: "skyblue"

        # === Dessin du graphe ===
        edges = bst_to_edges(root)
        G = nx.DiGraph()
        G.add_edges_from(edges)

        pos = hierarchy_pos(G, root.key)
        plt.figure(figsize=(8, 6))
        nx.draw(G, pos, with_labels=True,
                node_color=[color_map(n) for n in G.nodes()],
                node_size=1500, font_size=10)
        plt.title("Arbre Binaire de Recherche (ABR)")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        graph_img = base64.b64encode(buf.read()).decode("utf-8")
        plt.close()

        # === Propriétés ===
        if root:
            vals = inorder(root)
            props = {
                "Nombre de nœuds": len(vals),
                "Hauteur": height(root),
                "Minimum": min(vals),
                "Maximum": max(vals),
                "Parcours In-Order": ", ".join(map(str, vals))
            }

    return render(request, "matrix_structures/tree_view.html", {
        "form": form,
        "graph_img": graph_img,
        "props": props,
        "message": message
    })

# ======================================
# === POSITION HIÉRARCHIQUE (dessin) ===
# ======================================

def hierarchy_pos(G, root, width=1., vert_gap=0.2, vert_loc=0, xcenter=0.5):
    pos = {}
    def _hierarchy_pos(G, node, left, right, vert_loc, pos):
        pos[node] = ((left + right) / 2, vert_loc)
        neighbors = list(G.neighbors(node))
        if len(neighbors) == 2:
            _hierarchy_pos(G, neighbors[0], left, (left + right) / 2, vert_loc - vert_gap, pos)
            _hierarchy_pos(G, neighbors[1], (left + right) / 2, right, vert_loc - vert_gap, pos)
        elif len(neighbors) == 1:
            _hierarchy_pos(G, neighbors[0], left, right, vert_loc - vert_gap, pos)
        return pos
    return _hierarchy_pos(G, root, 0, width, vert_loc, pos)

# ====================================
# === FORMULAIRE POUR LES GRAPHES ====
# ====================================

class GraphChoiceForm(forms.Form):
    edges = forms.CharField(
        label="Arêtes du graphe (ex: A-B,B-C,C-D)",
        widget=forms.TextInput(attrs={'placeholder': 'Ex : A-B,B-C,C-D'})
    )
    GRAPH_TYPES = [
        ('non_oriente', 'Non orienté'),
        ('oriente', 'Orienté'),
    ]
    graph_type = forms.ChoiceField(
        label="Type de graphe",
        choices=GRAPH_TYPES,
        widget=forms.RadioSelect
    )

def graph_view(request):
    form = GraphChoiceForm(request.POST or None)
    graph_img = None
    props = {}

    if request.method == "POST" and form.is_valid():
        edges_input = form.cleaned_data['edges']
        graph_type = form.cleaned_data['graph_type']

        # Extraction et nettoyage des arêtes
        edges = [tuple(e.strip().split('-')) for e in re.split('[,;]', edges_input) if '-' in e]

        # Création du graphe
        if graph_type == 'oriente':
            G = nx.DiGraph()
        else:
            G = nx.Graph()
        G.add_edges_from(edges)

        # === Propriétés du graphe ===
        if G.number_of_nodes() > 0:
            props = {
                "Type": graph_type,
                "Sommets": G.number_of_nodes(),
                "Arêtes": G.number_of_edges(),
                "Densité": round(nx.density(G), 3),
                "Degré moyen": round(sum(dict(G.degree()).values()) / G.number_of_nodes(), 2)
            }

        # === Dessin du graphe ===
        pos = nx.spring_layout(G, seed=42)
        plt.figure(figsize=(6, 4))
        nx.draw(G, pos, with_labels=True, node_color="lightblue",
                node_size=1500, font_size=12)
        plt.title(f"Graphe : {graph_type}")

        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        graph_img = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()

    return render(request, "matrix_structures/graph_view.html", {
        "form": form,
        "graph_img": graph_img,
        "props": props
    })


# =====================================
# === POSITION HIÉRARCHIQUE ===========
# =====================================
def hierarchy_pos(G, root, width=1., vert_gap=0.3, vert_loc=0,
                  xcenter=0.5, pos=None, parent=None):
    """Position hiérarchique pour un arbre non orienté."""
    if pos is None:
        pos = {root: (xcenter, vert_loc)}
    else:
        pos[root] = (xcenter, vert_loc)

    children = list(G.neighbors(root))
    if parent is not None and parent in children:
        children.remove(parent)

    if len(children) != 0:
        dx = width / len(children)
        nextx = xcenter - width / 2 - dx / 2
        for child in children:
            nextx += dx
            pos = hierarchy_pos(G, child, width=dx, vert_gap=vert_gap,
                                vert_loc=vert_loc - vert_gap, xcenter=nextx,
                                pos=pos, parent=root)
    return pos
from django.shortcuts import render


def principal(request):
    """Page principale contenant les liens vers TP1 → TP6"""
    return render(request, "principal/principal.html")


def tp1(request):
    return render(request, "matrix_structures/tp1.html")


def tp2(request):
    return render(request, "matrix_structures/tp2.html")


def tp3(request):
    return render(request, "matrix_structures/tp3.html")


def tp4(request):
    return render(request, "matrix_structures/tp4.html")


def tp5(request):
    return render(request, "matrix_structures/tp5.html")


def tp6(request):
    return render(request, "matrix_structures/tp6.html")
